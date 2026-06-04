import os
import uuid
import time
import logging
import numpy as np
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlmodel import Session

logger = logging.getLogger(__name__)

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
    compute_shap_interactions,
    compute_shap_dependence,
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
    _build_lineage_group_map,
)
from app.modules.interpretability_analysis.cross_method_consensus import (
    compute_cross_method_consensus,
)
from app.modules.interpretability_analysis.correlation_analyzer import (
    compute_correlation_analysis,
)
from app.modules.interpretability_analysis.partial_dependence_analyzer import (
    compute_partial_dependence,
)
from app.modules.interpretability_analysis.residual_analyzer import (
    analyze_residuals,
)
from app.modules.interpretability_analysis.systematic_error_detector import (
    detect_systematic_errors,
)
from app.modules.interpretability_analysis.physics_constraint_checker import (
    check_physics_constraints,
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
from app.shared.common.exceptions import BusinessException


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

        # Step 1: Build context - gather upstream data
        context = build_interpretability_context(session, task_id)
        warnings_list.extend(context.warnings)

        # ---- [0/25] Pre-check: early return if cached ----
        if not request.force_rerun:
            existing = self.repo.get_latest_by_task_id(session, task_id)
            if existing and existing.metric_evaluation_id == context.metric_evaluation.id and existing.status in (
                InterpretabilityAnalysisStatus.ANALYZED,
                InterpretabilityAnalysisStatus.ANALYZED_WITH_WARNING,
            ):
                logger.info("[0/25] Returning cached analysis — ia_id=%s", existing.id)
                return self.get_interpretability_analysis(session, existing.id)

        started_at = time.time()
        logger.info("=== Interpretability Analysis — task=%s ===", task_id)

        # ---- [1/25] Build context ----
        logger.info("[1/25] Context built — me=%s pe=%s pg=%s",
                     context.metric_evaluation.id, context.pipeline_execution.id,
                     context.pipeline_generation.id)

        # ---- [2/25] Load interpretability analysis input ----
        ia_input = load_interpretability_analysis_input(context)
        logger.info("[2/25] Input loaded — model=%s predictions=%d",
                     ia_input.model_artifact_path, len(ia_input.prediction_artifact_paths))

        # ---- [3/25] Release DB transaction ----
        logger.info("[3/25] Releasing read transaction ...")
        session.commit()
        logger.info("[3/25] Transaction released")

        # ---- [4/25] Validate paths ----
        _validate_artifact_paths(ia_input.model_artifact_path, ia_input.model_ready_matrix_path)

        # ---- [5/25] Load model artifact ----
        logger.info("[5/25] Loading model artifact ...")
        t0 = time.time()
        try:
            model = load_model_artifact(ia_input.model_artifact_path)
            logger.info("[5/25] Done — type=%s (%.1fs)", type(model).__name__, time.time() - t0)
        except Exception as e:
            logger.error("[5/25] FAILED — %s", str(e))
            return _build_failed_response(
                session, task_id, request, str(e), warnings_list
            )

        # ---- [6/25] Load feature matrix ----
        logger.info("[6/25] Loading feature matrix ...")
        t0 = time.time()
        try:
            max_samples = request.max_shap_samples if request.interpretability_profile != "full" else None

            fc_input = list(ia_input.feature_columns) if ia_input.feature_columns else None
            X, y, sampled_indices = load_feature_matrix(
                matrix_path=ia_input.model_ready_matrix_path,
                feature_columns=fc_input or [],
                target_column=ia_input.target_column,
                max_samples=max_samples,
            )
            if fc_input:
                feature_columns = [c for c in fc_input if c in X.columns]
            else:
                feature_columns = [
                    c for c in X.select_dtypes(include=["number"]).columns
                    if c != ia_input.target_column
                ]
            logger.info("[6/25] Done — shape=%s features=%d (%.1fs)",
                         X.shape, len(feature_columns), time.time() - t0)
        except Exception as e:
            logger.error("[6/25] FAILED — %s", str(e))
            return _build_failed_response(
                session, task_id, request, str(e), warnings_list
            )

        # ---- [7/25] Load prediction artifacts ----
        logger.info("[7/25] Loading prediction artifacts ...")
        y_pred = None
        y_true_aligned = None  # y_true from prediction files, row-aligned with y_pred
        try:
            if ia_input.prediction_artifact_paths:
                pred_df = load_all_prediction_artifacts(ia_input.prediction_artifact_paths)
                pred_cols = ["y_pred", "prediction", "pred", "predicted"]
                for col in pred_cols:
                    if col in pred_df.columns:
                        y_pred = pred_df[col]
                        break
                if y_pred is None and len(pred_df.columns) > 0:
                    y_pred = pred_df.iloc[:, 0]
                # Extract y_true from prediction files for aligned residual analysis.
                # Do NOT use `y` from the feature matrix — the rows are in a
                # different order (original vs fold-grouped), which produces
                # garbage R² / RMSE / MAE.
                if "y_true" in pred_df.columns:
                    y_true_aligned = pred_df["y_true"]
            logger.info("[7/25] Done — %d prediction artifacts loaded",
                         len(ia_input.prediction_artifact_paths))

            # Align predictions with sampled X to prevent cross-index errors
            if sampled_indices is not None and y_pred is not None:
                common = sampled_indices.intersection(y_pred.index)
                y_pred = y_pred.loc[common]
                if y_true_aligned is not None:
                    y_true_aligned = y_true_aligned.loc[common]
                logger.info("[7/25] Aligned predictions to sampled X: %d rows", len(common))

        except Exception as e:
            logger.warning("[7/25] Warning — %s", str(e))
            warnings_list.append(f"Prediction artifact load warning: {str(e)}")

        # ---- [8/25] Select interpretability methods ----
        logger.info("[8/25] Selecting methods (family=%s profile=%s) ...",
              ia_input.final_model_family, request.interpretability_profile)
        method_plan = select_interpretability_methods(
            model_family=ia_input.final_model_family,
            include_shap=request.include_shap,
            include_permutation=request.include_permutation_importance,
            profile=request.interpretability_profile,
        )
        warnings_list.extend(method_plan.notes)
        logger.info("[8/25] Done — methods=%s", method_plan.methods_selected)

        # ---- [9/25] Compute importance (coefficient / native / permutation) ----
        logger.info("[9/25] Computing importance (%s) ...", method_plan.methods_selected)
        t0 = time.time()
        all_importance: List[GlobalFeatureImportanceItem] = []
        permutation_results = None
        method_statuses: Dict[str, str] = {}
        per_method_importance: Dict[str, List[Dict[str, Any]]] = {}

        if "coefficient" in method_plan.methods_selected:
            try:
                coef_importance = compute_coefficient_importance(model, feature_columns)
                all_importance.extend(coef_importance)
                per_method_importance["coefficient"] = [fi.model_dump() for fi in coef_importance]
                method_statuses["coefficient"] = InterpretabilityMethodStatus.COMPUTED
            except Exception as e:
                logger.warning("Coefficient importance failed: %s", str(e))
                method_statuses["coefficient"] = InterpretabilityMethodStatus.FAILED
                warnings_list.append(f"Coefficient importance: {str(e)}")

        if "native_importance" in method_plan.methods_selected:
            try:
                native_importance = compute_native_importance(model, feature_columns)
                all_importance.extend(native_importance)
                per_method_importance["native_importance"] = [fi.model_dump() for fi in native_importance]
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
                per_method_importance["permutation_importance"] = [fi.model_dump() for fi in perm_importance]
                method_statuses["permutation_importance"] = InterpretabilityMethodStatus.COMPUTED
            except Exception as e:
                logger.warning("Permutation importance failed: %s", str(e))
                method_statuses["permutation_importance"] = InterpretabilityMethodStatus.FAILED
                warnings_list.append(f"Permutation importance: {str(e)}")

        if not all_importance and method_plan.methods_selected:
            try:
                logger.info("[9/25] No importance results — using permutation fallback ...")
                permutation_results = compute_permutation_importance(
                    model, X, y, feature_columns, n_repeats=5
                )
                perm_importance = build_global_importance_from_permutation(permutation_results)
                all_importance.extend(perm_importance)
                per_method_importance["permutation_importance"] = [fi.model_dump() for fi in perm_importance]
                method_statuses["permutation_importance"] = InterpretabilityMethodStatus.FALLBACK_USED
            except Exception as e:
                logger.error("[9/25] Fallback permutation also failed: %s", str(e))
        logger.info("[9/25] Done — %d items (%.1fs)", len(all_importance), time.time() - t0)

        # ---- [10/25] Compute SHAP ----
        shap_summary = None
        shap_values = None
        if "shap" in method_plan.methods_selected:
            logger.info("[10/25] Computing SHAP (explainer=%s) ...",
                        method_plan.shap_explainer_type)
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
                    per_method_importance["shap"] = [fi.model_dump() for fi in shap_importance]
                    existing_names = {fi.feature_name for fi in all_importance}
                    all_importance.extend([si for si in shap_importance if si.feature_name not in existing_names])
            except Exception as e:
                logger.warning("[10/25] SHAP failed: %s", str(e))
                method_statuses["shap"] = InterpretabilityMethodStatus.FAILED
                warnings_list.append(f"SHAP: {str(e)}")
            logger.info("[10/25] Done — available=%s",
                         shap_summary.shap_available if shap_summary else False)

        # ---- Sort and re-rank ----
        logger.info("[11/25] Sorting and ranking features ...")
        lineage_group_map = _build_lineage_group_map(ia_input.feature_lineage) if ia_input.feature_lineage else {}
        all_importance.sort(key=lambda x: x.importance_value, reverse=True)
        for i, fi in enumerate(all_importance, start=1):
            fi.importance_rank = i
            fi.feature_group = classify_feature_group(fi.feature_name, lineage_group_map)

        top_importance = all_importance[:30]

        # ---- [12/25] Correlation analysis ----
        correlation_analysis = None
        if request.include_correlation:
            logger.info("[12/25] Computing correlation analysis ...")
            t0 = time.time()
            try:
                correlation_analysis = compute_correlation_analysis(
                    X=X, y=y, feature_columns=feature_columns,
                    top_n_features=request.correlation_top_n_features,
                )
            except Exception as e:
                logger.warning("Correlation analysis failed: %s", str(e))
                warnings_list.append(f"Correlation analysis: {str(e)}")

        # Step 11: Cross-method consensus
        cross_method_consensus = None
        if request.include_cross_method_consensus and len(per_method_importance) >= 2:
            try:
                cross_method_consensus = compute_cross_method_consensus(per_method_importance)
            except Exception as e:
                logger.warning("Cross-method consensus failed: %s", str(e))
                warnings_list.append(f"Cross-method consensus: {str(e)}")

        # Step 12: Partial dependence
        partial_dependence = None
        if request.include_pdp:
            try:
                partial_dependence = compute_partial_dependence(
                    model=model, X=X, feature_columns=feature_columns,
                    top_n_features=request.pdp_top_n_features,
                )
            except Exception as e:
                logger.warning("Partial dependence failed: %s", str(e))
                warnings_list.append(f"Partial dependence: {str(e)}")

        # Step 13: Residual analysis
        # Use y_true_aligned from prediction artifacts (row-aligned with y_pred),
        # NOT `y` from the feature matrix which has a different row order.
        residual_analysis = None
        if request.include_residual_analysis and y_true_aligned is not None and y_pred is not None:
            try:
                residual_analysis = analyze_residuals(
                    y_true=y_true_aligned, y_pred=y_pred, X=X, feature_columns=feature_columns,
                )
            except Exception as e:
                logger.warning("Residual analysis failed: %s", str(e))
                warnings_list.append(f"Residual analysis: {str(e)}")

        # Step 14: Systematic error detection
        systematic_errors = None
        if request.include_residual_analysis and y_true_aligned is not None and y_pred is not None:
            try:
                systematic_errors = detect_systematic_errors(
                    X=X, y_true=y_true_aligned, y_pred=y_pred, feature_columns=feature_columns,
                )
            except Exception as e:
                logger.warning("Systematic error detection failed: %s", str(e))
                warnings_list.append(f"Systematic error detection: {str(e)}")

        # Step 15: Physics constraint check
        physics_constraints = None
        if request.include_physics_constraints and y_pred is not None:
            try:
                physics_constraints = check_physics_constraints(
                    y_pred=y_pred,
                    target_property=ia_input.target_column,
                    prediction_target_name=ia_input.prediction_target_name,
                )
            except Exception as e:
                logger.warning("Physics constraint check failed: %s", str(e))
                warnings_list.append(f"Physics constraint check: {str(e)}")

        # Step 16: SHAP interaction values
        shap_interactions = None
        if "shap" in method_plan.methods_selected and shap_values is not None:
            try:
                shap_interactions = compute_shap_interactions(
                    shap_values=shap_values,
                    feature_columns=feature_columns,
                    top_n=10,
                )
            except Exception as e:
                logger.warning("SHAP interaction computation failed: %s", str(e))
                warnings_list.append(f"SHAP interactions: {str(e)}")

        # Step 17: SHAP dependence data
        shap_dependence = None
        if "shap" in method_plan.methods_selected and shap_values is not None:
            try:
                shap_dependence = compute_shap_dependence(
                    shap_values=shap_values,
                    X=X,
                    feature_columns=feature_columns,
                    top_n=10,
                )
            except Exception as e:
                logger.warning("SHAP dependence computation failed: %s", str(e))
                warnings_list.append(f"SHAP dependence: {str(e)}")

        # Step 18: Local explanations
        _y_true = y_true_aligned if y_true_aligned is not None else y
        _y_pred_arr = np.asarray(y_pred) if y_pred is not None else None
        local_explanations = []
        try:
            local_explanations = build_local_explanations(
                X=X,
                y_true=_y_true,
                y_pred=_y_pred_arr,
                feature_columns=feature_columns,
                shap_values=shap_values,
                max_explanations=request.max_local_explanations,
            )
        except Exception as e:
            logger.warning("Local explanations failed: %s", str(e))
            warnings_list.append(f"Local explanations: {str(e)}")

        # Step 19: High-error sample analysis
        high_error_analysis = []
        if request.include_high_error_samples:
            try:
                high_error_analysis = analyze_high_error_samples(
                    X=X,
                    y_true=y_true_aligned if y_true_aligned is not None else y,
                    y_pred=y_pred,
                    feature_columns=feature_columns,
                    shap_values=shap_values,
                    max_samples=request.max_local_explanations,
                )
            except Exception as e:
                logger.warning("High-error analysis failed: %s", str(e))
                warnings_list.append(f"High-error analysis: {str(e)}")

        # Step 20: Feature group summary
        try:
            feature_group_summary = build_feature_group_summary(
                top_importance,
                feature_lineage=ia_input.feature_lineage,
            )
        except Exception as e:
            logger.warning("Feature group summary failed: %s", str(e))
            warnings_list.append(f"Feature group summary: {str(e)}")
            feature_group_summary = FeatureGroupSummary()

        # Step 21-24: LLM interpretability summarizer
        llm_summary = None
        material_insight = None
        llm_raw_request = None
        llm_raw_response = None
        llm_used = False
        llm_confidence = None

        if request.use_llm_summarizer:
            logger.info("[23/25] Calling LLM summarizer ...")
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
                    cross_method_consensus=cross_method_consensus,
                    partial_dependence=partial_dependence,
                    correlation_analysis=correlation_analysis,
                    residual_analysis=residual_analysis,
                    physics_constraints=physics_constraints,
                    material_domain=ia_input.material_domain,
                    dataset_description=ia_input.dataset_description,
                    stop_rationale=ia_input.stop_rationale,
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
            logger.info("[23/25] LLM done — used=%s confidence=%s", llm_used, llm_confidence)

        # ---- [24/25] Build Final Output Input ----
        logger.info("[24/25] Building final output input ...")
        final_output_input = None
        ready_for_fo = False
        try:
            final_output_input = build_final_output_input(
                interpretability_analysis_id="",  # Will be replaced after persist
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
                    "metric_evaluation_id": ia_input.metric_evaluation_id,
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

        # ---- [25/25] Persist and build response ----
        logger.info("[25/25] Persisting record ...")
        ia_id = f"ia_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        record = InterpretabilityAnalysis(
            id=ia_id,
            task_id=task_id,
            metric_evaluation_id=ia_input.metric_evaluation_id,
            pipeline_execution_id=ia_input.pipeline_execution_id,
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
            cross_method_consensus_json=cross_method_consensus,
            partial_dependence_json=partial_dependence,
            residual_analysis_json=residual_analysis,
            correlation_analysis_json=correlation_analysis,
            physics_constraint_check_json=physics_constraints,
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

        try:
            record = self.repo.create(session, record)
        except Exception as e:
            logger.error("Failed to persist interpretability analysis: %s", str(e))
            session.rollback()
            raise BusinessException(
                f"Failed to save analysis result to database: {str(e)}",
                "INTERPRETABILITY_PERSIST_FAILED",
            )

        # Update final output input with real ID
        if final_output_input:
            final_output_input.interpretability_analysis_id = ia_id
            record.final_output_input_json = final_output_input.model_dump()
            try:
                record = self.repo.update(session, record)
            except Exception as e:
                logger.warning("Failed to update final output input ID: %s", str(e))

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
                cross_method_consensus=cross_method_consensus,
                partial_dependence=partial_dependence,
                residual_analysis=residual_analysis,
                correlation_analysis=correlation_analysis,
                physics_constraints=physics_constraints,
                shap_interactions=shap_interactions,
                shap_dependence=shap_dependence,
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

        total_dur = time.time() - started_at
        logger.info("[25/25] Done — ia_id=%s status=%s features=%d methods=%s | TOTAL %.1fs",
                     ia_id, status, len(top_importance),
                     list(method_statuses.keys()), total_dur)
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
    request: InterpretabilityAnalysisCreateRequest,
    error_message: str,
    warnings_list: list,
) -> InterpretabilityAnalysisResponse:
    now = datetime.now(timezone.utc)
    ia_id = f"ia_{uuid.uuid4().hex[:8]}"

    record = InterpretabilityAnalysis(
        id=ia_id,
        task_id=task_id,
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
