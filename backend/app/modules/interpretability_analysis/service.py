import os
import uuid
import time
import logging
import numpy as np
import pandas as pd
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
    ScientificInsightReport,
    FeatureGroupSummary,
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
from app.modules.interpretability_analysis.physics_rule_registry import (
    check_physics_constraints,
)
from app.modules.interpretability_analysis.llm_interpretability_summarizer import (
    LLMInterpretabilitySummarizer,
)
from app.modules.interpretability_analysis.final_output_input_builder import (
    build_final_output_input,
)
from app.modules.interpretability_analysis.interpretability_artifact_manager import (
    save_interpretability_artifacts,
)
from app.modules.interpretability_analysis.builder import build_response

# New: Scientific Insight Engine imports
from app.modules.interpretability_analysis.evidence_normalizer import (
    build_evidence_units,
    build_feature_evidence_profiles,
)
from app.modules.interpretability_analysis.material_pattern_miner import (
    mine_material_patterns,
)
from app.modules.interpretability_analysis.material_pattern_validator import (
    validate_material_patterns,
)
from app.modules.interpretability_analysis.material_pattern_ranker import (
    refine_and_rank_material_patterns,
)
# Phase 4: Material Mechanism Mapping
from app.modules.interpretability_analysis.material_mechanism_mapper import (
    map_patterns_to_mechanisms,
)
from app.modules.interpretability_analysis.material_mechanism_scorer import (
    score_material_mechanisms,
)
from app.modules.interpretability_analysis.material_scope_analyzer import (
    analyze_material_scope,
    apply_scope_to_mechanisms,
)
from app.modules.interpretability_analysis.scientific_hypothesis_builder import (
    generate_scientific_hypotheses,
    generate_applicability_boundaries,
    generate_anomaly_patterns,
    build_scientific_insight_report,
)
from app.modules.interpretability_analysis.confidence_scorer import (
    score_all_hypotheses,
)
from app.modules.interpretability_analysis.llm_scientific_insight_prompt_builder import (
    build_llm_scientific_insight_prompt,
)
from app.modules.interpretability_analysis.llm_scientific_insight_parser import (
    parse_llm_scientific_insights,
)
from app.modules.interpretability_analysis.llm_scientific_insight_validator import (
    validate_llm_scientific_insights,
)

from app.modules.interpretability_analysis.exceptions import (
    InterpretabilityAnalysisNotFoundException,
)
from app.modules.interpretability_analysis.debug_tracker import (
    InterpretabilityDebugTracker,
    determine_final_status,
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
        # 闁冲厜鍋撻柍鍏夊亾 Generate ID and create DB record IMMEDIATELY 闁冲厜鍋撻柍鍏夊亾
        ia_id = f"ia_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        # 闁冲厜鍋撻柍鍏夊亾 Build environment info for debug trace 闁冲厜鍋撻柍鍏夊亾
        env_info = {
            "profile": request.interpretability_profile,
            "max_shap_samples": request.max_shap_samples,
            "llm_enabled": request.use_llm_summarizer,
            "include_shap": request.include_shap,
            "include_permutation": request.include_permutation_importance,
            "include_pdp": request.include_pdp,
            "include_correlation": request.include_correlation,
            "include_residual_analysis": request.include_residual_analysis,
            "include_physics_constraints": request.include_physics_constraints,
            "force_rerun": request.force_rerun,
        }
        tracker = InterpretabilityDebugTracker(run_id=ia_id, environment=env_info)

        # 闁冲厜鍋撻柍鍏夊亾 Create early record (survives even if run crashes) 闁冲厜鍋撻柍鍏夊亾
        record = InterpretabilityAnalysis(
            id=ia_id,
            task_id=task_id,
            status=InterpretabilityAnalysisStatus.ANALYZING,
            analysis_profile=request.interpretability_profile,
            request_json=request.model_dump(),
            current_step="01_build_context",
            started_at=now,
            created_at=now,
            updated_at=now,
        )
        try:
            record = self.repo.create(session, record)
            logger.info("[00/25] Early record created 闁?ia_id=%s", ia_id)
        except Exception as e:
            logger.error("Failed to create early DB record: %s", str(e))
            # Not fatal 闁?fallback to in-memory only tracking
            record = InterpretabilityAnalysis(
                id=ia_id,
                task_id=task_id,
                status=InterpretabilityAnalysisStatus.ANALYZING,
                analysis_profile=request.interpretability_profile,
            )

        warnings_list: list = []

        # Step 1: Build context - gather upstream data
        context = build_interpretability_context(session, task_id)
        warnings_list.extend(context.warnings)
        for w in context.warnings:
            tracker.add_warning("01_build_context", "CONTEXT_WARNING", w)

        # ---- [0/25] Pre-check: early return if cached ----
        if not request.force_rerun:
            existing = self.repo.get_latest_by_task_id(session, task_id)
            if existing and existing.metric_evaluation_id == context.metric_evaluation.id and existing.status in (
                InterpretabilityAnalysisStatus.ANALYZED,
                InterpretabilityAnalysisStatus.ANALYZED_WITH_WARNING,
            ):
                logger.info("[0/25] Returning cached analysis 闁?ia_id=%s", existing.id)
                tracker.mark_cache_hit(cached_from_ia_id=existing.id)
                tracker.apply_to_record(record)
                record.current_step = None
                record.last_completed_step = None
                try:
                    record = self.repo.update(session, record)
                except Exception:
                    pass
                return self.get_interpretability_analysis(session, existing.id)

        logger.info("=== Interpretability Analysis 闁?task=%s ===", task_id)

        # ---- [1/25] Build context ----
        tracker.persist_after_step(session, record)
        logger.info("[1/25] Context built 闁?me=%s pe=%s pg=%s",
                     context.metric_evaluation.id, context.pipeline_execution.id,
                     context.pipeline_generation.id)

        # ---- [2/25] Load interpretability analysis input ----
        ia_input = load_interpretability_analysis_input(context)
        logger.info("[2/25] Input loaded 闁?model=%s predictions=%d",
                     ia_input.model_artifact_path, len(ia_input.prediction_artifact_paths))

        # ---- [3/25] Release DB transaction ----
        logger.info("[3/25] Releasing read transaction ...")
        session.commit()
        logger.info("[3/25] Transaction released")

        # ---- [4/25] Validate paths ----
        logger.info("[4/25] Validating artifact paths ...")
        try:
            with tracker.step("04_validate_paths", "Validate artifact paths",
                              input_summary={"model_path": ia_input.model_artifact_path,
                                            "matrix_path": ia_input.model_ready_matrix_path}):
                _validate_artifact_paths(ia_input.model_artifact_path, ia_input.model_ready_matrix_path)
            logger.info("[4/25] Done")
        except Exception as e:
            logger.error("[4/25] FAILED 闁?%s", str(e))
            tracker.apply_to_record(record)
            return _build_failed_response(
                session, record, task_id, request, str(e), warnings_list, tracker,
            )

        # ---- [5/25] Load model artifact ----
        logger.info("[5/25] Loading model artifact ...")
        try:
            with tracker.step("05_load_model_artifact", "Load model artifact",
                              input_summary={"model_path": ia_input.model_artifact_path}):
                model = load_model_artifact(ia_input.model_artifact_path)
                tracker.update_output({"model_type": type(model).__name__})
            logger.info("[5/25] Done 闁?type=%s", type(model).__name__)
        except Exception as e:
            logger.error("[5/25] FAILED 闁?%s", str(e))
            tracker.apply_to_record(record)
            return _build_failed_response(
                session, record, task_id, request, str(e), warnings_list, tracker,
            )

        # ---- [6/25] Load feature matrix ----
        logger.info("[6/25] Loading feature matrix ...")
        try:
            max_samples = request.max_shap_samples if request.interpretability_profile != "full" else None
            fc_input = list(ia_input.feature_columns) if ia_input.feature_columns else None

            with tracker.step("06_load_feature_matrix", "Load feature matrix",
                              input_summary={"matrix_path": ia_input.model_ready_matrix_path,
                                            "max_samples": max_samples}):
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
                tracker.update_output({"shape": list(X.shape), "n_features": len(feature_columns)})
            logger.info("[6/25] Done 闁?shape=%s features=%d", X.shape, len(feature_columns))
        except Exception as e:
            logger.error("[6/25] FAILED 闁?%s", str(e))
            tracker.apply_to_record(record)
            return _build_failed_response(
                session, record, task_id, request, str(e), warnings_list, tracker,
            )

        # ---- [7/25] Load prediction artifacts ----
        logger.info("[7/25] Loading prediction artifacts ...")
        y_pred = None
        y_true_aligned = None  # y_true from prediction files, row-aligned with y_pred
        prediction_index_source = "none"
        prediction_alignment_info = None
        prediction_alignment_warning = None
        try:
            with tracker.step("07_load_predictions", "Load prediction artifacts",
                              input_summary={"n_prediction_paths": len(ia_input.prediction_artifact_paths)}):
                if ia_input.prediction_artifact_paths:
                    pred_df = load_all_prediction_artifacts(ia_input.prediction_artifact_paths)
                    prediction_index_source = pred_df.attrs.get("index_source", "dataframe_index")
                    pred_cols = ["y_pred", "prediction", "pred", "predicted"]
                    for col in pred_cols:
                        if col in pred_df.columns:
                            y_pred = pred_df[col]
                            break
                    if y_pred is None and len(pred_df.columns) > 0:
                        y_pred = pred_df.iloc[:, 0]
                    if "y_true" in pred_df.columns:
                        y_true_aligned = pred_df["y_true"]
                logger.info("[7/25] Done 闁?%d prediction artifacts loaded",
                             len(ia_input.prediction_artifact_paths))

                # Align predictions with X before downstream code builds masks
                # from X and indexes y_pred/y_true with those masks.
                if y_pred is not None:
                    X, y, y_pred, y_true_aligned, alignment_info = _align_predictions_to_feature_rows(
                        X=X,
                        y=y,
                        y_pred=y_pred,
                        y_true=y_true_aligned,
                        prediction_index_source=prediction_index_source,
                    )
                    prediction_alignment_info = alignment_info
                    if alignment_info.get("aligned"):
                        logger.info(
                            "[7/25] Prediction alignment complete: strategy=%s X %d->%d pred %d->%d common=%d",
                            alignment_info.get("strategy"),
                            alignment_info.get("x_rows_before"),
                            alignment_info.get("x_rows_after"),
                            alignment_info.get("pred_rows_before"),
                            alignment_info.get("pred_rows_after"),
                            alignment_info.get("common_rows"),
                        )
                    else:
                        message = alignment_info.get("warning") or "Prediction alignment failed."
                        logger.warning("[7/25] %s", message)
                        warnings_list.append(message)
                        prediction_alignment_warning = message
            if prediction_alignment_info is not None:
                tracker.update_output({"prediction_alignment": prediction_alignment_info})
            if prediction_alignment_warning:
                tracker.add_warning(
                    "07_load_predictions",
                    "PREDICTION_ALIGNMENT_FAILED",
                    prediction_alignment_warning,
                )
        except Exception as e:
            logger.warning("[7/25] Warning 闁?%s", str(e))
            warnings_list.append(f"Prediction artifact load warning: {str(e)}")
            tracker.add_recoverable_error("07_load_predictions", e)

        # ---- [8/25] Select interpretability methods ----
        logger.info("[8/25] Selecting methods (family=%s profile=%s) ...",
              ia_input.final_model_family, request.interpretability_profile)
        with tracker.step("08_select_methods", "Select interpretability methods",
                          input_summary={"model_family": ia_input.final_model_family,
                                        "profile": request.interpretability_profile}):
            method_plan = select_interpretability_methods(
                model_family=ia_input.final_model_family,
                include_shap=request.include_shap,
                include_permutation=request.include_permutation_importance,
                profile=request.interpretability_profile,
            )
            tracker.update_output({"methods": method_plan.methods_selected,
                                  "explainer": method_plan.shap_explainer_type})
        warnings_list.extend(method_plan.notes)
        for note in method_plan.notes:
            tracker.add_warning("08_select_methods", "METHOD_NOTE", note)
        logger.info("[8/25] Done 闁?methods=%s", method_plan.methods_selected)

        # ---- [9/25] Compute importance (coefficient / native / permutation) ----
        logger.info("[9/25] Computing importance (%s) ...", method_plan.methods_selected)
        all_importance: List[GlobalFeatureImportanceItem] = []
        permutation_results = None
        method_statuses: Dict[str, str] = {}
        per_method_importance: Dict[str, List[Dict[str, Any]]] = {}

        with tracker.step("09_compute_importance", "Compute feature importance",
                          input_summary={"methods": method_plan.methods_selected,
                                        "n_features": len(feature_columns)}):

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
                    tracker.add_warning("09_compute_importance", "COEFFICIENT_FAILED", str(e))

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
                    tracker.add_warning("09_compute_importance", "NATIVE_FAILED", str(e))

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
                    tracker.add_warning("09_compute_importance", "PERMUTATION_FAILED", str(e))

            if not all_importance and method_plan.methods_selected:
                try:
                    logger.info("[9/25] No importance results 闁?using permutation fallback ...")
                    permutation_results = compute_permutation_importance(
                        model, X, y, feature_columns, n_repeats=5
                    )
                    perm_importance = build_global_importance_from_permutation(permutation_results)
                    all_importance.extend(perm_importance)
                    per_method_importance["permutation_importance"] = [fi.model_dump() for fi in perm_importance]
                    method_statuses["permutation_importance"] = InterpretabilityMethodStatus.FALLBACK_USED
                    tracker.add_warning("09_compute_importance", "FALLBACK_USED",
                                       "All primary methods failed; used permutation fallback")
                except Exception as e:
                    logger.error("[9/25] Fallback permutation also failed: %s", str(e))
                    tracker.add_warning("09_compute_importance", "FALLBACK_FAILED", str(e),
                                       severity="error")

            tracker.update_output({"n_importance_items": len(all_importance),
                                  "method_statuses": dict(method_statuses)})

        logger.info("[9/25] Done 闁?%d items", len(all_importance))

        # ---- [10/25] Compute SHAP ----
        shap_summary = None
        shap_values = None
        if "shap" in method_plan.methods_selected:
            logger.info("[10/25] Computing SHAP (explainer=%s) ...",
                        method_plan.shap_explainer_type)
            try:
                with tracker.step("10_compute_shap", "Compute SHAP values",
                                  input_summary={"explainer": method_plan.shap_explainer_type,
                                                "max_samples": request.max_shap_samples,
                                                "n_features": len(feature_columns)}):
                    shap_summary, shap_values, shap_warnings = compute_shap(
                        model=model,
                        X=X,
                        feature_columns=feature_columns,
                        explainer_type=method_plan.shap_explainer_type,
                        max_samples=request.max_shap_samples,
                    )
                    tracker.update_output({"shap_available": shap_summary.shap_available,
                                          "n_top_features": len(shap_summary.top_shap_features)})
                warnings_list.extend(shap_warnings)
                for sw in shap_warnings:
                    tracker.add_warning("10_compute_shap", "SHAP_WARNING", sw)
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
                tracker.add_recoverable_error("10_compute_shap", e)
            logger.info("[10/25] Done 闁?available=%s",
                         shap_summary.shap_available if shap_summary else False)

        # ---- [11/25] Sort and re-rank ----
        logger.info("[11/25] Sorting and ranking features ...")
        with tracker.step("11_sort_rank", "Sort and rank features",
                          input_summary={"n_importance_items": len(all_importance)}):
            lineage_group_map = _build_lineage_group_map(ia_input.feature_lineage) if ia_input.feature_lineage else {}
            all_importance.sort(key=lambda x: x.importance_value, reverse=True)
            for i, fi in enumerate(all_importance, start=1):
                fi.importance_rank = i
                fi.feature_group = classify_feature_group(fi.feature_name, lineage_group_map)

        top_importance = all_importance[:30]

        # Build ranked feature column list from top_importance for downstream
        # analyzers (PDP, systematic error, high-error). This ensures they
        # operate on truly important features, not the first N raw columns.
        ranked_feature_columns = [
            fi.feature_name
            for fi in top_importance
            if fi.feature_name in X.columns
        ]

        # ---- [12/25] Correlation analysis ----
        correlation_analysis = None
        if request.include_correlation:
            logger.info("[12/25] Computing correlation analysis ...")
            try:
                with tracker.step("12_correlation", "Correlation analysis",
                                  input_summary={"n_features": len(feature_columns),
                                                "top_n": request.correlation_top_n_features}):
                    correlation_analysis = compute_correlation_analysis(
                        X=X, y=y, feature_columns=feature_columns,
                        top_n_features=request.correlation_top_n_features,
                    )
            except Exception as e:
                logger.warning("Correlation analysis failed: %s", str(e))
                warnings_list.append(f"Correlation analysis: {str(e)}")
                tracker.add_recoverable_error("12_correlation", e)

        # Step 13: Cross-method consensus
        cross_method_consensus = None
        if request.include_cross_method_consensus and len(per_method_importance) >= 2:
            logger.info("[13/25] Computing cross-method consensus ...")
            try:
                with tracker.step("13_cross_method", "Cross-method consensus",
                                  input_summary={"methods": list(per_method_importance.keys())}):
                    cross_method_consensus = compute_cross_method_consensus(per_method_importance)
            except Exception as e:
                logger.warning("Cross-method consensus failed: %s", str(e))
                warnings_list.append(f"Cross-method consensus: {str(e)}")
                tracker.add_recoverable_error("13_cross_method", e)

        # Step 14: Partial dependence
        partial_dependence = None
        if request.include_pdp:
            logger.info("[14/25] Computing partial dependence ...")
            try:
                with tracker.step("14_pdp", "Partial dependence",
                                  input_summary={"n_features": len(ranked_feature_columns)}):
                    partial_dependence = compute_partial_dependence(
                        model=model, X=X, feature_columns=ranked_feature_columns,
                        top_n_features=request.pdp_top_n_features,
                    )
            except Exception as e:
                logger.warning("Partial dependence failed: %s", str(e))
                warnings_list.append(f"Partial dependence: {str(e)}")
                tracker.add_recoverable_error("14_pdp", e)

        # Step 15: Residual analysis
        residual_analysis = None
        if request.include_residual_analysis and y_true_aligned is not None and y_pred is not None:
            logger.info("[15/25] Computing residual analysis ...")
            try:
                with tracker.step("15_residual", "Residual analysis"):
                    residual_analysis = analyze_residuals(
                        y_true=y_true_aligned, y_pred=y_pred, X=X, feature_columns=feature_columns,
                    )
            except Exception as e:
                logger.warning("Residual analysis failed: %s", str(e))
                warnings_list.append(f"Residual analysis: {str(e)}")
                tracker.add_recoverable_error("15_residual", e)

        # Step 16: Systematic error detection
        systematic_errors = None
        if request.include_residual_analysis and y_true_aligned is not None and y_pred is not None:
            logger.info("[16/25] Detecting systematic errors ...")
            try:
                with tracker.step("16_systematic_error", "Systematic error detection"):
                    systematic_errors = detect_systematic_errors(
                        X=X, y_true=y_true_aligned, y_pred=y_pred, feature_columns=ranked_feature_columns,
                    )
            except Exception as e:
                logger.warning("Systematic error detection failed: %s", str(e))
                warnings_list.append(f"Systematic error detection: {str(e)}")
                tracker.add_recoverable_error("16_systematic_error", e)

        # Step 17: Physics constraint check
        physics_constraints = None
        if request.include_physics_constraints and y_pred is not None:
            logger.info("[17/25] Checking physics constraints ...")
            try:
                with tracker.step("17_physics", "Physics constraint check"):
                    physics_constraints = check_physics_constraints(
                        y_pred=y_pred,
                        target_property=ia_input.target_column,
                        prediction_target_name=ia_input.prediction_target_name,
                    )
            except Exception as e:
                logger.warning("Physics constraint check failed: %s", str(e))
                warnings_list.append(f"Physics constraint check: {str(e)}")
                tracker.add_recoverable_error("17_physics", e)

        # Step 18: SHAP interaction values
        shap_interactions = None
        if "shap" in method_plan.methods_selected and shap_values is not None:
            logger.info("[18/25] Computing SHAP interactions ...")
            try:
                with tracker.step("18_shap_interactions", "SHAP interactions"):
                    shap_interactions = compute_shap_interactions(
                        shap_values=shap_values,
                        feature_columns=feature_columns,
                        top_n=10,
                    )
            except Exception as e:
                logger.warning("SHAP interaction computation failed: %s", str(e))
                warnings_list.append(f"SHAP interactions: {str(e)}")
                tracker.add_recoverable_error("18_shap_interactions", e)

        # Step 19: SHAP dependence data
        shap_dependence = None
        if "shap" in method_plan.methods_selected and shap_values is not None:
            logger.info("[19/25] Computing SHAP dependence ...")
            try:
                with tracker.step("19_shap_dependence", "SHAP dependence"):
                    shap_dependence = compute_shap_dependence(
                        shap_values=shap_values,
                        X=X,
                        feature_columns=feature_columns,
                        top_n=10,
                    )
            except Exception as e:
                logger.warning("SHAP dependence computation failed: %s", str(e))
                warnings_list.append(f"SHAP dependence: {str(e)}")
                tracker.add_recoverable_error("19_shap_dependence", e)

        # Step 20: Local explanations
        _y_true = y_true_aligned if y_true_aligned is not None else y
        _y_pred_arr = np.asarray(y_pred) if y_pred is not None else None
        local_explanations = []
        try:
            logger.info("[20/25] Building local explanations ...")
            with tracker.step("20_local_explanations", "Local explanations",
                              input_summary={"max_explanations": request.max_local_explanations}):
                local_explanations = build_local_explanations(
                    X=X,
                    y_true=_y_true,
                    y_pred=_y_pred_arr,
                    feature_columns=feature_columns,
                    shap_values=shap_values,
                    max_explanations=request.max_local_explanations,
                )
                tracker.update_output({"n_explanations": len(local_explanations)})
        except Exception as e:
            logger.warning("Local explanations failed: %s", str(e))
            warnings_list.append(f"Local explanations: {str(e)}")
            tracker.add_recoverable_error("20_local_explanations", e)

        # Step 21: High-error sample analysis
        high_error_analysis = []
        if request.include_high_error_samples:
            try:
                logger.info("[21/25] Analyzing high-error samples ...")
                with tracker.step("21_high_error", "High-error sample analysis"):
                    high_error_analysis = analyze_high_error_samples(
                        X=X,
                        y_true=y_true_aligned if y_true_aligned is not None else y,
                        y_pred=y_pred,
                        feature_columns=ranked_feature_columns,
                        shap_values=shap_values,
                        max_samples=request.max_local_explanations,
                        shap_feature_columns=feature_columns,
                    )
            except Exception as e:
                logger.warning("High-error analysis failed: %s", str(e))
                warnings_list.append(f"High-error analysis: {str(e)}")
                tracker.add_recoverable_error("21_high_error", e)

        # Step 22: Feature group summary
        try:
            logger.info("[22/25] Building feature group summary ...")
            with tracker.step("22_feature_groups", "Feature group summary"):
                feature_group_summary = build_feature_group_summary(
                    top_importance,
                    feature_lineage=ia_input.feature_lineage,
                )
        except Exception as e:
            logger.warning("Feature group summary failed: %s", str(e))
            warnings_list.append(f"Feature group summary: {str(e)}")
            tracker.add_recoverable_error("22_feature_groups", e)
            feature_group_summary = FeatureGroupSummary()

        # ==== NEW: Scientific Insight Engine ====

        # Step 23a: Evidence Normalization
        logger.info("[23a/25] Building evidence units and feature profiles ...")
        evidence_units: List[Any] = []
        feature_profiles: List[Any] = []
        scientific_report = None  # type: Optional[ScientificInsightReport]

        try:
            with tracker.step("23a_evidence_units", "Evidence normalization"):
                evidence_units = build_evidence_units(
                    per_method_importance=per_method_importance,
                    correlation_analysis=correlation_analysis,
                    partial_dependence=partial_dependence,
                    residual_analysis=residual_analysis,
                    systematic_errors=systematic_errors,
                    physics_constraints=physics_constraints,
                    shap_summary=shap_summary,
                    cross_method_consensus=cross_method_consensus,
                    shap_interactions=shap_interactions,
                    shap_dependence=shap_dependence,
                )
                tracker.update_output({"n_evidence_units": len(evidence_units)})
            if not evidence_units:
                logger.warning("[23a/25] No evidence units produced; check analyzer outputs.")
                tracker.add_warning("23a_evidence_units", "NO_EVIDENCE", "No evidence units produced")
            else:
                logger.info("[23a/25] Built %d evidence units", len(evidence_units))
        except Exception as e:
            logger.error("[23a/25] Evidence normalization FAILED: %s", str(e))
            warnings_list.append(f"Evidence normalization failed: {str(e)}")
            tracker.add_recoverable_error("23a_evidence_units", e)

        # Step 23b: Build feature evidence profiles
        try:
            with tracker.step("23b_feature_profiles", "Feature evidence profiles"):
                if evidence_units:
                    feature_profiles = build_feature_evidence_profiles(
                        evidence_units=evidence_units,
                        feature_columns=feature_columns,
                        correlation_analysis=correlation_analysis,
                        cross_method_consensus=cross_method_consensus,
                        feature_lineage=ia_input.feature_lineage,
                    )
                    tracker.update_output({"n_profiles": len(feature_profiles)})
                    logger.info("[23b/25] Built %d feature evidence profiles", len(feature_profiles))
                else:
                    logger.warning("[23b/25] Skipping feature profiles 闁?no evidence units")
                    tracker.add_warning("23b_feature_profiles", "SKIPPED", "No evidence units available")
        except Exception as e:
            logger.error("[23b/25] Feature profiles FAILED: %s", str(e))
            warnings_list.append(f"Feature profiles failed: {str(e)}")
            tracker.add_recoverable_error("23b_feature_profiles", e)

        # Step 23c: Material Pattern Mining (Phase 1)
        material_patterns: List[Any] = []
        try:
            with tracker.step("23c_pattern_mining", "Material pattern mining"):
                if evidence_units and feature_profiles:
                    material_patterns = mine_material_patterns(
                        X=X,
                        y_true=y_true_aligned if y_true_aligned is not None else y,
                        y_pred=y_pred,
                        feature_profiles=feature_profiles,
                        evidence_units=evidence_units,
                        partial_dependence=partial_dependence,
                        shap_dependence=shap_dependence,
                        shap_interactions=shap_interactions,
                        correlation_analysis=correlation_analysis,
                        high_error_analysis=high_error_analysis if high_error_analysis else None,
                        systematic_errors=systematic_errors,
                        feature_lineage=ia_input.feature_lineage,
                        target_name=ia_input.target_column or "",
                        material_domain=ia_input.material_domain,
                    )
                    tracker.update_output({"n_candidates": len(material_patterns)})
                    logger.info("[23c/25] Material pattern mining complete 闁?%d candidates", len(material_patterns))
                else:
                    logger.warning("[23c/25] Skipping material pattern mining 闁?no evidence/features")
                    tracker.add_warning("23c_pattern_mining", "SKIPPED", "No evidence/features for pattern mining")
        except Exception as e:
            logger.error("[23c/25] Material pattern mining FAILED: %s", str(e))
            warnings_list.append(f"Material pattern mining failed: {str(e)}")
            tracker.add_recoverable_error("23c_pattern_mining", e)

        # Step 23d: Validate + Rank Material Patterns (Phase 3)
        try:
            with tracker.step("23d_pattern_validate", "Pattern validation & ranking"):
                if material_patterns and X is not None and y_pred is not None:
                    material_patterns = validate_material_patterns(
                        patterns=material_patterns,
                        X=X,
                        y_true=y_true_aligned if y_true_aligned is not None else y,
                        y_pred=y_pred,
                        model=model,
                        evidence_units=evidence_units,
                        feature_profiles=feature_profiles,
                        partial_dependence=partial_dependence,
                        shap_dependence=shap_dependence,
                    )
                if material_patterns and feature_profiles:
                    material_patterns = refine_and_rank_material_patterns(
                        patterns=material_patterns,
                        feature_profiles=feature_profiles,
                        evidence_units=evidence_units,
                        max_patterns=10,
                    )
                tracker.update_output({"n_validated": len(material_patterns)})
                logger.info("[23d/25] Pattern validation & ranking complete 闁?%d top patterns",
                           len(material_patterns))
        except Exception as e:
            logger.error("[23d/25] Pattern validation/ranking FAILED: %s", str(e))
            warnings_list.append(f"Pattern validation/ranking failed: {str(e)}")
            tracker.add_recoverable_error("23d_pattern_validate", e)

        # Step 23e: Material Mechanism Mapping (Phase 4)
        material_mechanisms: List[Any] = []
        material_scope_results: List[Dict[str, Any]] = []
        try:
            with tracker.step("23e_mechanisms", "Material mechanism mapping"):
                if material_patterns and feature_profiles:
                    material_mechanisms = map_patterns_to_mechanisms(
                        patterns=material_patterns,
                        feature_lineage=ia_input.feature_lineage,
                        feature_profiles=feature_profiles,
                        evidence_units=evidence_units,
                        material_domain=ia_input.material_domain,
                    )
                    if material_mechanisms:
                        material_mechanisms = score_material_mechanisms(
                            mechanisms=material_mechanisms,
                            source_patterns=material_patterns,
                        )
                    if material_patterns and X is not None:
                        material_scope_results = analyze_material_scope(
                            patterns=material_patterns,
                            X=X,
                            material_metadata=None,
                            feature_lineage=ia_input.feature_lineage,
                        )
                        if material_mechanisms and material_scope_results:
                            material_mechanisms = apply_scope_to_mechanisms(
                                mechanisms=material_mechanisms,
                                scope_results=material_scope_results,
                            )
                tracker.update_output({"n_mechanisms": len(material_mechanisms),
                                      "n_scopes": len(material_scope_results)})
                logger.info("[23e/25] Mechanism mapping complete 闁?%d mechanisms",
                           len(material_mechanisms))
        except Exception as e:
            logger.error("[23e/25] Mechanism mapping FAILED: %s", str(e))
            warnings_list.append(f"Mechanism mapping failed: {str(e)}")
            tracker.add_recoverable_error("23e_mechanisms", e)

        # Step 23f: Scientific Hypothesis Generation
        scientific_hypotheses: List[Any] = []
        boundaries: List[Any] = []
        anomalies: List[Any] = []
        try:
            with tracker.step("23f_hypotheses", "Scientific hypotheses & boundaries"):
                if evidence_units and feature_profiles:
                    scientific_hypotheses = generate_scientific_hypotheses(
                        evidence_units=evidence_units,
                        feature_profiles=feature_profiles,
                        partial_dependence=partial_dependence,
                        correlation_analysis=correlation_analysis,
                        residual_analysis=residual_analysis,
                        systematic_errors=systematic_errors,
                        high_error_analysis=high_error_analysis if high_error_analysis else None,
                        physics_constraints=physics_constraints,
                        shap_interactions=shap_interactions,
                        feature_lineage=ia_input.feature_lineage,
                        sample_size=len(X) if X is not None else 0,
                    )
                boundaries = generate_applicability_boundaries(
                    residual_analysis=residual_analysis,
                    systematic_errors=systematic_errors,
                    high_error_analysis=high_error_analysis if high_error_analysis else None,
                    evidence_units=evidence_units,
                    feature_profiles=feature_profiles,
                )
                anomalies = generate_anomaly_patterns(
                    high_error_analysis=high_error_analysis if high_error_analysis else None,
                    systematic_errors=systematic_errors,
                    evidence_units=evidence_units,
                )
                tracker.update_output({"n_hypotheses": len(scientific_hypotheses),
                                      "n_boundaries": len(boundaries),
                                      "n_anomalies": len(anomalies)})
                logger.info("[23f/25] Generated %d hypotheses, %d boundaries, %d anomalies",
                           len(scientific_hypotheses), len(boundaries), len(anomalies))
        except Exception as e:
            logger.error("[23f/25] Hypothesis generation FAILED: %s", str(e))
            warnings_list.append(f"Hypothesis generation failed: {str(e)}")
            tracker.add_recoverable_error("23f_hypotheses", e)

        # Step 23g: Confidence Scoring + Report Assembly
        try:
            with tracker.step("23g_report", "Confidence scoring & report assembly"):
                if scientific_hypotheses:
                    model_perf = {
                        "primary_metric": ia_input.primary_metric,
                        "primary_metric_value": ia_input.primary_metric_value,
                        "r_squared": residual_analysis.get("r_squared") if residual_analysis else None,
                        "rmse": residual_analysis.get("rmse") if residual_analysis else None,
                    }
                    scientific_hypotheses = score_all_hypotheses(
                        hypotheses=scientific_hypotheses,
                        feature_profiles=feature_profiles,
                        cross_method_consensus=cross_method_consensus,
                        model_performance=model_perf,
                        sample_size=len(X) if X is not None else 0,
                        physics_constraints=physics_constraints,
                        evidence_units=evidence_units,
                    )
                scientific_report = build_scientific_insight_report(
                    hypotheses=scientific_hypotheses,
                    boundaries=boundaries,
                    anomalies=anomalies,
                    physics_constraints=physics_constraints,
                    evidence_units=evidence_units,
                    feature_profiles=feature_profiles,
                    method_statuses=method_statuses,
                    material_patterns=material_patterns,
                    material_mechanisms=material_mechanisms,
                )
                tracker.update_output({"n_exec_insights": len(scientific_report.executive_insights),
                                      "n_ranked": len(scientific_report.ranked_hypotheses)})
                logger.info("[23g/25] Scientific insight report assembled 闁?%d exec_insights, %d ranked",
                           len(scientific_report.executive_insights),
                           len(scientific_report.ranked_hypotheses))
        except Exception as e:
            logger.error("[23g/25] Report assembly FAILED: %s", str(e))
            warnings_list.append(f"Report assembly failed: {str(e)}")
            tracker.add_recoverable_error("23g_report", e)

        # ==== LLM Academic Insight Generation (step 24) ====
        scientific_insight_output = None
        material_insight = None
        llm_raw_request = None
        llm_raw_response = None
        llm_used = False
        llm_confidence = None

        # Source confidence from the evidence-driven scorer, not LLM.
        if scientific_report and scientific_report.executive_insights:
            llm_confidence = scientific_report.executive_insights[0].confidence_label

        if request.use_llm_summarizer and scientific_report:
            logger.info("[24/25] Building LLM academic insight context (evidence-grounded) ...")
            try:
                with tracker.step("24_llm_academic_insights", "LLM academic insight generation"):
                    llm_insight_context = build_llm_scientific_insight_prompt(
                        scientific_report=scientific_report,
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
                        material_domain=ia_input.material_domain,
                        dataset_description=ia_input.dataset_description,
                    )
                    llm_raw_request = llm_insight_context

                    llm_result = self.llm_summarizer.summarize(
                        llm_insight_context["system_prompt"],
                        llm_insight_context["user_message"],
                    )
                    raw_response = llm_result.get("raw_response", "")
                    llm_raw_response = raw_response

                    all_evidence_ids = [eu.evidence_id for eu in evidence_units] if evidence_units else []
                    scientific_insight_output = parse_llm_scientific_insights(
                        raw_response,
                        all_evidence_ids,
                    )
                    validation = validate_llm_scientific_insights(
                        output=scientific_insight_output,
                        raw_response=raw_response,
                        valid_evidence_ids=set(all_evidence_ids),
                    )
                    tracker.update_output({
                        "llm_used": validation["is_valid"] and bool(scientific_insight_output.academic_insights),
                        "n_academic_insights": len(scientific_insight_output.academic_insights),
                        "n_rejected_claims": len(scientific_insight_output.rejected_claims),
                        "n_repaired_claims": len(validation.get("repaired_claim_ids", [])),
                    })

                if validation["is_valid"]:
                    llm_used = bool(scientific_insight_output.academic_insights)
                    material_insight = {
                        "academic_executive_summary": scientific_insight_output.executive_summary,
                        "academic_insights": scientific_insight_output.academic_insights,
                        "rejected_claims": scientific_insight_output.rejected_claims,
                        "missing_evidence": scientific_insight_output.missing_evidence,
                        "human_review_notes": scientific_insight_output.human_review_notes,
                        "top_material_patterns": _material_patterns_from_academic_insights(
                            scientific_insight_output.academic_insights,
                            evidence_units,
                        ),
                        "feature_groups_interpretation": _build_feature_groups_interpretation(feature_group_summary),
                        "domain_hypotheses": [
                            ins.get("claim", "")
                            for ins in scientific_insight_output.academic_insights
                            if ins.get("claim_type") in ("candidate_hypothesis", "mechanism_hypothesis", "design_rule")
                        ][:10],
                        "limitations": [
                            item.get("description", "")
                            for item in scientific_insight_output.limitations_section
                            if item.get("description")
                        ][:5] or scientific_report.limitations[:5],
                        "confidence_level": llm_confidence or _infer_material_insight_confidence(
                            scientific_insight_output.academic_insights
                        ),
                    }
                    logger.info(
                        "[24/25] LLM academic insight generation done: used=%s confidence=%s insights=%d rejected=%d repaired=%d",
                        llm_used,
                        material_insight.get("confidence_level"),
                        len(scientific_insight_output.academic_insights),
                        len(scientific_insight_output.rejected_claims),
                        len(validation.get("repaired_claim_ids", [])),
                    )
                else:
                    logger.warning("LLM academic insight validation failed: %s", validation["issues"])
                    warnings_list.append(
                        f"LLM academic insight validation failed: {'; '.join(validation['issues'])}"
                    )
                    tracker.add_warning(
                        "24_llm_academic_insights",
                        "VALIDATION_FAILED",
                        "; ".join(validation["issues"]),
                    )

            except Exception as e:
                logger.error("LLM academic insight generation failed: %s", str(e))
                warnings_list.append(f"LLM academic insight generation: {str(e)}")
                tracker.add_recoverable_error("24_llm_academic_insights", e)
        elif not scientific_report:
            logger.warning("[24/25] Skipping LLM academic insight generation: no scientific report available")
            tracker.add_warning(
                "24_llm_academic_insights",
                "SKIPPED",
                "No scientific report for LLM context",
            )
        # Fallback: populate material_insight from scientific hypotheses when
        # LLM academic insight generation did not run and patterns are unavailable.
        if material_insight is None and scientific_report and not scientific_report.material_pattern_candidates:
            top = scientific_report.executive_insights[:10] if scientific_report.executive_insights else scientific_report.ranked_hypotheses[:10]
            material_insight = {
                "top_material_patterns": [
                    {
                        "pattern": h.claim[:200] if h.claim else "",
                        "supporting_features": _features_from_evidence_refs(
                            h.supporting_evidence_ids, evidence_units,
                        )[:5],
                        "supporting_evidence_ids": h.supporting_evidence_ids[:5],
                        "possible_material_meaning": f"Confidence: {h.confidence_label} (score={h.confidence_score:.2f})",
                        "evidence_strength": _evidence_strength_from_confidence(h.confidence_label),
                        "caution": h.scope_conditions[0] if h.scope_conditions else "This is a model-based association, not a causal mechanism.",
                    }
                    for h in top
                ],
                "academic_insights": _academic_insights_from_hypotheses(scientific_report, evidence_units),
                "rejected_claims": [],
                "missing_evidence": [],
                "human_review_notes": [],
                "feature_groups_interpretation": _build_feature_groups_interpretation(feature_group_summary),
                "domain_hypotheses": [h.claim for h in scientific_report.ranked_hypotheses[:10] if h.claim_type == "mechanism_hypothesis"],
                "limitations": scientific_report.limitations[:5],
                "confidence_level": scientific_report.executive_insights[0].confidence_label if scientific_report.executive_insights else "medium",
            }

        # When material_pattern_candidates exist, unconditionally derive
        # top_material_patterns from them; LLM academic insights may enrich prose
        # but must not replace structured pattern data.
        if scientific_report and scientific_report.material_pattern_candidates:
            if material_insight is None:
                material_insight = {}
            top_patterns = scientific_report.material_pattern_candidates[:10]
            material_insight["top_material_patterns"] = [
                {
                    "pattern": p.statement[:200] if p.statement else "",
                    "pattern_type": p.pattern_type,
                    "supporting_features": list(dict.fromkeys(
                        c.feature_name for c in p.conditions if c.feature_name
                    ))[:5],
                    "supporting_evidence_ids": p.supporting_evidence_ids[:5],
                    "possible_material_meaning": ", ".join(p.material_concepts) if p.material_concepts else "",
                    "evidence_strength": _evidence_strength_from_confidence(p.confidence_label),
                    "caution": "; ".join(p.limitations[:2]) if p.limitations else "This is a model-based association, not a causal mechanism.",
                    "conditions": [c.model_dump() for c in p.conditions],
                    "predicted_effect": p.predicted_effect.model_dump(),
                    "sample_support": p.sample_support.model_dump() if p.sample_support else None,
                    "validation_status": p.validation_status,
                    "validation_summary": [
                        {
                            "type": vr.validation_type,
                            "status": vr.status,
                            "interpretation": vr.interpretation,
                        }
                        for vr in p.validation_results
                    ],
                    "scientific_score": p.scientific_score.model_dump() if p.scientific_score else None,
                    "scope": p.scope_conditions,
                    "counterexamples": [ce.model_dump() for ce in p.counterexamples],
                    "validation_suggestions": p.validation_suggestions[:3],
                }
                for p in top_patterns
            ]
            if not material_insight.get("academic_insights"):
                material_insight["academic_insights"] = _academic_insights_from_patterns(top_patterns)
            material_insight.setdefault("rejected_claims", [])
            material_insight.setdefault("missing_evidence", [])
            material_insight.setdefault("human_review_notes", [])
            if not material_insight.get("domain_hypotheses"):
                material_insight["domain_hypotheses"] = [
                    p.statement for p in top_patterns if p.pattern_type == "interaction"
                ]
            if not material_insight.get("limitations"):
                material_insight["limitations"] = scientific_report.limitations[:5]
            # Always overwrite with real feature-group data (LLM limitations_section
            # was injected here earlier in Path A; replace with ground-truth groups).
            material_insight["feature_groups_interpretation"] = _build_feature_groups_interpretation(feature_group_summary)
            material_insight["confidence_level"] = top_patterns[0].confidence_label if top_patterns else "medium"
            # Phase 4: Attach mechanism candidates to material_insight
            material_insight["mechanism_candidates"] = [
                {
                    "mechanism_statement": m.mechanism_statement,
                    "mechanism_family": m.mechanism_family,
                    "source_pattern_ids": m.source_pattern_ids,
                    "causal_chain": m.causal_chain,
                    "grounding_level": m.grounding_level,
                    "confidence": m.confidence_label,
                    "limitations": m.limitations,
                    "validation_suggestions": m.validation_suggestions,
                }
                for m in (material_mechanisms or [])
            ]

        # ---- Build properly-typed llm_interpretability_summary ----
        # The old LLMInterpretabilitySummary format (used by the frontend
        # fallback chain) expects top_material_patterns, feature_groups_interpretation,
        # domain_hypotheses, limitations, human_review_notes, and confidence_level.
        # Populate it from the (now-correct) material_insight so the frontend
        # MaterialInsightTab fallback works when material_insight_summary is absent.
        llm_interpretability_summary = {
            "top_material_patterns": material_insight.get("top_material_patterns", []) if material_insight else [],
            "academic_insights": material_insight.get("academic_insights", []) if material_insight else [],
            "rejected_claims": material_insight.get("rejected_claims", []) if material_insight else [],
            "missing_evidence": material_insight.get("missing_evidence", []) if material_insight else [],
            "feature_groups_interpretation": material_insight.get("feature_groups_interpretation", []) if material_insight else [],
            "domain_hypotheses": material_insight.get("domain_hypotheses", []) if material_insight else [],
            "limitations": material_insight.get("limitations", []) if material_insight else [],
            "human_review_notes": material_insight.get("human_review_notes", []) if material_insight else [],
            "confidence_level": material_insight.get("confidence_level", "medium") if material_insight else "medium",
        }

        # ---- Build interpretability risk notes ----
        risk_notes = _build_risk_notes(
            physics_constraints=physics_constraints,
            warnings_list=warnings_list,
            scientific_report=scientific_report,
        )

        # ---- [25/25] Build Final Output Input ----
        logger.info("[25/25] Building final output input ...")
        final_output_input = None
        final_output_failed = False
        try:
            with tracker.step("25_final_output_input", "Build final output input"):
                final_output_input = build_final_output_input(
                    interpretability_analysis_id=ia_id,
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
                    scientific_insight_summary=(
                        scientific_report.model_dump() if scientific_report else None
                    ),
                    interpretability_artifacts={},
                    workflow_trace_refs={},
                )
            ready_for_fo = True
        except Exception as e:
            logger.warning("Final output input build failed: %s", str(e))
            warnings_list.append(f"Final output input: {str(e)}")
            tracker.add_recoverable_error("25_final_output_input", e)
            final_output_failed = True
            ready_for_fo = False

        # Determine status via the tracker
        status = determine_final_status(
            tracker,
            artifact_save_failed=False,
            final_output_failed=final_output_failed,
        )

        # ---- Persist ----
        logger.info("[PERSIST] Updating DB record ...")
        now = datetime.now(timezone.utc)
        finished_at = now
        total_dur = time.time() - tracker._started_at

        # Populate the early-created record with all results
        record.status = status
        record.analysis_profile = request.interpretability_profile
        record.final_model_id = ia_input.final_model_id
        record.final_model_family = ia_input.final_model_family
        record.final_trial_id = ia_input.final_trial_id
        record.methods_used_json={
            "methods": list(method_statuses.keys()),
            "statuses": method_statuses,
        }
        record.global_feature_importance_json={"items": [fi.model_dump() for fi in top_importance]}
        record.permutation_importance_json={
            "items": [pr.model_dump() for pr in permutation_results]
        } if permutation_results else None
        record.shap_summary_json=shap_summary.model_dump() if shap_summary else None
        record.local_explanations_json={"items": [le.model_dump() for le in local_explanations]}
        record.high_error_sample_analysis_json={"items": [he.model_dump() for he in high_error_analysis]}
        record.cross_method_consensus_json=cross_method_consensus
        record.partial_dependence_json=partial_dependence
        record.residual_analysis_json=residual_analysis
        record.correlation_analysis_json=correlation_analysis
        record.physics_constraint_check_json=physics_constraints
        record.feature_group_summary_json = feature_group_summary.model_dump() if feature_group_summary else None
        record.material_insight_summary_json = material_insight
        record.llm_summary_json = llm_interpretability_summary
        record.scientific_insight_report_json = (
            scientific_report.model_dump() if scientific_report else None
        )
        record.final_output_input_json = final_output_input.model_dump() if final_output_input else None
        record.artifact_manifest_json = None
        record.ready_for_final_output = ready_for_fo
        record.llm_used = llm_used
        record.llm_confidence_level = llm_confidence
        record.llm_request_json = llm_raw_request
        record.llm_response_json = {"raw_response": llm_raw_response} if llm_raw_response else None
        record.error_message = None
        record.input_snapshot_json = {
            "model_artifact_path": ia_input.model_artifact_path,
            "matrix_path": ia_input.model_ready_matrix_path,
            "x_shape": list(X.shape) if X is not None else None,
            "feature_count": len(feature_columns),
            "prediction_artifact_count": len(ia_input.prediction_artifact_paths),
            "model_type": type(model).__name__ if model else None,
        }
        record.started_at = record.started_at or now
        record.finished_at = finished_at
        record.duration_seconds = round(total_dur, 2)
        record.updated_at = now

        # Apply debug trace to record
        tracker.apply_to_record(record)

        artifact_save_failed = False
        try:
            record = self.repo.update(session, record)
            logger.info("[PERSIST] DB record updated 闁?ia_id=%s", ia_id)
        except Exception as e:
            logger.error("Failed to persist interpretability analysis: %s", str(e))
            session.rollback()
            raise BusinessException(
                f"Failed to save analysis result to database: {str(e)}",
                "INTERPRETABILITY_PERSIST_FAILED",
            )

        # Save artifacts
        try:
            with tracker.step("99_save_artifacts", "Save interpretability artifacts"):
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
                    llm_interpretability_summary=scientific_insight_output.model_dump() if scientific_insight_output else None,
                    scientific_insight_report=(
                        scientific_report.model_dump() if scientific_report else None
                    ),
                    material_patterns=[mp.model_dump() for mp in material_patterns] if material_patterns else None,
                    material_pattern_validation={
                        "validated_patterns": [mp.model_dump() for mp in material_patterns],
                        "validation_method": "subgroup_contrast/bootstrap/ice_consistency",
                        "warnings": [
                            f"Pattern '{p.pattern_id}' validation failed: {p.validation_status}"
                            for p in material_patterns if p.validation_status == "fail"
                        ],
                    } if material_patterns else None,
                    material_mechanisms=[mm.model_dump() for mm in material_mechanisms] if material_mechanisms else None,
                    final_output_input=final_output_input.model_dump() if final_output_input else None,
                    debug_trace=tracker.to_debug_trace().model_dump(),
                    debug_warnings={"items": [w.model_dump() for w in tracker.get_all_warnings()]},
                    request_snapshot=request.model_dump(),
                    input_snapshot=record.input_snapshot_json,
                )
                record.artifact_manifest_json = artifact_manifest.model_dump()
                record = self.repo.update(session, record)
        except Exception as e:
            logger.warning("Artifact save failed: %s", str(e))
            warnings_list.append(f"Artifact save: {str(e)}")
            tracker.add_recoverable_error("99_save_artifacts", e)
            artifact_save_failed = True

        # Re-determine status after artifact save
        if artifact_save_failed:
            record.status = determine_final_status(
                tracker,
                artifact_save_failed=True,
                final_output_failed=final_output_failed,
            )
            tracker.apply_to_record(record)
            try:
                record = self.repo.update(session, record)
            except Exception:
                pass

        total_dur = time.time() - tracker._started_at
        record.duration_seconds = round(total_dur, 2)
        logger.info("[DONE] ia_id=%s status=%s features=%d methods=%s | TOTAL %.1fs",
                     ia_id, record.status, len(top_importance),
                     list(method_statuses.keys()), total_dur)
        return build_response(record=record, warnings=warnings_list, tracker=tracker, risk_notes=risk_notes)

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
    record: InterpretabilityAnalysis,
    task_id: str,
    request: InterpretabilityAnalysisCreateRequest,
    error_message: str,
    warnings_list: list,
    tracker: "InterpretabilityDebugTracker",
) -> InterpretabilityAnalysisResponse:
    from app.modules.interpretability_analysis.debug_tracker import determine_final_status

    now = datetime.now(timezone.utc)
    finished_at = now

    tracker.apply_to_record(record)
    record.status = InterpretabilityAnalysisStatus.FAILED
    record.error_message = error_message
    record.finished_at = finished_at
    record.duration_seconds = round(time.time() - tracker._started_at, 2) if tracker._started_at else None
    record.updated_at = now

    repo = InterpretabilityAnalysisRepository()
    try:
        record = repo.update(session, record)
    except Exception:
        # If update fails (e.g. record was not persisted early), create instead
        record = repo.create(session, record)

    return build_response(record=record, warnings=warnings_list, tracker=tracker)


def _build_feature_groups_interpretation(feature_group_summary):
    """Map the computed feature_group_summary to the frontend's
    FeatureGroupInterpretation format: [{feature_group, summary}, ...].

    Args:
        feature_group_summary: FeatureGroupSummary from step 22, or None.
    Returns:
        List[dict] with keys 'feature_group' and 'summary'.
    """
    if feature_group_summary is None:
        return []
    groups = getattr(feature_group_summary, "feature_groups", {}) or {}
    if not groups:
        return []

    group_labels = {
        "composition_descriptor": "Composition-based features dominate the predictive behavior.",
        "structure_descriptor": "Structure-based features contribute to the predictions.",
        "elemental_descriptor": "Elemental property features play a role in model behavior.",
        "statistical_descriptor": "Statistical descriptor features provide supplementary contributions.",
        "derived_feature": "Derived features from feature engineering have notable influence.",
        "other": "Unclassified features contribute to model predictions.",
    }

    result = []
    for group_name, group_data in sorted(
        groups.items(), key=lambda x: x[1].get("total_importance", 0), reverse=True
    ):
        top_features = group_data.get("top_features", [])[:3]
        summary = (
            f"{group_data.get('feature_count', 0)} features, "
            f"total importance {group_data.get('total_importance', 0):.3f}, "
            f"top: {', '.join(top_features) if top_features else 'none'}"
        )
        label = group_labels.get(group_name, f"{group_name} features contribute to the model.")
        result.append({
            "feature_group": group_name,
            "summary": f"{label} {summary}",
        })
    return result


def _build_risk_notes(
    physics_constraints=None,
    warnings_list=None,
    scientific_report=None,
):
    """Build interpretability_risk_notes from physics constraints, warnings,
    and the scientific insight report.

    Returns:
        List[dict] with keys 'risk_type', 'description', 'severity'.
    """
    notes = []

    # Risk from physics constraint violations
    if isinstance(physics_constraints, dict):
        checks = physics_constraints.get("checks", [])
        if isinstance(checks, list):
            for check in checks:
                if isinstance(check, dict) and not check.get("passed", True):
                    notes.append({
                        "risk_type": "physics_constraint_violation",
                        "description": (
                            f"Physics constraint '{check.get('constraint', '?')}' "
                            f"({check.get('severity', 'warning')}) violated: "
                            f"{check.get('detail', check.get('message', 'no detail'))}"
                        ),
                        "severity": check.get("severity", "warning"),
                    })

    # Risk from warnings
    for w in (warnings_list or []):
        if "failed" in str(w).lower() or "error" in str(w).lower():
            severity = "error"
        else:
            severity = "warning"
        notes.append({
            "risk_type": "analysis_warning",
            "description": str(w)[:500],
            "severity": severity,
        })

    # Risk from report-level limitations
    if scientific_report and getattr(scientific_report, "limitations", None):
        for lim in scientific_report.limitations[:5]:
            notes.append({
                "risk_type": "model_limitation",
                "description": str(lim)[:500],
                "severity": "warning",
            })

    return notes


def _material_patterns_from_academic_insights(academic_insights, evidence_units):
    """Compatibility projection from academic insights to old material-pattern cards."""
    patterns = []
    for insight in (academic_insights or [])[:10]:
        refs = _ensure_list(insight.get("supporting_evidence_ids"))
        patterns.append({
            "pattern": str(insight.get("claim", ""))[:200],
            "supporting_features": _features_from_evidence_refs(refs, evidence_units)[:5],
            "supporting_evidence_ids": refs[:5],
            "possible_material_meaning": insight.get("material_meaning") or _first_evidence_chain_summary(insight),
            "evidence_strength": _normalize_evidence_strength(insight.get("evidence_strength")),
            "caution": _join_risks(insight.get("counterexamples_or_risks")) or insight.get("allowed_wording", "This is a model-supported candidate hypothesis, not a causal conclusion."),
            "claim_type": insight.get("claim_type", "candidate_hypothesis"),
            "validation_status": insight.get("validation_status", "model_supported_only"),
            "falsifiable_prediction": insight.get("falsifiable_prediction", ""),
            "suggested_validation": _ensure_list(insight.get("suggested_validation"))[:3],
            "scope": _ensure_list(insight.get("scope_conditions")),
        })
    return patterns


def _academic_insights_from_hypotheses(scientific_report, evidence_units):
    """Fallback academic insights when LLM is unavailable and no patterns exist."""
    if not scientific_report:
        return []
    top = scientific_report.executive_insights[:10] if scientific_report.executive_insights else scientific_report.ranked_hypotheses[:10]
    insights = []
    for index, hypothesis in enumerate(top):
        refs = hypothesis.supporting_evidence_ids or []
        insights.append({
            "claim_id": hypothesis.hypothesis_id or f"fallback_hypothesis_{index + 1}",
            "claim_type": _map_hypothesis_claim_type(hypothesis.claim_type),
            "claim": hypothesis.claim,
            "material_meaning": "Evidence-grounded model association translated from the scientific hypothesis engine.",
            "supporting_evidence_ids": refs,
            "evidence_chain": [
                {"step": "model_evidence", "summary": f"Supported by {len(refs)} evidence unit(s): {', '.join(refs[:5])}."},
                {"step": "hypothesis", "summary": hypothesis.hypothesis_pattern or "The claim is retained as a falsifiable candidate hypothesis."},
            ],
            "evidence_strength": _evidence_strength_from_confidence(hypothesis.confidence_label),
            "confidence": _normalize_confidence(hypothesis.confidence_label),
            "validation_status": "model_supported_only",
            "falsifiable_prediction": "Evaluate the same association on an independent holdout, external dataset, or targeted simulation/experiment.",
            "suggested_validation": hypothesis.validation_suggestions[:3] if hypothesis.validation_suggestions else [
                "external holdout test",
                "bootstrap or subgroup contrast",
                "domain-specific DFT/MD/experimental validation if actionable",
            ],
            "counterexamples_or_risks": hypothesis.scope_conditions[:3] if hypothesis.scope_conditions else ["Model evidence alone does not establish causality."],
            "scope_conditions": hypothesis.scope_conditions,
            "allowed_wording": "model-supported candidate hypothesis",
        })
    return insights


def _academic_insights_from_patterns(patterns):
    """Fallback academic insights from validated deterministic material patterns."""
    insights = []
    for index, pattern in enumerate(patterns or []):
        validation_status = _validation_status_from_pattern(pattern)
        claim_type = "applicability_boundary" if pattern.pattern_type == "boundary" else "candidate_hypothesis"
        if pattern.pattern_type == "interaction":
            claim_type = "mechanism_hypothesis"
        insights.append({
            "claim_id": pattern.pattern_id or f"pattern_insight_{index + 1}",
            "claim_type": claim_type,
            "claim": pattern.statement,
            "material_meaning": ", ".join(pattern.material_concepts) if pattern.material_concepts else "Descriptor-grounded material association.",
            "supporting_evidence_ids": pattern.supporting_evidence_ids,
            "evidence_chain": [
                {"step": "pattern_mining", "summary": f"Deterministic pattern miner identified a {pattern.pattern_type} pattern."},
                {"step": "validation", "summary": f"Pattern validation status is {pattern.validation_status}."},
            ],
            "evidence_strength": _evidence_strength_from_confidence(pattern.confidence_label),
            "confidence": _normalize_confidence(pattern.confidence_label),
            "validation_status": validation_status,
            "falsifiable_prediction": _prediction_from_pattern(pattern),
            "suggested_validation": pattern.validation_suggestions[:3] if pattern.validation_suggestions else [
                "external holdout test",
                "subgroup contrast or bootstrap validation",
                "domain-specific simulation or experiment if the rule is actionable",
            ],
            "counterexamples_or_risks": _pattern_risks(pattern),
            "scope_conditions": pattern.scope_conditions,
            "allowed_wording": "model-supported candidate hypothesis" if validation_status == "model_supported_only" else "statistically supported candidate hypothesis",
        })
    return insights


def _infer_material_insight_confidence(academic_insights):
    order = {"low": 0, "medium": 1, "high": 2}
    best = "medium"
    for insight in academic_insights or []:
        confidence = _normalize_confidence(insight.get("confidence"))
        if order[confidence] > order[best]:
            best = confidence
    return best


def _normalize_confidence(value):
    value = str(value or "").lower()
    if value in {"high", "strong", "very_high"}:
        return "high"
    if value in {"low", "weak", "very_low"}:
        return "low"
    return "medium"


def _normalize_evidence_strength(value):
    value = str(value or "").lower()
    if value in {"strong", "high", "very_high"}:
        return "strong"
    if value in {"weak", "low", "very_low"}:
        return "weak"
    return "moderate"


def _evidence_strength_from_confidence(confidence):
    confidence = _normalize_confidence(confidence)
    if confidence == "high":
        return "strong"
    if confidence == "low":
        return "weak"
    return "moderate"


def _validation_status_from_pattern(pattern):
    if getattr(pattern, "validation_status", "") == "pass":
        return "statistically_supported"
    if getattr(pattern, "validation_status", "") == "fail":
        return "insufficient_evidence"
    if getattr(pattern, "validation_results", None):
        return "statistically_supported"
    return "model_supported_only"


def _map_hypothesis_claim_type(claim_type):
    if claim_type == "mechanism_hypothesis":
        return "mechanism_hypothesis"
    if claim_type == "limitation":
        return "applicability_boundary"
    if claim_type == "anomaly":
        return "applicability_boundary"
    return "candidate_hypothesis"


def _first_evidence_chain_summary(insight):
    chain = insight.get("evidence_chain", []) or []
    if chain and isinstance(chain[0], dict):
        return chain[0].get("summary", "")
    return ""


def _ensure_list(value):
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _join_risks(risks):
    if not risks:
        return ""
    return "; ".join(str(risk) for risk in risks[:2])


def _prediction_from_pattern(pattern):
    effect = getattr(pattern, "predicted_effect", None)
    if effect and getattr(effect, "target_direction", None):
        return f"Materials satisfying this pattern should show target response that {effect.target_direction} within the stated scope."
    return "Evaluate whether materials satisfying this pattern differ from out-of-scope samples on an independent holdout set."


def _pattern_risks(pattern):
    risks = list(getattr(pattern, "limitations", []) or [])[:3]
    for counterexample in getattr(pattern, "counterexamples", []) or []:
        if getattr(counterexample, "description", None):
            risks.append(counterexample.description)
    if not risks:
        risks.append("Model-derived association; independent validation is still required.")
    return risks[:5]

def _features_from_evidence_refs(evidence_ids, evidence_units):
    """Map evidence IDs to their actual feature names.

    Returns deduplicated, ordered list of feature names referenced by the
    given evidence IDs.  Used so that top_material_patterns don't leak
    raw evidence IDs as "supporting_features".
    """
    features = []
    id_set = set(evidence_ids or [])
    for eu in evidence_units or []:
        if eu.evidence_id in id_set:
            features.extend(eu.feature_names)
    return list(dict.fromkeys([f for f in features if f]))


def _align_predictions_to_feature_rows(
    X,
    y,
    y_pred,
    y_true,
    prediction_index_source: str,
):
    """Return row-aligned X/y/y_pred/y_true plus diagnostic metadata."""
    info = {
        "aligned": False,
        "strategy": "none",
        "index_source": prediction_index_source,
        "x_rows_before": len(X) if X is not None else 0,
        "pred_rows_before": len(y_pred) if y_pred is not None else 0,
        "x_rows_after": len(X) if X is not None else 0,
        "pred_rows_after": len(y_pred) if y_pred is not None else 0,
        "common_rows": 0,
    }

    if X is None or y_pred is None:
        info["warning"] = "Prediction alignment skipped because X or y_pred is missing."
        return X, y, None, None, info

    if prediction_index_source == "sample_id":
        aligned = _align_by_prediction_index(X, y, y_pred, y_true)
        if aligned is not None:
            X2, y2, yp2, yt2, common_rows, strategy = aligned
            info.update({
                "aligned": True,
                "strategy": strategy,
                "x_rows_after": len(X2),
                "pred_rows_after": len(yp2),
                "common_rows": common_rows,
            })
            return X2, y2, yp2, yt2, info

    if len(y_pred) == len(X):
        yp2 = _series_with_index(y_pred, X.index)
        yt2 = _series_with_index(y_true, X.index) if y_true is not None and len(y_true) == len(X) else None
        info.update({
            "aligned": True,
            "strategy": "positional",
            "x_rows_after": len(X),
            "pred_rows_after": len(yp2),
            "common_rows": len(X),
        })
        return X, y, yp2, yt2, info

    info["warning"] = (
        "Prediction alignment failed: X rows="
        f"{len(X)}, y_pred rows={len(y_pred)}, index_source={prediction_index_source}. "
        "Prediction-dependent interpretability steps will be skipped."
    )
    return X, y, None, None, info


def _align_by_prediction_index(X, y, y_pred, y_true):
    pred_index = getattr(y_pred, "index", None)
    if pred_index is None or not hasattr(X, "index"):
        return None

    pred_labels = set(pred_index)
    common = [label for label in X.index if label in pred_labels]
    if common:
        X2 = X.loc[common]
        y2 = y.loc[common] if y is not None and hasattr(y, "loc") else y
        yp2 = y_pred.loc[common]
        yt2 = y_true.loc[common] if y_true is not None and hasattr(y_true, "loc") else None
        return X2, y2, yp2, yt2, len(common), "sample_id"

    # Some parquet readers round-trip integer ids as strings. Retry with
    # string-normalized labels while preserving X row order.
    pred_by_key = {str(label): label for label in pred_index}
    x_by_key = {str(label): label for label in X.index}
    common_keys = [str(label) for label in X.index if str(label) in pred_by_key]
    if not common_keys:
        return None

    x_labels = [x_by_key[key] for key in common_keys]
    pred_lookup_labels = [pred_by_key[key] for key in common_keys]
    X2 = X.loc[x_labels]
    y2 = y.loc[x_labels] if y is not None and hasattr(y, "loc") else y
    yp2 = y_pred.loc[pred_lookup_labels]
    yp2.index = X2.index
    yt2 = None
    if y_true is not None and hasattr(y_true, "loc"):
        yt2 = y_true.loc[pred_lookup_labels]
        yt2.index = X2.index
    return X2, y2, yp2, yt2, len(common_keys), "sample_id_string"


def _series_with_index(values, index):
    if values is None:
        return None
    if isinstance(values, pd.Series) and values.index.equals(index):
        return values
    arr = np.asarray(values).reshape(-1)
    return pd.Series(arr, index=index)


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
