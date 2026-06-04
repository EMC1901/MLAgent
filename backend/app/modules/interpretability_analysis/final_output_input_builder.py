import logging
from typing import List, Dict, Any, Optional

from app.modules.interpretability_analysis.schemas import FinalOutputInput
from app.modules.interpretability_analysis.exceptions import FinalOutputInputBuildException

logger = logging.getLogger(__name__)


def build_final_output_input(
    interpretability_analysis_id: str,
    task_id: str,
    final_model_id: str,
    final_trial_id: str,
    model_artifact_path: str,
    prediction_artifact_paths: List[str],
    metric_summary: Dict[str, Any],
    selection_summary: Dict[str, Any],
    global_feature_importance: List[Dict[str, Any]],
    shap_summary: Optional[Dict[str, Any]] = None,
    material_insight_summary: Optional[Dict[str, Any]] = None,
    interpretability_artifacts: Optional[Dict[str, str]] = None,
    workflow_trace_refs: Optional[Dict[str, str]] = None,
) -> FinalOutputInput:
    ready = bool(
        global_feature_importance
        and model_artifact_path
        and metric_summary
        and selection_summary
    )

    if not ready:
        missing = []
        if not global_feature_importance:
            missing.append("global_feature_importance")
        if not model_artifact_path:
            missing.append("model_artifact_path")
        if not metric_summary:
            missing.append("metric_summary")
        if not selection_summary:
            missing.append("selection_summary")
        raise FinalOutputInputBuildException(
            f"Cannot build FinalOutputInput: missing {', '.join(missing)}"
        )

    logger.info("Built FinalOutputInput for interpretability analysis %s", interpretability_analysis_id)
    return FinalOutputInput(
        interpretability_analysis_id=interpretability_analysis_id,
        task_id=task_id,
        final_model_id=final_model_id,
        final_trial_id=final_trial_id,
        model_artifact_path=model_artifact_path,
        prediction_artifact_paths=prediction_artifact_paths,
        metric_summary=metric_summary,
        selection_summary=selection_summary,
        global_feature_importance=global_feature_importance,
        shap_summary=shap_summary,
        material_insight_summary=material_insight_summary,
        interpretability_artifacts=interpretability_artifacts or {},
        workflow_trace_refs=workflow_trace_refs or {},
        ready_for_final_output=ready,
    )
