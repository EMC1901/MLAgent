import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlmodel import Session

from app.modules.interpretability_analysis.model import InterpretabilityAnalysis
from app.modules.interpretability_analysis.repository import InterpretabilityAnalysisRepository
from app.modules.interpretability_analysis.schemas import (
    InterpretabilityAnalysisCreateRequest,
    InterpretabilityAnalysisResponse,
    GlobalFeatureImportanceItem,
)
from app.modules.interpretability_analysis.enums import (
    InterpretabilityAnalysisStatus,
    InterpretabilityMethodStatus,
)

from app.modules.interpretability_analysis.context_builder import build_interpretability_context
from app.modules.interpretability_analysis.interpretability_input_loader import (
    load_interpretability_analysis_input,
)
from app.modules.interpretability_analysis.model_artifact_loader import load_model_artifact
from app.modules.interpretability_analysis.feature_matrix_loader import load_feature_matrix
from app.modules.interpretability_analysis.prediction_artifact_loader import load_all_prediction_artifacts
from app.modules.interpretability_analysis.interpretability_method_selector import (
    select_interpretability_methods,
)
from app.modules.interpretability_analysis.coefficient_importance_analyzer import (
    compute_coefficient_importance,
)
from app.modules.interpretability_analysis.native_importance_analyzer import (
    compute_native_importance,
)
from app.modules.interpretability_analysis.permutation_importance_analyzer import (
    compute_permutation_importance,
    build_global_importance_from_permutation,
)
from app.modules.interpretability_analysis.shap_analyzer import (
    compute_shap,
    build_global_importance_from_shap,
)
from app.modules.interpretability_analysis.local_explanation_builder import (
    build_local_explanations,
)
from app.modules.interpretability_analysis.high_error_sample_analyzer import (
    analyze_high_error_samples,
)
from app.modules.interpretability_analysis.feature_group_analyzer import (
    build_feature_group_summary,
    classify_feature_group,
)
from app.modules.interpretability_analysis.llm_interpretability_prompt_builder import (
    build_llm_interpretability_context,
)
from app.modules.interpretability_analysis.llm_interpretability_summarizer import (
    LLMInterpretabilitySummarizer,
)
from app.modules.interpretability_analysis.llm_interpretability_parser import (
    parse_llm_interpretability_summary,
)
from app.modules.interpretability_analysis.llm_interpretability_validator import (
    validate_llm_interpretability_summary,
)
from app.modules.interpretability_analysis.llm_interpretability_normalizer import (
    normalize_llm_interpretability_summary,
)
from app.modules.interpretability_analysis.final_output_input_builder import (
    build_final_output_input,
)
from app.modules.interpretability_analysis.interpretability_artifact_manager import (
    save_interpretability_artifacts,
)
from app.modules.interpretability_analysis.builder import build_response

from app.modules.interpretability_analysis.exceptions import (
    InterpretabilityAnalysisNotFoundException,
)

logger = logging.getLogger(__name__)


class InterpretabilityAnalysisService:

    def __init__(self):
        self.repo = InterpretabilityAnalysisRepository()
        self.llm_summarizer = LLMInterpretabilitySummarizer()

    def create_interpretability_analysis(
        self,
        session: Session,
        task_id: str,
        request: InterpretabilityAnalysisCreateRequest,
    ) -> InterpretabilityAnalysisResponse:
        warnings_list: list = []

        # Step 1: Build context - validate upstream FinalPipelineSelection
        fps = build_interpretability_context(
            session, task_id, request.final_pipeline_selection_id
        )

        # Early return if not force_rerun and existing analysis is available
        if not request.force_rerun:
            existing = self.repo.get_latest_by_task_id(session, task_id)
            if existing and existing.final_pipeline_selection_id == fps.id and existing.status in (
                InterpretabilityAnalysisStatus.ANALYZED,
                InterpretabilityAnalysisStatus.ANALYZED_WITH_WARNING,
            ):
                return self.get_interpretability_analysis(session, existing.id)

        # Step 2: Load interpretability analysis input
        ia_input = load_interpretability_analysis_input(fps)

        # Step 3: Validate paths
        _validate_artifact_paths(ia_input.model_artifact_path, ia_input.model_ready_matrix_path)

        # Step 4: Load model artifact
        try:
            model = load_model_artifact(ia_input.model_artifact_path)
        except Exception as e:
            logger.error("Failed to load model artifact: %s", str(e))
            return _build_failed_response(
                session, task_id, fps.id, request, str(e), warnings_list
            )

        # Step 5: Load feature matrix
        try:
            max_samples = request.max_shap_samples if request.interpretability_profile != "full" else None

            # If upstream didn't set feature_columns, derive them from the matrix
            fc_input = list(ia_input.feature_columns) if ia_input.feature_columns else None
            X, y = load_feature_matrix(
                matrix_path=ia_input.model_ready_matrix_path,
                feature_columns=fc_input or [],
                target_column=ia_input.target_column,
                max_samples=max_samples,
            )
            if fc_input:
                feature_columns = [c for c in fc_input if c in X.columns]
            else:
                # Derive features from matrix: all numeric columns except target
                feature_columns = [
                    c for c in X.select_dtypes(include=["number"]).columns
                    if c != ia_input.target_column
                ]
                logger.info("Derived %d feature columns from matrix.", len(feature_columns))
        except Exception as e:
            logger.error("Failed to load feature matrix: %s", str(e))
            return _build_failed_response(
                session, task_id, fps.id, request, str(e), warnings_list
            )

        # Step 6: Load prediction artifacts
        y_pred = None
        try:
            if ia_input.prediction_artifact_paths:
                pred_df = load_all_prediction_artifacts(ia_input.prediction_artifact_paths)
                pred_cols = ["y_pred", "prediction", "pred", "predicted"]
                for col in pred_cols:
                    if col in pred_df.columns:
                        y_pred = pred_df[col].values
                        break
                if y_pred is None and len(pred_df.columns) > 0:
                    y_pred = pred_df.iloc[:, 0].values
        except Exception as e:
            logger.warning("Failed to load prediction artifacts: %s", str(e))
            warnings_list.append(f"Prediction artifact load warning: {str(e)}")

        # Step 7: Select interpretability methods
        method_plan = select_interpretability_methods(
            model_family=ia_input.final_model_family,
            include_shap=request.include_shap,
            include_permutation=request.include_permutation_importance,
            profile=request.interpretability_profile,
        )
        warnings_list.extend(method_plan.notes)

        # Step 8: Compute coefficient / native / permutation importance
        all_importance: List[GlobalFeatureImportanceItem] = []
        permutation_results = None
        method_statuses: Dict[str, str] = {}

        if "coefficient" in method_plan.methods_selected:
            try:
                coef_importance = compute_coefficient_importance(model, feature_columns)
                all_importance.extend(coef_importance)
                method_statuses["coefficient"] = InterpretabilityMethodStatus.COMPUTED
            except Exception as e:
                logger.warning("Coefficient importance failed: %s", str(e))
                method_statuses["coefficient"] = InterpretabilityMethodStatus.FAILED
                warnings_list.append(f"Coefficient importance: {str(e)}")

        if "native_importance" in method_plan.methods_selected:
            try:
                native_importance = compute_native_importance(model, feature_columns)
                all_importance.extend(native_importance)
                method_statuses["native_importance"] = InterpretabilityMethodStatus.COMPUTED
            except Exception as e:
                logger.warning("Native importance failed: %s", str(e))
                method_statuses["native_importance"] = InterpretabilityMethodStatus.FAILED
                warnings_list.append(f"Native importance: {str(e)}")

        if "permutation_importance" in method_plan.methods_selected:
            try:
                permutation_results = compute_permutation_importance(
                    model, X, y, feature_columns
                )
                perm_importance = build_global_importance_from_permutation(permutation_results)
                all_importance.extend(perm_importance)
                method_statuses["permutation_importance"] = InterpretabilityMethodStatus.COMPUTED
            except Exception as e:
                logger.warning("Permutation importance failed: %s", str(e))
                method_statuses["permutation_importance"] = InterpretabilityMethodStatus.FAILED
                warnings_list.append(f"Permutation importance: {str(e)}")

        if not all_importance and method_plan.methods_selected:
            try:
                logger.info("No importance results; computing permutation importance as fallback.")
                permutation_results = compute_permutation_importance(
                    model, X, y, feature_columns, n_repeats=5
                )
                perm_importance = build_global_importance_from_permutation(permutation_results)
                all_importance.extend(perm_importance)
                method_statuses["permutation_importance"] = InterpretabilityMethodStatus.FALLBACK_USED
            except Exception as e:
                logger.error("Fallback permutation importance also failed: %s", str(e))

        # Step 9: Compute SHAP
        shap_summary = None
        shap_values = None
        if "shap" in method_plan.methods_selected:
            try:
                shap_summary, shap_values, shap_warnings = compute_shap(
                    model=model,
                    X=X,
                    feature_columns=feature_columns,
                    explainer_type=method_plan.shap_explainer_type,
                    max_samples=request.max_shap_samples,
                )
                warnings_list.extend(shap_warnings)
                method_statuses["shap"] = InterpretabilityMethodStatus.COMPUTED if shap_summary.shap_available else InterpretabilityMethodStatus.FAILED
                if shap_summary.shap_available:
                    shap_importance = build_global_importance_from_shap(shap_summary)
                    existing_names = {fi.feature_name for fi in all_importance}
                    all_importance.extend([si for si in shap_importance if si.feature_name not in existing_names])
            except Exception as e:
                logger.warning("SHAP computation failed: %s", str(e))
                method_statuses["shap"] = InterpretabilityMethodStatus.FAILED
                warnings_list.append(f"SHAP: {str(e)}")

        # Sort and re-rank
        all_importance.sort(key=lambda x: x.importance_value, reverse=True)
        for i, fi in enumerate(all_importance, start=1):
            fi.importance_rank = i
            fi.feature_group = classify_feature_group(fi.feature_name)

        top_importance = all_importance[:30]

        # Step 10: Local explanations
        local_explanations = []
        try:
            local_explanations = build_local_explanations(
                X=X,
                y_true=y,
                y_pred=y_pred,
                feature_columns=feature_columns,
                shap_values=shap_values,
                max_explanations=request.max_local_explanations,
            )
        except Exception as e:
            logger.warning("Local explanations failed: %s", str(e))
            warnings_list.append(f"Local explanations: {str(e)}")

        # Step 11: High-error sample analysis
        high_error_analysis = []
        if request.include_high_error_samples:
            try:
                high_error_analysis = analyze_high_error_samples(
                    X=X,
                    y_true=y,
                    y_pred=y_pred,
                    feature_columns=feature_columns,
                    shap_values=shap_values,
                    max_samples=request.max_local_explanations,
                )
            except Exception as e:
                logger.warning("High-error analysis failed: %s", str(e))
                warnings_list.append(f"High-error analysis: {str(e)}")

        # Step 12: Feature group summary
        feature_group_summary = build_feature_group_summary(top_importance)

        # Step 13-16: LLM interpretability summarizer
        llm_summary = None
        material_insight = None
        llm_raw_request = None
        llm_raw_response = None
        llm_used = False
        llm_confidence = None

        if request.use_llm_summarizer:
            try:
                llm_context = build_llm_interpretability_context(
                    task_summary={
                        "task_type": ia_input.task_type,
                        "target_column": ia_input.target_column,
                        "primary_metric": ia_input.primary_metric,
                    },
                    final_model_summary={
                        "model_id": ia_input.final_model_id,
                        "model_family": ia_input.final_model_family,
                    },
                    final_metric_summary={
                        "primary_metric": ia_input.primary_metric,
                        "primary_metric_value": ia_input.primary_metric_value,
                    },
                    global_feature_importance=top_importance,
                    shap_summary=shap_summary,
                    feature_group_summary=feature_group_summary,
                    high_error_samples=high_error_analysis if high_error_analysis else None,
                )
                llm_raw_request = llm_context

                llm_result = self.llm_summarizer.summarize(
                    llm_context["system_prompt"], llm_context["user_message"]
                )
                raw_response = llm_result.get("raw_response", "")
                llm_raw_response = raw_response

                llm_summary = parse_llm_interpretability_summary(raw_response)

                validation = validate_llm_interpretability_summary(llm_summary, raw_response)

                if validation.is_valid:
                    llm_summary = normalize_llm_interpretability_summary(llm_summary)
                    llm_used = True
                    llm_confidence = llm_summary.confidence_level
                    material_insight = {
                        "top_material_patterns": [p.model_dump() if hasattr(p, "model_dump") else p for p in llm_summary.top_material_patterns],
                        "feature_groups_interpretation": [g.model_dump() if hasattr(g, "model_dump") else g for g in llm_summary.feature_groups_interpretation],
                        "domain_hypotheses": llm_summary.domain_hypotheses,
                        "limitations": llm_summary.limitations,
                        "confidence_level": llm_summary.confidence_level,
                    }
                else:
                    logger.warning("LLM interpretability validation failed: %s", validation.issues)
                    llm_summary = None
                    warnings_list.append(
                        f"LLM interpretability summary validation failed: {'; '.join(validation.issues)}"
                    )

            except Exception as e:
                logger.error("LLM interpretability summarizer failed: %s", str(e))
                warnings_list.append(f"LLM interpretability summary: {str(e)}")

        # Step 17: Build Final Output Input
        final_output_input = None
        ready_for_fo = False
        try:
            final_output_input = build_final_output_input(
                interpretability_analysis_id="",  # Will be replaced after persist
                final_pipeline_selection_id=fps.id,
                task_id=task_id,
                final_model_id=ia_input.final_model_id or "",
                final_trial_id=ia_input.final_trial_id or "",
                model_artifact_path=ia_input.model_artifact_path or "",
                prediction_artifact_paths=ia_input.prediction_artifact_paths,
                metric_summary={
                    "primary_metric": ia_input.primary_metric,
                    "primary_metric_value": ia_input.primary_metric_value,
                },
                selection_summary={
                    "selection_reason": ia_input.selection_reason_summary,
                    "final_pipeline_selection_id": fps.id,
                },
                global_feature_importance=[
                    fi.model_dump() for fi in top_importance
                ],
                shap_summary=shap_summary.model_dump() if shap_summary else None,
                material_insight_summary=material_insight,
                interpretability_artifacts={},
                workflow_trace_refs={},
            )
            ready_for_fo = True
        except Exception as e:
            logger.warning("Final output input build failed: %s", str(e))
            warnings_list.append(f"Final output input: {str(e)}")

        # Determine status
        status = InterpretabilityAnalysisStatus.ANALYZED
        if warnings_list:
            status = InterpretabilityAnalysisStatus.ANALYZED_WITH_WARNING

        # Persist
        ia_id = f"ia_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        record = InterpretabilityAnalysis(
            id=ia_id,
            task_id=task_id,
            final_pipeline_selection_id=fps.id,
            metric_evaluation_id=fps.metric_evaluation_id,
            pipeline_execution_id=fps.pipeline_execution_id,
            status=status,
            analysis_profile=request.interpretability_profile,
            final_model_id=ia_input.final_model_id,
            final_model_family=ia_input.final_model_family,
            final_trial_id=ia_input.final_trial_id,
            methods_used_json={
                "methods": list(method_statuses.keys()),
                "statuses": method_statuses,
            },
            global_feature_importance_json={"items": [fi.model_dump() for fi in top_importance]},
            permutation_importance_json={
                "items": [pr.model_dump() for pr in permutation_results]
            } if permutation_results else None,
            shap_summary_json=shap_summary.model_dump() if shap_summary else None,
            local_explanations_json={"items": [le.model_dump() for le in local_explanations]},
            high_error_sample_analysis_json={"items": [he.model_dump() for he in high_error_analysis]},
            material_insight_summary_json=material_insight,
            llm_summary_json=llm_summary.model_dump() if llm_summary else None,
            final_output_input_json=final_output_input.model_dump() if final_output_input else None,
            artifact_manifest_json=None,
            ready_for_final_output=ready_for_fo,
            llm_used=llm_used,
            llm_confidence_level=llm_confidence,
            llm_request_json=llm_raw_request,
            llm_response_json={"raw_response": llm_raw_response} if llm_raw_response else None,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        record = self.repo.create(session, record)

        # Update final output input with real ID
        if final_output_input:
            final_output_input.interpretability_analysis_id = ia_id
            record.final_output_input_json = final_output_input.model_dump()
            record = self.repo.update(session, record)

        # Save artifacts
        try:
            artifact_manifest = save_interpretability_artifacts(
                interpretability_analysis_id=ia_id,
                analysis_result=_safe_dump(record),
                global_feature_importance={"items": [fi.model_dump() for fi in top_importance]},
                permutation_importance={"items": [pr.model_dump() for pr in permutation_results]} if permutation_results else None,
                shap_summary=shap_summary.model_dump() if shap_summary else None,
                local_explanations={"items": [le.model_dump() for le in local_explanations]},
                high_error_sample_analysis={"items": [he.model_dump() for he in high_error_analysis]},
                feature_group_summary=feature_group_summary.model_dump(),
                material_insight_summary=material_insight,
                llm_interpretability_summary=llm_summary.model_dump() if llm_summary else None,
                final_output_input=final_output_input.model_dump() if final_output_input else None,
            )
            record.artifact_manifest_json = artifact_manifest.model_dump()
            record = self.repo.update(session, record)
        except Exception as e:
            logger.warning("Artifact save failed: %s", str(e))
            warnings_list.append(f"Artifact save: {str(e)}")

        return build_response(record=record, warnings=warnings_list)

    def get_interpretability_analysis(
        self, session: Session, ia_id: str
    ) -> InterpretabilityAnalysisResponse:
        record = self.repo.get_by_id(session, ia_id)
        if not record:
            raise InterpretabilityAnalysisNotFoundException(
                f"InterpretabilityAnalysis {ia_id} not found."
            )
        return self._record_to_response(record)

    def get_latest_by_task_id(
        self, session: Session, task_id: str
    ) -> InterpretabilityAnalysisResponse:
        record = self.repo.get_latest_by_task_id(session, task_id)
        if not record:
            raise InterpretabilityAnalysisNotFoundException(
                f"No InterpretabilityAnalysis found for task {task_id}."
            )
        return self._record_to_response(record)

    def rerun_interpretability_analysis(
        self, session: Session, task_id: str
    ) -> InterpretabilityAnalysisResponse:
        request = InterpretabilityAnalysisCreateRequest(force_rerun=True)
        return self.create_interpretability_analysis(session, task_id, request)

    def get_feature_importance(
        self, session: Session, ia_id: str
    ) -> dict:
        record = self.repo.get_by_id(session, ia_id)
        if not record:
            raise InterpretabilityAnalysisNotFoundException(
                f"InterpretabilityAnalysis {ia_id} not found."
            )
        return record.global_feature_importance_json or {}

    def get_shap_summary(
        self, session: Session, ia_id: str
    ) -> dict:
        record = self.repo.get_by_id(session, ia_id)
        if not record:
            raise InterpretabilityAnalysisNotFoundException(
                f"InterpretabilityAnalysis {ia_id} not found."
            )
        return record.shap_summary_json or {}

    def get_local_explanations(
        self, session: Session, ia_id: str
    ) -> dict:
        record = self.repo.get_by_id(session, ia_id)
        if not record:
            raise InterpretabilityAnalysisNotFoundException(
                f"InterpretabilityAnalysis {ia_id} not found."
            )
        return record.local_explanations_json or {}

    def get_final_output_input(
        self, session: Session, ia_id: str
    ) -> dict:
        record = self.repo.get_by_id(session, ia_id)
        if not record:
            raise InterpretabilityAnalysisNotFoundException(
                f"InterpretabilityAnalysis {ia_id} not found."
            )
        return record.final_output_input_json or {}

    def _record_to_response(self, record: InterpretabilityAnalysis) -> InterpretabilityAnalysisResponse:
        return build_response(record=record)


from app.modules.interpretability_analysis.exceptions import FeatureMatrixLoadException


def _validate_artifact_paths(model_path, matrix_path):
    allowed_dir = os.path.normpath("/app/artifacts")
    for path, name in [(model_path, "model"), (matrix_path, "matrix")]:
        if not path:
            continue
        normalized = os.path.normpath(path)
        if ".." in normalized or not normalized.startswith(allowed_dir):
            raise FeatureMatrixLoadException(
                f"{name} path is outside allowed directory: {path}"
            )


def _build_failed_response(
    session: Session,
    task_id: str,
    fps_id: str,
    request: InterpretabilityAnalysisCreateRequest,
    error_message: str,
    warnings_list: list,
) -> InterpretabilityAnalysisResponse:
    now = datetime.now(timezone.utc)
    ia_id = f"ia_{uuid.uuid4().hex[:8]}"

    record = InterpretabilityAnalysis(
        id=ia_id,
        task_id=task_id,
        final_pipeline_selection_id=fps_id,
        status=InterpretabilityAnalysisStatus.FAILED,
        analysis_profile=request.interpretability_profile,
        error_message=error_message,
        created_at=now,
        updated_at=now,
    )
    repo = InterpretabilityAnalysisRepository()
    record = repo.create(session, record)

    return InterpretabilityAnalysisResponse(
        interpretability_analysis_id=record.id,
        task_id=task_id,
        final_pipeline_selection_id=fps_id,
        status=InterpretabilityAnalysisStatus.FAILED,
        analysis_profile=request.interpretability_profile,
        warnings=warnings_list,
        error_message=error_message,
        created_at=now,
        updated_at=now,
    )


def _safe_dump(obj) -> Optional[dict]:
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, list):
        return [_safe_dump(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _safe_dump(v) for k, v in obj.items()}
    return obj
