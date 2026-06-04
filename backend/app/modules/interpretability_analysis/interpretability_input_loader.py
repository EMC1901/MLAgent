import logging
from typing import List

from app.modules.interpretability_analysis.schemas import InterpretabilityAnalysisInput
from app.modules.interpretability_analysis.exceptions import InterpretabilityInputInvalidException

logger = logging.getLogger(__name__)


def load_interpretability_analysis_input(context) -> InterpretabilityAnalysisInput:
    """
    Extract interpretability analysis input from upstream context records.

    Args:
        context: InterpretabilityContext from context_builder.

    Returns:
        InterpretabilityAnalysisInput with all fields populated from upstream data.
    """
    me = context.metric_evaluation
    pe = context.pipeline_execution
    pg = context.pipeline_generation
    fp = context.feature_preprocessing
    itd = context.iteration_decision
    ti = context.task_interpretation
    ts = context.task_specification

    # --- Model artifact paths from PipelineExecution ---
    model_artifact_path = None
    prediction_artifact_paths: List[str] = []
    best_trial_id = me.best_trial_id

    if pe and pe.execution_json:
        exec_json = pe.execution_json or {}
        # Look up the best trial's artifacts
        for trial in exec_json.get("trial_results", []):
            if isinstance(trial, dict) and trial.get("trial_id") == best_trial_id:
                model_paths = trial.get("model_artifact_paths") or trial.get("model_artifact_path")
                if isinstance(model_paths, list) and model_paths:
                    model_artifact_path = model_paths[0]
                elif isinstance(model_paths, str):
                    model_artifact_path = model_paths

                pred_paths = trial.get("prediction_artifact_paths") or trial.get("prediction_artifact_path")
                if isinstance(pred_paths, list):
                    prediction_artifact_paths = pred_paths
                elif isinstance(pred_paths, str) and pred_paths:
                    prediction_artifact_paths = [pred_paths]
                break

        # Fallback: look in pipeline_run_results
        if not model_artifact_path:
            for pr in exec_json.get("pipeline_run_results", []):
                if isinstance(pr, dict) and pr.get("best_trial_id") == best_trial_id:
                    model_paths = pr.get("model_artifact_paths", [])
                    if model_paths:
                        model_artifact_path = model_paths[0]
                    pred_paths = pr.get("prediction_artifact_paths", [])
                    if pred_paths:
                        prediction_artifact_paths = pred_paths
                    break

        # Fallback: use training_artifact_dir
        if not model_artifact_path and pe.training_artifact_dir:
            import os
            candidate = os.path.join(pe.training_artifact_dir, "model.pkl")
            if os.path.exists(candidate):
                model_artifact_path = candidate

        # Check metric_evaluation_input_json for prediction artifacts
        mei = pe.metric_evaluation_input_json or {}
        if not prediction_artifact_paths:
            pred_artifacts = mei.get("prediction_artifacts", [])
            if pred_artifacts:
                prediction_artifact_paths = pred_artifacts

    if not model_artifact_path:
        logger.warning(
            "No model artifact path found for best_trial_id=%s in PipelineExecution %s",
            best_trial_id, pe.id if pe else None,
        )

    logger.info("model_artifact_path=%s predictions=%d", model_artifact_path, len(prediction_artifact_paths))

    # --- Feature matrix path and feature columns ---
    model_ready_matrix_path = None
    feature_columns: List[str] = []
    preprocessor_artifact_path = None

    if fp:
        model_ready_matrix_path = fp.model_ready_artifact_path
        preprocessor_artifact_path = fp.preprocessor_artifact_path

    if pg:
        pipeline_json = pg.pipeline_json or {}
        if not model_ready_matrix_path:
            model_ready_matrix_path = pipeline_json.get("model_ready_matrix_path")
        if not feature_columns:
            feature_columns = pipeline_json.get("feature_columns", [])
        if not preprocessor_artifact_path:
            preprocessor_artifact_path = pipeline_json.get("preprocessor_artifact_path")

        # Also check execution_input_json
        exec_input = pg.execution_input_json or {}
        if not feature_columns:
            feature_columns = exec_input.get("feature_columns", [])
        if not model_ready_matrix_path:
            model_ready_matrix_path = exec_input.get("model_ready_matrix_path")

    # --- Model metadata from MetricEvaluation ---
    final_model_family = ""
    model_ranking = []
    if me.model_ranking_json:
        model_ranking = me.model_ranking_json if isinstance(me.model_ranking_json, list) else []
        # Find the entry matching best_model_id
        for mr in model_ranking:
            if isinstance(mr, dict) and mr.get("model_id") == me.best_model_id:
                final_model_family = mr.get("model_family", "")
                break

    # Fallback: derive family from model_id
    if not final_model_family and me.best_model_id:
        # Try PipelineGeneration pipeline_specs
        if pg and pg.pipeline_json:
            for spec in pg.pipeline_json.get("pipeline_specs", []):
                if isinstance(spec, dict) and spec.get("model_id") == me.best_model_id:
                    final_model_family = spec.get("model_family", "")
                    break

    # --- Material domain from TaskInterpretation ---
    material_domain = None
    if ti:
        material_domain = ti.interpreted_material_domain

    # --- Dataset description from TaskSpecification ---
    dataset_description = None
    prediction_target_name = None
    if ts:
        dataset_description = ts.dataset_description
        prediction_target_name = ts.prediction_target

    # --- Stop rationale from IterationDecision ---
    stop_rationale = None
    if itd and itd.stop_rationale_json:
        stop_rationale = itd.stop_rationale_json

    # --- Feature lineage from FeaturePreprocessing ---
    feature_lineage = {}
    if fp and fp.feature_lineage_json:
        feature_lineage = fp.feature_lineage_json

    # --- Metric summary from MetricEvaluation ---
    metric_summary = me.metric_summary_json or {}

    return InterpretabilityAnalysisInput(
        model_artifact_path=model_artifact_path,
        model_ready_matrix_path=model_ready_matrix_path,
        prediction_artifact_paths=prediction_artifact_paths,
        preprocessor_artifact_path=preprocessor_artifact_path,
        task_id=context.task_id,
        task_type=me.task_type,
        target_column=me.target_column,
        primary_metric=me.primary_metric,
        primary_metric_value=me.best_primary_metric_value,
        metric_direction=me.metric_direction,
        final_model_id=me.best_model_id,
        final_model_family=final_model_family,
        final_trial_id=me.best_trial_id,
        feature_columns=feature_columns,
        feature_lineage=feature_lineage,
        material_domain=material_domain,
        dataset_description=dataset_description,
        prediction_target_name=prediction_target_name,
        stop_rationale=stop_rationale,
        metric_evaluation_id=me.id,
        pipeline_execution_id=pe.id if pe else (me.pipeline_execution_id),
        pipeline_generation_id=pg.id if pg else (me.pipeline_generation_id),
        selection_reason_summary=_build_selection_reason_summary(me, itd),
        model_ranking=model_ranking,
        metric_summary=metric_summary,
    )


def _build_selection_reason_summary(me, itd) -> str:
    """Build a concise selection reason summary from available data."""
    parts = []
    if me.best_model_id:
        parts.append(f"Model: {me.best_model_id}")
    if me.best_primary_metric_value is not None and me.primary_metric:
        parts.append(f"{me.primary_metric}: {me.best_primary_metric_value:.4f}")
    if itd and itd.stop_rationale_json:
        sr = itd.stop_rationale_json
        if isinstance(sr, dict):
            reason = sr.get("primary_reason") or sr.get("best_result_summary", "")
            if reason:
                parts.append(f"Stop reason: {reason}")
    if not parts:
        parts.append("Best model selected by primary metric.")
    return " | ".join(parts)
