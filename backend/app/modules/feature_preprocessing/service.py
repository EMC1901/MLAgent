import logging
import uuid
from datetime import datetime
from sqlmodel import Session

from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.feature_preprocessing.model import FeaturePreprocessing
from app.modules.feature_preprocessing.repository import FeaturePreprocessingRepository
from app.modules.feature_preprocessing.schemas import (
    FeaturePreprocessingCreateRequest,
    FeaturePreprocessingResponse,
    PreviewResponse,
    PlanRequest,
    ExecuteRequest,
    PlanResponse,
    RationaleResponse,
    ExecutionReportResponse,
    RemovedFeaturesResponse,
    FeatureLineageResponse,
    ArtifactManifestResponse,
    ProvenanceResponse,
    PPRationale,
    PreprocessingPlan,
    PreprocessingExecutionReport,
    OperationResult,
    RemovedFeature,
    ModelReadyArtifact,
    PreprocessorArtifact,
    PreprocessingProvenance,
    FeatureLineageEntry,
    FeatureGroupLineageEntry,
    ExplainabilityPreservationReport,
    ModelSearchContextInput,
)
from app.modules.feature_preprocessing.context_builder import build_preprocessing_context
from app.modules.feature_preprocessing.artifact_loader import load_raw_feature_matrix
from app.modules.feature_preprocessing.feature_filter import filter_features
from app.modules.feature_preprocessing.feature_group_validator import validate_feature_groups
from app.modules.feature_preprocessing.preprocessing_executor import execute_preprocessing
from app.modules.feature_preprocessing.preprocessing_pipeline_builder import build_pipeline
from app.modules.feature_preprocessing.artifact_manager import (
    save_model_ready_artifact,
    read_preview_from_model_ready,
)
from app.modules.feature_preprocessing.builder import build_preprocessing_object
from app.modules.feature_preprocessing.enums import FeaturePreprocessingStatus
from app.modules.feature_preprocessing.exceptions import (
    FeaturePreprocessingNotFoundException,
    FeaturePreprocessingUpstreamNotReadyException,
    FeatureArtifactLoadException,
    FeatureArtifactMissingException,
    TargetColumnMissingException,
    NoValidFeaturesException,
    ImputationFailedException,
    ScalingFailedException,
    FeatureSelectionFailedException,
    ModelReadyArtifactSaveException,
    PreprocessorArtifactSaveException,
)

# New LLM-guided imports
from app.modules.feature_preprocessing.llm_planner import (
    build_preprocessing_plan_prompt,
    PREPROCESSING_PLAN_SCHEMA,
)
from app.modules.feature_preprocessing.plan_validator import validate_preprocessing_plan
from app.modules.feature_preprocessing.plan_executor import PreprocessingPlanExecutor
from app.shared.registry.fp_capability_registry import (
    get_available_fp_capabilities,
    get_registry_snapshot_fp,
    CAPABILITY_GROUPS,
)
from app.modules.task_interpretation.llm_client import LLMClient

import hashlib
import json
import re

logger = logging.getLogger(__name__)


class FeaturePreprocessingService:

    def __init__(self):
        self.task_repo = TaskSpecificationRepository()
        self.fmp_repo = FeaturePreprocessingRepository()
        self.llm_client = LLMClient()

    # ============================================================
    #  Create (LLM-guided flow)
    # ============================================================

    def create_feature_preprocessing(
        self, session: Session, task_id: str, request: FeaturePreprocessingCreateRequest,
    ) -> FeaturePreprocessingResponse:
        fmp_id = f"fmp_{uuid.uuid4().hex[:8]}"

        if request.planning_mode == "llm_guided":
            return self._create_with_llm(session, task_id, fmp_id, request)
        else:
            return self._create_legacy(session, task_id, fmp_id, request)

    # ============================================================
    #  Plan-only (no execution)
    # ============================================================

    def plan_only(
        self, session: Session, task_id: str, request: PlanRequest,
    ) -> PlanResponse:
        fmp_id = f"fmp_{uuid.uuid4().hex[:8]}"
        logger.info("=== FP Plan: starting (fmp_id=%s, task_id=%s, force_regenerate=%s) ===", fmp_id, task_id, request.force_regenerate)

        # Build context
        logger.info("FP Plan: building preprocessing context...")
        context = build_preprocessing_context(session, task_id)
        task_ctx = context.get("task_context") or {}
        fe_ctx = context.get("feature_engineering_context") or {}
        logger.info(
            "FP Plan: context built — task_type=%s target_col=%s n_samples=%s n_features=%s modality=%s",
            task_ctx.get("task_type"), task_ctx.get("target_column"),
            fe_ctx.get("n_samples"), fe_ctx.get("n_features"),
            context.get("data_context", {}).get("input_modality"),
        )

        # Get FE decision input
        fe_json = fe_ctx.get("feature_json", {})
        decision_input = fe_json.get(
            "feature_preprocessing_decision_input",
            fe_json.get("preprocessing_decision_input_json", {})
        )
        if not decision_input:
            logger.warning("FP Plan: no decision_input in FE result, building from context")
            decision_input = self._build_decision_input_from_context(context)
        else:
            fc = decision_input.get("feature_matrix_context") or {}
            dc = decision_input.get("dataset_context") or {}
            logger.info(
                "FP Plan: decision_input loaded — feature_count=%s row_count=%s risks=%s",
                fc.get("feature_count"), dc.get("row_count"),
                len(decision_input.get("known_preprocessing_risks", [])),
            )

        # Get preprocessing intent from workflow plan
        plan_context = context.get("plan_context") or {}
        preprocessing_intent = plan_context.get("feature_strategy", {}).get(
            "preprocessing_intent",
            plan_context.get("preprocessing_intent", {})
        )
        goals = preprocessing_intent.get("high_level_goals", []) if isinstance(preprocessing_intent, dict) else []
        logger.info("FP Plan: preprocessing_intent — goals=%d: %s", len(goals), goals[:5] if len(goals) > 5 else goals)

        # Build LLM prompt
        logger.info("FP Plan: building LLM prompt...")
        system_prompt, user_message = build_preprocessing_plan_prompt(
            decision_input, preprocessing_intent
        )
        logger.info(
            "FP Plan: prompt ready — system_prompt_chars=%d user_message_chars=%d",
            len(system_prompt), len(user_message),
        )

        # Call LLM
        logger.info(
            "FP Plan: calling LLM — provider=%s model=%s timeout=%ds retries=%d",
            self.llm_client.provider, self.llm_client.model,
            self.llm_client.timeout, self.llm_client.max_retries,
        )
        try:
            raw_response = self.llm_client.generate(system_prompt, user_message)
            logger.info("FP Plan: LLM response received — chars=%d", len(raw_response) if raw_response else 0)
        except Exception as e:
            logger.error(
                "FP Plan: LLM call FAILED — provider=%s model=%s error_type=%s: %s",
                self.llm_client.provider, self.llm_client.model, type(e).__name__, str(e),
            )
            raise ImputationFailedException(f"LLM plan generation failed: {str(e)}")

        # Parse
        logger.info("FP Plan: parsing LLM response...")
        plan_dict = self._parse_llm_response(raw_response)
        ops = plan_dict.get("operation_sequence", [])
        caps = plan_dict.get("capability_groups_used", [])
        logger.info(
            "FP Plan: parsed — operations=%d groups_used=%d cols=%d",
            len(ops), len(caps), len(plan_dict.get("column_policies", [])),
        )

        # Validate
        logger.info("FP Plan: validating plan...")
        validation = validate_preprocessing_plan(plan_dict, decision_input)
        if not validation.get("is_valid"):
            errors = validation.get("errors", [])
            logger.error("FP Plan: validation FAILED — errors=%d: %s", len(errors), errors[:3] if len(errors) > 3 else errors)
            raise ImputationFailedException(
                f"Plan validation failed: {'; '.join(errors)}"
            )
        logger.info("FP Plan: validation PASSED — warnings=%d", len(validation.get("warnings", [])))

        # Persist plan record
        plan_obj = PreprocessingPlan(**plan_dict)
        plan_obj.plan_id = fmp_id

        fmp_model = FeaturePreprocessing(
            id=fmp_id,
            task_id=context["task_id"],
            interpretation_id=context.get("interpretation_id"),
            dataset_profile_id=context.get("dataset_profile_id"),
            workflow_plan_id=context.get("workflow_plan_id"),
            feature_engineering_id=context.get("feature_engineering_id"),
            status=FeaturePreprocessingStatus.PENDING,
            preprocessing_plan_json=plan_obj.model_dump(mode="json"),
            registry_snapshot_version=get_registry_snapshot_fp()["snapshot_version"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.fmp_repo.create(session, fmp_model)

        return PlanResponse(
            preprocessing_id=fmp_id,
            task_id=task_id,
            preprocessing_plan=plan_obj,
        )

    # ============================================================
    #  Execute plan
    # ============================================================

    def execute_plan(
        self, session: Session, task_id: str, request: ExecuteRequest,
    ) -> FeaturePreprocessingResponse:
        all_warnings = []
        all_errors = []

        logger.info("=== FP Execute: starting (task_id=%s, plan_id=%s, has_plan=%s) ===", task_id, request.plan_id, request.plan is not None)

        # Build context
        logger.info("FP Execute: building preprocessing context...")
        context = build_preprocessing_context(session, task_id)

        fe_context = context.get("feature_engineering_context") or {}
        artifact_path = fe_context.get("artifact_path")
        logger.info("FP Execute: context built — artifact_path=%s", artifact_path)

        # Load plan
        if request.plan_id:
            logger.info("FP Execute: loading plan from DB — plan_id=%s", request.plan_id)
            fmp = self.fmp_repo.get_by_id(session, request.plan_id)
            if not fmp or not fmp.preprocessing_plan_json:
                raise FeaturePreprocessingNotFoundException(
                    f"Plan with id {request.plan_id} not found or has no plan."
                )
            plan_dict = fmp.preprocessing_plan_json
            fmp_id = request.plan_id
        elif request.plan:
            plan_dict = request.plan
            fmp_id = f"fmp_{uuid.uuid4().hex[:8]}"
            logger.info("FP Execute: using inline plan — new fmp_id=%s", fmp_id)
        else:
            raise ImputationFailedException("Either plan_id or plan must be provided.")

        ops = plan_dict.get("operation_sequence", [])
        logger.info("FP Execute: plan loaded — operations=%d", len(ops))

        # Load raw feature matrix
        logger.info("FP Execute: loading feature matrix from %s", artifact_path)
        try:
            load_result = load_raw_feature_matrix(artifact_path)
        except (FeatureArtifactLoadException, FeatureArtifactMissingException) as e:
            logger.error("FP Execute: failed to load feature matrix — %s: %s", type(e).__name__, str(e))
            failed = self._persist_failed(session, fmp_id, context, "Failed to load feature artifact.")
            raise

        raw_df = load_result["dataframe"]
        candidate_features = load_result["candidate_feature_columns"]
        target_column = context.get("task_context", {}).get("target_column") or load_result["target_column"]
        n_raw_features = len(candidate_features)
        logger.info(
            "FP Execute: matrix loaded — shape=%s target=%s raw_features=%d",
            raw_df.shape, target_column, n_raw_features,
        )

        if not target_column or target_column not in raw_df.columns:
            logger.error("FP Execute: target column '%s' not found — available: %s", target_column, list(raw_df.columns)[:10])
            failed = self._persist_failed(
                session, fmp_id, context,
                "Target column missing.",
                n_samples=len(raw_df), n_raw_features=n_raw_features,
                target_column=target_column,
            )
            raise TargetColumnMissingException(f"Target column '{target_column}' not found in feature matrix.")

        # Get feature groups from FE
        fe_json = fe_context.get("feature_json", {})
        feature_groups = (
            fe_json.get("feature_schema", {}).get("feature_groups", [])
            or fe_json.get("feature_groups", [])
        )

        # Validate plan
        logger.info("FP Execute: validating plan...")
        validation = validate_preprocessing_plan(plan_dict)
        if not validation.get("is_valid"):
            errors = validation.get("errors", [])
            logger.error("FP Execute: plan validation FAILED — errors=%d: %s", len(errors), errors[:3] if len(errors) > 3 else errors)
            failed = self._persist_failed(
                session, fmp_id, context,
                f"Plan validation failed: {'; '.join(errors)}",
                n_samples=len(raw_df), n_raw_features=n_raw_features,
                target_column=target_column,
            )
            raise ImputationFailedException(f"Plan validation failed: {'; '.join(errors)}")
        logger.info("FP Execute: plan validation PASSED — warnings=%d", len(validation.get("warnings", [])))

        # Execute plan
        logger.info("FP Execute: running PreprocessingPlanExecutor...")
        executor = PreprocessingPlanExecutor(random_seed=42)
        execution_result = executor.execute(
            df=raw_df,
            target_column=target_column,
            feature_columns=candidate_features,
            plan=plan_dict,
            feature_groups=feature_groups,
        )

        exec_errors = execution_result.get("errors", [])
        exec_warnings = execution_result.get("warnings", [])
        all_warnings.extend(exec_warnings)
        all_errors.extend(exec_errors)

        model_ready_df = execution_result.get("dataframe")
        final_features = execution_result.get("feature_columns", [])
        n_removed = len(execution_result.get("removed_features", []))
        logger.info(
            "FP Execute: executor done — shape=%s final_features=%d removed=%d errors=%d warnings=%d",
            model_ready_df.shape if model_ready_df is not None else None,
            len(final_features), n_removed, len(exec_errors), len(exec_warnings),
        )

        if model_ready_df is None or len(final_features) == 0:
            failed = self._persist_failed(
                session, fmp_id, context,
                "No features after plan execution.",
                n_samples=len(raw_df), n_raw_features=n_raw_features,
                n_valid_features=len(candidate_features),
                n_final_features=0, n_dropped_features=len(execution_result.get("removed_features", [])),
                target_column=target_column,
            )
            raise NoValidFeaturesException("No features remain after preprocessing plan execution.")

        # Build pipeline
        logger.info("FP Execute: building preprocessing pipeline...")
        pipeline = build_pipeline(execution_result, final_features)

        # Save artifacts
        logger.info("FP Execute: saving model-ready artifact (id=%s)...", fmp_id)
        try:
            artifact_result = save_model_ready_artifact(fmp_id, model_ready_df, pipeline)
            logger.info(
                "FP Execute: artifacts saved — model_ready=%s preprocessor=%s",
                artifact_result.get("model_ready_artifact_id"),
                artifact_result.get("preprocessor_artifact_id"),
            )
        except (ModelReadyArtifactSaveException, PreprocessorArtifactSaveException) as e:
            logger.error("FP Execute: artifact save FAILED — %s: %s", type(e).__name__, str(e))
            failed = self._persist_failed(
                session, fmp_id, context,
                "Failed to save artifacts.",
                n_samples=len(raw_df), n_raw_features=n_raw_features,
                n_valid_features=len(candidate_features),
                n_final_features=len(final_features),
                n_dropped_features=len(execution_result.get("removed_features", [])),
                target_column=target_column,
            )
            raise

        # Build execution report
        op_results = []
        for op in execution_result.get("operation_results", []):
            op_results.append(OperationResult(
                operation_id=op.get("operation_id", ""),
                capability_id=op.get("capability_id", ""),
                capability_group=op.get("capability_group", ""),
                status=op.get("status", "unknown"),
                affected_features=op.get("affected_features", []),
                removed_features=op.get("removed_features", []),
                warnings=op.get("warnings", []),
                error_message=op.get("error_message"),
            ))
        execution_report = PreprocessingExecutionReport(operation_results=op_results)

        # Build removed features
        removed_features = []
        for rf in execution_result.get("removed_features", []):
            removed_features.append(RemovedFeature(
                feature_name=rf.get("feature_name", ""),
                reason=rf.get("reason", ""),
                evidence=rf.get("evidence", ""),
                source_feature_group=rf.get("source_feature_group", ""),
            ))

        # Build lineage
        lineage_map = execution_result.get("lineage_map", {})
        feature_lineage_map = {}
        for orig_name, linfo in lineage_map.items():
            feature_lineage_map[orig_name] = FeatureLineageEntry(
                original_name=linfo.get("original_name", orig_name),
                transformed_name=linfo.get("transformed_name", orig_name),
                source_feature_group=linfo.get("source_feature_group", ""),
                source_feature_action=linfo.get("source_feature_action", ""),
                transformations_applied=linfo.get("transformations_applied", []),
                imputed=linfo.get("imputed", False),
                scaled=linfo.get("scaled", False),
                transformed=linfo.get("transformed", False),
                selected=linfo.get("selected", True),
                reduced=linfo.get("reduced", False),
                is_interpretable=linfo.get("is_interpretable", True),
                removed=linfo.get("removed", False),
                removal_reason=linfo.get("removal_reason"),
            )

        # Feature group lineage
        feature_group_lineage_map = {}
        for fg in (feature_groups or []):
            gname = fg.get("group_name", fg.get("display_name", ""))
            fg_orig_count = len(fg.get("feature_columns", []))
            fg_retained = [c for c in fg.get("feature_columns", []) if c in final_features]
            fg_removed = fg_orig_count - len(fg_retained)
            fg_ops = [op.get("capability_id", "") for op in execution_result.get("operation_results", [])
                      if any(c in op.get("affected_features", []) for c in fg.get("feature_columns", []))]
            feature_group_lineage_map[gname] = FeatureGroupLineageEntry(
                group_name=gname,
                group_status="removed" if len(fg_retained) == 0 else (
                    "partially_retained" if fg_removed > 0 else "retained"
                ),
                original_feature_count=fg_orig_count,
                retained_feature_count=len(fg_retained),
                removed_feature_count=fg_removed,
                operations_applied=list(set(fg_ops)),
            )

        # Explainability report
        n_interpretable = sum(
            1 for linfo in lineage_map.values()
            if linfo.get("is_interpretable") and not linfo.get("removed")
        )
        explainability_report = ExplainabilityPreservationReport(
            total_original_features=len(candidate_features),
            total_retained_features=len(final_features),
            total_interpretable_features=n_interpretable,
            total_reduced_features=sum(1 for linfo in lineage_map.values() if linfo.get("reduced")),
            interpretability_score=round(n_interpretable / max(len(final_features), 1), 4),
        )

        # Build artifacts
        model_ready_artifacts = [
            ModelReadyArtifact(
                artifact_id=artifact_result.get("model_ready_artifact_id", ""),
                variant_name="default",
                path=artifact_result.get("model_ready_file_path", ""),
                usage="fold_safe_template",
                row_count=artifact_result.get("model_ready_n_samples", len(raw_df)),
                feature_count=artifact_result.get("model_ready_n_features", len(final_features)),
                artifact_hash=self._compute_hash(artifact_result.get("model_ready_file_path", "")),
            )
        ]
        preprocessor_artifacts = [
            PreprocessorArtifact(
                artifact_id=artifact_result.get("preprocessor_artifact_id", ""),
                variant_name="default",
                path=artifact_result.get("preprocessor_file_path", ""),
                usage="pipeline_template",
                artifact_hash=self._compute_hash(artifact_result.get("preprocessor_file_path", "")),
            )
        ]

        # Provenance
        provenance = PreprocessingProvenance(
            registry_snapshot_version=get_registry_snapshot_fp()["snapshot_version"],
            input_feature_artifact_hash=self._compute_hash(artifact_path or ""),
            output_artifact_hash=model_ready_artifacts[0].artifact_hash,
            operation_parameter_snapshot={
                op.get("operation_id", ""): op.get("parameters", {})
                for op in plan_dict.get("operation_sequence", [])
            },
            fitted_statistics_summary=execution_result.get("fitted_statistics", {}),
            dependency_versions={},
            random_seed=42,
            created_at=datetime.now(),
        )

        # Model search context input
        model_search_context_input = ModelSearchContextInput(
            model_ready_matrix_path=artifact_result.get("model_ready_file_path"),
            preprocessor_path=artifact_result.get("preprocessor_file_path"),
            feature_summary={
                "n_final_features": len(final_features),
                "n_removed_features": len(removed_features),
                "feature_lineage_summary": {
                    "imputed_count": sum(1 for l in lineage_map.values() if l.get("imputed")),
                    "scaled_count": sum(1 for l in lineage_map.values() if l.get("scaled")),
                    "reduced_count": sum(1 for l in lineage_map.values() if l.get("reduced")),
                },
            },
            default_variant_id=artifact_result.get("model_ready_artifact_id"),
            available_variants=[
                {"variant_name": "default", "artifact_id": artifact_result.get("model_ready_artifact_id")}
            ],
            recommended_variant_by_model_family={},
        )

        # Determine status
        if all_errors:
            status = FeaturePreprocessingStatus.FAILED
        elif all_warnings or execution_result.get("removed_features"):
            status = FeaturePreprocessingStatus.PREPROCESSED_WITH_WARNING
        else:
            status = FeaturePreprocessingStatus.PREPROCESSED

        n_removed = len(removed_features)

        # Calculate dropped features
        n_dropped = n_removed  # from plan execution

        # Derive preprocessing_execution from operation_results
        imputation_executed = False
        scaling_executed = False
        feature_selection_executed = False
        categorical_encoding_executed = False
        imputation_strategy = "none"
        scaling_strategy = "none"
        feature_selection_strategy = "none"
        selection_dropped = []

        for op_result in execution_result.get("operation_results", []):
            if op_result.get("status") != "success":
                continue
            cap_id = op_result.get("capability_id", "")
            cap_group = op_result.get("capability_group", "")

            if cap_group == "missing_value_handling" and cap_id in (
                "median_imputer", "mean_imputer", "most_frequent_imputer",
                "constant_imputer", "missing_indicator", "groupwise_imputer",
            ):
                imputation_executed = True
                imputation_strategy = cap_id.replace("_imputer", "").replace("_indicator", "")

            if cap_group == "scaling_normalization" and cap_id in (
                "standard_scaler", "minmax_scaler", "robust_scaler", "maxabs_scaler",
                "groupwise_scaler", "model_family_aware_scaling_policy",
            ):
                scaling_executed = True
                scaling_strategy = cap_id

            if cap_group in ("feature_selection", "low_information_filtering", "correlation_collinearity"):
                if op_result.get("removed_features"):
                    feature_selection_executed = True
                    feature_selection_strategy = cap_id
                    selection_dropped.extend(op_result.get("removed_features", []))

            if cap_group == "categorical_encoding":
                categorical_encoding_executed = True

        preprocessing_execution = {
            "imputation": {
                "executed": imputation_executed,
                "strategy": imputation_strategy,
                "columns": [],
                "artifact_component": "numeric_imputer" if imputation_executed else "",
            },
            "scaling": {
                "executed": scaling_executed,
                "strategy": scaling_strategy,
                "columns": [],
                "artifact_component": "numeric_scaler" if scaling_executed else "",
            },
            "categorical_encoding": {
                "executed": categorical_encoding_executed,
                "strategy": "onehot" if categorical_encoding_executed else "none",
                "columns": [],
            },
            "feature_selection": {
                "executed": feature_selection_executed,
                "strategy": feature_selection_strategy if feature_selection_executed else "none",
                "columns_dropped": list(set(selection_dropped)),
            },
        }

        # Build preprocessing_json for backward compat
        preprocessing_json = {
            "preprocessing_id": fmp_id,
            "task_id": context["task_id"],
            "interpretation_id": context.get("interpretation_id"),
            "dataset_profile_id": context.get("dataset_profile_id"),
            "workflow_plan_id": context.get("workflow_plan_id"),
            "feature_engineering_id": context.get("feature_engineering_id"),
            "status": status,
            "preprocessing_execution": preprocessing_execution,
            "validation_summary": {
                "is_model_ready": status in (FeaturePreprocessingStatus.PREPROCESSED, FeaturePreprocessingStatus.PREPROCESSED_WITH_WARNING),
                "n_samples": len(raw_df),
                "n_raw_features": n_raw_features,
                "n_valid_features_before_preprocessing": len(candidate_features),
                "n_features_after_preprocessing": len(final_features),
                "n_dropped_features": n_removed,
                "target_column": target_column,
                "task_type": context.get("task_context", {}).get("task_type"),
            },
            "model_search_input": {
                "model_ready_artifact_id": artifact_result.get("model_ready_artifact_id"),
                "model_ready_matrix_path": artifact_result.get("model_ready_file_path"),
                "preprocessing_pipeline_artifact_id": artifact_result.get("preprocessor_artifact_id"),
                "target_column": target_column,
                "feature_columns": final_features,
                "task_type": context.get("task_context", {}).get("task_type"),
                "primary_metric": context.get("task_context", {}).get("primary_metric"),
                "ready_for_model_search": status in (FeaturePreprocessingStatus.PREPROCESSED, FeaturePreprocessingStatus.PREPROCESSED_WITH_WARNING),
            },
            "warnings": all_warnings,
            "errors": all_errors,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # Persist
        logger.info(
            "FP Execute: persisting — id=%s status=%s samples=%d features=%d→%d removed=%d warnings=%d errors=%d",
            fmp_id, status, len(raw_df), n_raw_features, len(final_features), n_removed,
            len(all_warnings), len(all_errors),
        )
        fmp_model = FeaturePreprocessing(
            id=fmp_id,
            task_id=context["task_id"],
            interpretation_id=context.get("interpretation_id"),
            dataset_profile_id=context.get("dataset_profile_id"),
            workflow_plan_id=context.get("workflow_plan_id"),
            feature_engineering_id=context.get("feature_engineering_id"),
            status=status,
            n_samples=len(raw_df),
            n_raw_features=n_raw_features,
            n_valid_features=len(candidate_features),
            n_final_features=len(final_features),
            n_dropped_features=n_removed,
            target_column=target_column,
            model_ready_artifact_id=artifact_result.get("model_ready_artifact_id"),
            model_ready_artifact_path=artifact_result.get("model_ready_file_path"),
            preprocessor_artifact_id=artifact_result.get("preprocessor_artifact_id"),
            preprocessor_artifact_path=artifact_result.get("preprocessor_file_path"),
            is_ready_for_model_search=status in (
                FeaturePreprocessingStatus.PREPROCESSED,
                FeaturePreprocessingStatus.PREPROCESSED_WITH_WARNING,
            ),
            preprocessing_json=preprocessing_json,
            preview_json=artifact_result.get("preview_json"),
            preprocessing_plan_json=plan_dict,
            execution_report_json=execution_report.model_dump(mode="json"),
            removed_features_json={"removed_features": [rf.model_dump(mode="json") for rf in removed_features]},
            feature_lineage_json={
                "feature_lineage_map": {k: v.model_dump(mode="json") for k, v in feature_lineage_map.items()},
                "feature_group_lineage_map": {k: v.model_dump(mode="json") for k, v in feature_group_lineage_map.items()},
            },
            explainability_report_json=explainability_report.model_dump(mode="json"),
            provenance_json=provenance.model_dump(mode="json"),
            registry_snapshot_version=get_registry_snapshot_fp()["snapshot_version"],
            error_message=None if all_errors == [] else "; ".join(all_errors),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.fmp_repo.save(session, fmp_model)
        logger.info("=== FP Execute: DONE (fmp_id=%s) ===", fmp_id)

        return FeaturePreprocessingResponse(
            preprocessing_id=fmp_id,
            task_id=context["task_id"],
            interpretation_id=context.get("interpretation_id"),
            dataset_profile_id=context.get("dataset_profile_id"),
            workflow_plan_id=context.get("workflow_plan_id"),
            feature_engineering_id=context.get("feature_engineering_id"),
            status=status,
            preprocessing_plan=PreprocessingPlan(**plan_dict),
            preprocessing_registry_snapshot_version=get_registry_snapshot_fp()["snapshot_version"],
            execution_report=execution_report,
            removed_features=removed_features,
            retained_feature_groups=[fg for fg in (feature_groups or []) if fg.get("group_name", "") in feature_group_lineage_map and feature_group_lineage_map[fg.get("group_name", "")].retained_feature_count > 0],
            feature_lineage_map={k: v.model_dump() for k, v in feature_lineage_map.items()},
            feature_group_lineage_map={k: v.model_dump() for k, v in feature_group_lineage_map.items()},
            explainability_preservation_report=explainability_report,
            model_ready_artifacts=model_ready_artifacts,
            preprocessor_artifacts=preprocessor_artifacts,
            preprocessing_provenance=provenance,
            model_search_context_input=model_search_context_input,
            validation_summary=preprocessing_json.get("validation_summary"),
            model_search_input=preprocessing_json.get("model_search_input"),
            warnings=all_warnings,
            errors=all_errors,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    # ============================================================
    #  Sub-resource getters
    # ============================================================

    def get_plan(self, session: Session, fmp_id: str) -> PlanResponse:
        fmp = self.fmp_repo.get_by_id(session, fmp_id)
        if not fmp:
            raise FeaturePreprocessingNotFoundException(
                f"Feature preprocessing with id {fmp_id} not found."
            )
        plan = None
        if fmp.preprocessing_plan_json:
            plan = PreprocessingPlan(**fmp.preprocessing_plan_json)
        return PlanResponse(
            preprocessing_id=fmp_id,
            task_id=fmp.task_id or "",
            preprocessing_plan=plan or PreprocessingPlan(),
        )

    def get_rationale(self, session: Session, fmp_id: str) -> RationaleResponse:
        fmp = self.fmp_repo.get_by_id(session, fmp_id)
        if not fmp:
            raise FeaturePreprocessingNotFoundException(
                f"Feature preprocessing with id {fmp_id} not found."
            )
        plan_dict = fmp.preprocessing_plan_json or {}
        rationales = []
        for op in plan_dict.get("operation_sequence", []):
            dr = op.get("decision_rationale", {})
            rationales.append(PPRationale(
                reason=dr.get("reason", ""),
                evidence=dr.get("evidence", []),
                expected_benefit=dr.get("expected_benefit", ""),
                risk=dr.get("risk", ""),
                fallback=dr.get("fallback", ""),
            ))
        rejected_ops = []
        for ro in plan_dict.get("rejected_operations", []):
            from app.modules.feature_preprocessing.schemas import RejectedOperation
            rejected_ops.append(RejectedOperation(
                capability_id=ro.get("capability_id", ""),
                reason=ro.get("reason", ""),
                evidence=ro.get("evidence", []),
            ))
        return RationaleResponse(
            preprocessing_id=fmp_id,
            rationales=rationales,
            rejected_operations=rejected_ops,
        )

    def get_execution_report(self, session: Session, fmp_id: str) -> ExecutionReportResponse:
        fmp = self.fmp_repo.get_by_id(session, fmp_id)
        if not fmp:
            raise FeaturePreprocessingNotFoundException(
                f"Feature preprocessing with id {fmp_id} not found."
            )
        report = PreprocessingExecutionReport()
        if fmp.execution_report_json:
            report = PreprocessingExecutionReport(**fmp.execution_report_json)
        return ExecutionReportResponse(
            preprocessing_id=fmp_id,
            execution_report=report,
        )

    def get_removed_features(self, session: Session, fmp_id: str) -> RemovedFeaturesResponse:
        fmp = self.fmp_repo.get_by_id(session, fmp_id)
        if not fmp:
            raise FeaturePreprocessingNotFoundException(
                f"Feature preprocessing with id {fmp_id} not found."
            )
        rf_list = []
        if fmp.removed_features_json:
            rf_list = fmp.removed_features_json.get("removed_features", [])
        removed = [RemovedFeature(**rf) for rf in rf_list]
        return RemovedFeaturesResponse(
            preprocessing_id=fmp_id,
            removed_features=removed,
            total_removed=len(removed),
        )

    def get_feature_lineage(self, session: Session, fmp_id: str) -> FeatureLineageResponse:
        fmp = self.fmp_repo.get_by_id(session, fmp_id)
        if not fmp:
            raise FeaturePreprocessingNotFoundException(
                f"Feature preprocessing with id {fmp_id} not found."
            )
        fl_map = {}
        fg_map = {}
        if fmp.feature_lineage_json:
            fl_map = fmp.feature_lineage_json.get("feature_lineage_map", {})
            fg_map = fmp.feature_lineage_json.get("feature_group_lineage_map", {})
        return FeatureLineageResponse(
            preprocessing_id=fmp_id,
            feature_lineage_map=fl_map,
            feature_group_lineage_map=fg_map,
        )

    def get_artifact_manifest(self, session: Session, fmp_id: str) -> ArtifactManifestResponse:
        fmp = self.fmp_repo.get_by_id(session, fmp_id)
        if not fmp:
            raise FeaturePreprocessingNotFoundException(
                f"Feature preprocessing with id {fmp_id} not found."
            )
        mr_artifacts = [
            ModelReadyArtifact(
                artifact_id=fmp.model_ready_artifact_id or "",
                variant_name="default",
                path=fmp.model_ready_artifact_path or "",
                usage="fold_safe_template",
                row_count=fmp.n_samples or 0,
                feature_count=fmp.n_final_features or 0,
                artifact_hash=self._compute_hash(fmp.model_ready_artifact_path or ""),
            )
        ]
        pp_artifacts = [
            PreprocessorArtifact(
                artifact_id=fmp.preprocessor_artifact_id or "",
                variant_name="default",
                path=fmp.preprocessor_artifact_path or "",
                usage="pipeline_template",
                artifact_hash=self._compute_hash(fmp.preprocessor_artifact_path or ""),
            )
        ]
        return ArtifactManifestResponse(
            preprocessing_id=fmp_id,
            model_ready_artifacts=mr_artifacts,
            preprocessor_artifacts=pp_artifacts,
        )

    def get_provenance(self, session: Session, fmp_id: str) -> ProvenanceResponse:
        fmp = self.fmp_repo.get_by_id(session, fmp_id)
        if not fmp:
            raise FeaturePreprocessingNotFoundException(
                f"Feature preprocessing with id {fmp_id} not found."
            )
        provenance = PreprocessingProvenance()
        if fmp.provenance_json:
            provenance = PreprocessingProvenance(**fmp.provenance_json)
        return ProvenanceResponse(
            preprocessing_id=fmp_id,
            preprocessing_provenance=provenance,
        )

    # ============================================================
    #  Query / Get
    # ============================================================

    def get_feature_preprocessing(self, session: Session, fmp_id: str) -> FeaturePreprocessingResponse:
        fmp = self.fmp_repo.get_by_id(session, fmp_id)
        if not fmp:
            raise FeaturePreprocessingNotFoundException(
                f"Feature preprocessing with id {fmp_id} not found."
            )
        return self._to_response(fmp)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> FeaturePreprocessingResponse:
        self._check_task_exists(session, task_id)
        fmp = self.fmp_repo.get_latest_by_task_id(session, task_id)
        if not fmp:
            raise FeaturePreprocessingNotFoundException(
                f"No feature preprocessing found for task {task_id}."
            )
        return self._to_response(fmp)

    def rerun_feature_preprocessing(
        self, session: Session, task_id: str, request: FeaturePreprocessingCreateRequest,
    ) -> FeaturePreprocessingResponse:
        return self.create_feature_preprocessing(session, task_id, request)

    def get_preview(self, session: Session, fmp_id: str) -> PreviewResponse:
        fmp = self.fmp_repo.get_by_id(session, fmp_id)
        if not fmp:
            raise FeaturePreprocessingNotFoundException(
                f"Feature preprocessing with id {fmp_id} not found."
            )

        if fmp.preview_json:
            return PreviewResponse(
                columns=fmp.preview_json.get("columns", []),
                preview_rows=fmp.preview_json.get("preview_rows", 0),
                total_rows=fmp.preview_json.get("total_rows", 0),
                rows=fmp.preview_json.get("rows", []),
            )

        preview = read_preview_from_model_ready(fmp_id)
        return PreviewResponse(
            columns=preview.get("columns", []),
            preview_rows=preview.get("preview_rows", 0),
            total_rows=preview.get("total_rows", 0),
            rows=preview.get("rows", []),
        )

    # ============================================================
    #  Private helpers
    # ============================================================

    def _create_with_llm(
        self, session: Session, task_id: str, fmp_id: str, request: FeaturePreprocessingCreateRequest,
    ) -> FeaturePreprocessingResponse:
        """Full LLM-guided flow: plan -> validate -> execute."""
        logger.info("=== FP LLM-Guided: starting full flow (task_id=%s, fmp_id=%s) ===", task_id, fmp_id)

        # Generate plan
        logger.info("FP LLM-Guided: phase 1 — generating plan...")
        plan_req = PlanRequest(force_regenerate=request.force_rerun)
        try:
            plan_response = self.plan_only(session, task_id, plan_req)
            logger.info("FP LLM-Guided: phase 1 DONE — plan_id=%s", plan_response.preprocessing_id)
        except Exception:
            logger.error("FP LLM-Guided: phase 1 FAILED")
            raise

        # Execute plan
        logger.info("FP LLM-Guided: phase 2 — executing plan %s...", plan_response.preprocessing_id)
        exec_req = ExecuteRequest(plan_id=plan_response.preprocessing_id)
        try:
            result = self.execute_plan(session, task_id, exec_req)
            logger.info("=== FP LLM-Guided: DONE (preprocessing_id=%s) ===", result.preprocessing_id if hasattr(result, 'preprocessing_id') else '?')
            return result
        except Exception:
            logger.error("FP LLM-Guided: phase 2 FAILED")
            raise

    def _create_legacy(
        self, session: Session, task_id: str, fmp_id: str, request: FeaturePreprocessingCreateRequest,
    ) -> FeaturePreprocessingResponse:
        """Legacy system-default flow (backward compatible)."""
        all_warnings = []
        all_errors = []

        try:
            context = build_preprocessing_context(session, task_id)
        except FeaturePreprocessingUpstreamNotReadyException:
            failed = FeaturePreprocessing(
                id=fmp_id,
                task_id=task_id,
                status=FeaturePreprocessingStatus.BLOCKED,
                error_message="Upstream not ready.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fmp_repo.create(session, failed)
            raise

        fe_context = context.get("feature_engineering_context") or {}
        artifact_path = fe_context.get("artifact_path")

        try:
            load_result = load_raw_feature_matrix(artifact_path)
        except (FeatureArtifactLoadException, FeatureArtifactMissingException):
            failed = FeaturePreprocessing(
                id=fmp_id,
                task_id=task_id,
                interpretation_id=context.get("interpretation_id"),
                dataset_profile_id=context.get("dataset_profile_id"),
                workflow_plan_id=context.get("workflow_plan_id"),
                feature_engineering_id=context.get("feature_engineering_id"),
                status=FeaturePreprocessingStatus.FAILED,
                error_message="Failed to load feature artifact.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fmp_repo.create(session, failed)
            raise

        raw_df = load_result["dataframe"]
        candidate_features = load_result["candidate_feature_columns"]
        target_column = context.get("task_context", {}).get("target_column") or load_result["target_column"]
        n_raw_features = len(candidate_features)

        if not target_column or target_column not in raw_df.columns:
            failed = FeaturePreprocessing(
                id=fmp_id,
                task_id=task_id,
                interpretation_id=context.get("interpretation_id"),
                dataset_profile_id=context.get("dataset_profile_id"),
                workflow_plan_id=context.get("workflow_plan_id"),
                feature_engineering_id=context.get("feature_engineering_id"),
                status=FeaturePreprocessingStatus.FAILED,
                n_samples=len(raw_df),
                n_raw_features=n_raw_features,
                target_column=target_column,
                error_message="Target column missing.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fmp_repo.create(session, failed)
            raise TargetColumnMissingException(f"Target column '{target_column}' not found in feature matrix.")

        max_missing_ratio = request.max_missing_ratio
        filter_result = filter_features(raw_df, candidate_features, max_missing_ratio)
        retained_features = filter_result["retained_feature_columns"]

        if not retained_features:
            failed = FeaturePreprocessing(
                id=fmp_id,
                task_id=task_id,
                interpretation_id=context.get("interpretation_id"),
                dataset_profile_id=context.get("dataset_profile_id"),
                workflow_plan_id=context.get("workflow_plan_id"),
                feature_engineering_id=context.get("feature_engineering_id"),
                status=FeaturePreprocessingStatus.FAILED,
                n_samples=len(raw_df),
                n_raw_features=n_raw_features,
                n_valid_features=0,
                n_final_features=0,
                n_dropped_features=len(filter_result.get("total_dropped", [])),
                target_column=target_column,
                error_message="No valid features after filtering.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fmp_repo.create(session, failed)
            raise NoValidFeaturesException()

        fe_json = fe_context.get("feature_json", {})
        feature_groups = (
            fe_json.get("feature_schema", {}).get("feature_groups", [])
            or fe_json.get("feature_groups", [])
        )
        group_validation = validate_feature_groups(feature_groups, retained_features)

        filtered_df = filter_result["dataframe"]
        execution_result = execute_preprocessing(
            df=filtered_df,
            target_column=target_column,
            feature_columns=retained_features,
            imputation_strategy=request.imputation_strategy,
            scaling_strategy=request.scaling_strategy,
            feature_selection_strategy=request.feature_selection_strategy,
        )

        exec_errors = execution_result.get("errors", [])
        exec_warnings = execution_result.get("warnings", [])
        all_warnings.extend(exec_warnings)
        all_errors.extend(exec_errors)

        if exec_errors:
            failed = FeaturePreprocessing(
                id=fmp_id,
                task_id=task_id,
                interpretation_id=context.get("interpretation_id"),
                dataset_profile_id=context.get("dataset_profile_id"),
                workflow_plan_id=context.get("workflow_plan_id"),
                feature_engineering_id=context.get("feature_engineering_id"),
                status=FeaturePreprocessingStatus.FAILED,
                n_samples=len(raw_df),
                n_raw_features=n_raw_features,
                n_valid_features=len(retained_features),
                n_final_features=len(execution_result.get("feature_columns", [])),
                n_dropped_features=len(filter_result.get("total_dropped", [])),
                target_column=target_column,
                error_message="; ".join(exec_errors),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fmp_repo.create(session, failed)
            raise ImputationFailedException("; ".join(exec_errors))

        model_ready_df = execution_result["dataframe"]
        final_features = execution_result["feature_columns"]

        if model_ready_df is None or final_features is None or len(final_features) == 0:
            failed = FeaturePreprocessing(
                id=fmp_id,
                task_id=task_id,
                interpretation_id=context.get("interpretation_id"),
                dataset_profile_id=context.get("dataset_profile_id"),
                workflow_plan_id=context.get("workflow_plan_id"),
                feature_engineering_id=context.get("feature_engineering_id"),
                status=FeaturePreprocessingStatus.FAILED,
                n_samples=len(raw_df),
                n_raw_features=n_raw_features,
                n_valid_features=len(retained_features),
                n_final_features=0,
                n_dropped_features=len(filter_result.get("total_dropped", [])),
                target_column=target_column,
                error_message="No features after preprocessing.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fmp_repo.create(session, failed)
            raise NoValidFeaturesException("No features remain after preprocessing.")

        pipeline = build_pipeline(execution_result, final_features)

        try:
            artifact_result = save_model_ready_artifact(fmp_id, model_ready_df, pipeline)
        except (ModelReadyArtifactSaveException, PreprocessorArtifactSaveException):
            failed = FeaturePreprocessing(
                id=fmp_id,
                task_id=task_id,
                interpretation_id=context.get("interpretation_id"),
                dataset_profile_id=context.get("dataset_profile_id"),
                workflow_plan_id=context.get("workflow_plan_id"),
                feature_engineering_id=context.get("feature_engineering_id"),
                status=FeaturePreprocessingStatus.FAILED,
                n_samples=len(raw_df),
                n_raw_features=n_raw_features,
                n_valid_features=len(retained_features),
                n_final_features=len(final_features),
                n_dropped_features=len(filter_result.get("total_dropped", [])),
                target_column=target_column,
                error_message="Failed to save artifacts.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fmp_repo.create(session, failed)
            raise

        if all_errors:
            status = FeaturePreprocessingStatus.FAILED
        elif all_warnings or filter_result.get("total_dropped"):
            status = FeaturePreprocessingStatus.PREPROCESSED_WITH_WARNING
        else:
            status = FeaturePreprocessingStatus.PREPROCESSED

        filter_result["n_samples"] = len(raw_df)

        fmp_object = build_preprocessing_object(
            preprocessing_id=fmp_id,
            context=context,
            status=status,
            filter_result=filter_result,
            group_validation=group_validation,
            execution_result=execution_result,
            artifact_result=artifact_result,
            warnings=all_warnings,
            errors=all_errors,
        )

        fmp_model = FeaturePreprocessing(
            id=fmp_id,
            task_id=context["task_id"],
            interpretation_id=context.get("interpretation_id"),
            dataset_profile_id=context.get("dataset_profile_id"),
            workflow_plan_id=context.get("workflow_plan_id"),
            feature_engineering_id=context.get("feature_engineering_id"),
            status=status,
            n_samples=fmp_object.validation_summary.n_samples if fmp_object.validation_summary else len(raw_df),
            n_raw_features=n_raw_features,
            n_valid_features=len(retained_features),
            n_final_features=fmp_object.validation_summary.n_features_after_preprocessing if fmp_object.validation_summary else len(final_features),
            n_dropped_features=fmp_object.validation_summary.n_dropped_features if fmp_object.validation_summary else len(filter_result.get("total_dropped", [])),
            target_column=target_column,
            model_ready_artifact_id=artifact_result.get("model_ready_artifact_id"),
            model_ready_artifact_path=artifact_result.get("model_ready_file_path"),
            preprocessor_artifact_id=artifact_result.get("preprocessor_artifact_id"),
            preprocessor_artifact_path=artifact_result.get("preprocessor_file_path"),
            is_ready_for_model_search=fmp_object.model_search_input.ready_for_model_search if fmp_object.model_search_input else False,
            preprocessing_json=fmp_object.model_dump(mode="json"),
            preview_json=artifact_result.get("preview_json"),
            error_message=None if all_errors == [] else "; ".join(all_errors),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.fmp_repo.create(session, fmp_model)

        return fmp_object

    def _persist_failed(
        self, session: Session, fmp_id: str, context: dict, error_message: str,
        n_samples: int = 0, n_raw_features: int = 0, n_valid_features: int = 0,
        n_final_features: int = 0, n_dropped_features: int = 0,
        target_column: str = None,
    ) -> FeaturePreprocessing:
        failed = FeaturePreprocessing(
            id=fmp_id,
            task_id=context.get("task_id"),
            interpretation_id=context.get("interpretation_id"),
            dataset_profile_id=context.get("dataset_profile_id"),
            workflow_plan_id=context.get("workflow_plan_id"),
            feature_engineering_id=context.get("feature_engineering_id"),
            status=FeaturePreprocessingStatus.FAILED,
            n_samples=n_samples,
            n_raw_features=n_raw_features,
            n_valid_features=n_valid_features,
            n_final_features=n_final_features,
            n_dropped_features=n_dropped_features,
            target_column=target_column,
            error_message=error_message,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.fmp_repo.create(session, failed)
        return failed

    def _parse_llm_response(self, raw_text: str) -> dict:
        if not raw_text or not raw_text.strip():
            logger.error("FP Parse: LLM returned empty response (raw_text is None or whitespace)")
            raise ImputationFailedException("LLM returned empty response for plan generation.")
        cleaned = raw_text.strip()
        logger.info("FP Parse: raw response length=%d chars", len(cleaned))
        code_fence_pattern = r"^```(?:json)?\s*\n(.*?)\n```\s*$"
        match = re.search(code_fence_pattern, cleaned, re.DOTALL)
        if match:
            inner = match.group(1).strip()
            logger.info("FP Parse: detected code fence — inner content=%d chars", len(inner))
            cleaned = inner
        else:
            logger.info("FP Parse: no code fence detected, treating raw text as JSON")
        try:
            parsed = json.loads(cleaned)
            logger.info("FP Parse: JSON parsed successfully — top-level keys=%s", list(parsed.keys()))
            return parsed
        except json.JSONDecodeError as e:
            logger.error(
                "FP Parse: JSON parse FAILED — error=%s pos=%d line=%d col=%d",
                str(e), e.pos, e.lineno, e.colno,
            )
            logger.error(
                "FP Parse: first 300 chars: %s",
                raw_text[:300],
            )
            logger.error(
                "FP Parse: last 300 chars: %s",
                raw_text[-300:] if len(raw_text) > 300 else raw_text,
            )
            raise ImputationFailedException(
                f"Failed to parse LLM output as JSON: {str(e)}. "
                f"Raw text (first 500 chars): {raw_text[:500]}"
            )

    def _build_decision_input_from_context(self, context: dict) -> dict:
        """Build a minimal decision input from context when FE decision input is missing."""
        task_context = context.get("task_context") or {}
        fe_context = context.get("feature_engineering_context") or {}
        plan_context = context.get("plan_context") or {}
        data_context = context.get("data_context") or {}

        return {
            "task_context": {
                "task_type": task_context.get("task_type", ""),
                "prediction_target": task_context.get("target_column", ""),
                "evaluation_metric": task_context.get("primary_metric", ""),
                "user_priority": task_context.get("user_priority", []),
            },
            "dataset_context": {
                "row_count": fe_context.get("n_samples", 0),
                "target_column": task_context.get("target_column", ""),
                "input_modalities": [data_context.get("input_modality", "")],
                "data_quality_summary": {},
            },
            "workflow_context": {
                "workflow_plan_id": context.get("workflow_plan_id"),
                "feature_strategy_summary": {},
                "preprocessing_intent": plan_context.get("preprocessing_intent", {}),
            },
            "feature_matrix_context": {
                "artifact_path": fe_context.get("artifact_path", ""),
                "row_count": fe_context.get("n_samples", 0),
                "feature_count": fe_context.get("n_features", 0),
                "feature_groups": [],
                "feature_quality_profile": {},
            },
            "execution_context": {
                "feature_engineering_status": "completed",
                "warnings": [],
                "failed_actions": [],
                "fallback_used": [],
            },
            "known_preprocessing_risks": [],
        }

    def _compute_hash(self, path: str) -> str:
        if not path:
            return ""
        try:
            return hashlib.sha256(path.encode()).hexdigest()[:16]
        except Exception:
            return "hash_unavailable"

    def _check_task_exists(self, session: Session, task_id: str):
        task_spec = self.task_repo.get_by_id(session, task_id)
        if not task_spec:
            from app.shared.common.exceptions import NotFoundException
            raise NotFoundException(f"Task specification with id {task_id} not found.")

    def _to_response(self, fmp: FeaturePreprocessing) -> FeaturePreprocessingResponse:
        resp = None
        if fmp.preprocessing_json:
            try:
                resp = FeaturePreprocessingResponse(**fmp.preprocessing_json)
            except Exception:
                logger.warning(
                    "FP _to_response: failed to reconstruct from preprocessing_json, falling back to columns"
                )
        if resp is None:
            resp = FeaturePreprocessingResponse(
                preprocessing_id=fmp.id or "",
                task_id=fmp.task_id or "",
                interpretation_id=fmp.interpretation_id,
                dataset_profile_id=fmp.dataset_profile_id,
                workflow_plan_id=fmp.workflow_plan_id,
                feature_engineering_id=fmp.feature_engineering_id,
                status=fmp.status or FeaturePreprocessingStatus.PENDING,
                created_at=fmp.created_at,
                updated_at=fmp.updated_at,
            )

        # Attach new output fields from dedicated columns
        if fmp.preprocessing_plan_json:
            resp.preprocessing_plan = PreprocessingPlan(**fmp.preprocessing_plan_json)
        if fmp.registry_snapshot_version:
            resp.preprocessing_registry_snapshot_version = fmp.registry_snapshot_version
        if fmp.execution_report_json:
            resp.execution_report = PreprocessingExecutionReport(**fmp.execution_report_json)
        if fmp.removed_features_json:
            resp.removed_features = [
                RemovedFeature(**rf) for rf in fmp.removed_features_json.get("removed_features", [])
            ]
        if fmp.feature_lineage_json:
            resp.feature_lineage_map = fmp.feature_lineage_json.get("feature_lineage_map", {})
            resp.feature_group_lineage_map = fmp.feature_lineage_json.get("feature_group_lineage_map", {})
        if fmp.explainability_report_json:
            resp.explainability_preservation_report = ExplainabilityPreservationReport(
                **fmp.explainability_report_json
            )
        if fmp.model_ready_artifact_id:
            resp.model_ready_artifacts = [
                ModelReadyArtifact(
                    artifact_id=fmp.model_ready_artifact_id or "",
                    variant_name="default",
                    path=fmp.model_ready_artifact_path or "",
                    usage="fold_safe_template",
                    row_count=fmp.n_samples or 0,
                    feature_count=fmp.n_final_features or 0,
                    artifact_hash=self._compute_hash(fmp.model_ready_artifact_path or ""),
                )
            ]
        if fmp.preprocessor_artifact_id:
            resp.preprocessor_artifacts = [
                PreprocessorArtifact(
                    artifact_id=fmp.preprocessor_artifact_id or "",
                    variant_name="default",
                    path=fmp.preprocessor_artifact_path or "",
                    usage="pipeline_template",
                    artifact_hash=self._compute_hash(fmp.preprocessor_artifact_path or ""),
                )
            ]
        if fmp.provenance_json:
            resp.preprocessing_provenance = PreprocessingProvenance(**fmp.provenance_json)
        if fmp.model_ready_artifact_path:
            resp.model_search_context_input = ModelSearchContextInput(
                model_ready_matrix_path=fmp.model_ready_artifact_path,
                preprocessor_path=fmp.preprocessor_artifact_path,
                feature_summary={"n_final_features": fmp.n_final_features or 0},
            )

        return resp
