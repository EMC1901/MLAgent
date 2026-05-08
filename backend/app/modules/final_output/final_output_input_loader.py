import logging
from typing import Dict, Any

from app.modules.interpretability_analysis.model import InterpretabilityAnalysis
from app.modules.final_output.exceptions import FinalOutputInputInvalidException

logger = logging.getLogger(__name__)


class FinalOutputInput:
    def __init__(self, data: Dict[str, Any]):
        self.interpretability_analysis_id: str = data.get("interpretability_analysis_id", "")
        self.final_pipeline_selection_id: str = data.get("final_pipeline_selection_id", "")
        self.task_id: str = data.get("task_id", "")
        self.final_model_id: str = data.get("final_model_id", "")
        self.final_trial_id: str = data.get("final_trial_id", "")
        self.model_artifact_path: str = data.get("model_artifact_path", "")
        self.prediction_artifact_paths: list = data.get("prediction_artifact_paths", [])
        self.metric_summary: Dict[str, Any] = data.get("metric_summary", {})
        self.selection_summary: Dict[str, Any] = data.get("selection_summary", {})
        self.global_feature_importance: list = data.get("global_feature_importance", [])
        self.shap_summary: Dict[str, Any] = data.get("shap_summary") or {}
        self.material_insight_summary: Dict[str, Any] = data.get("material_insight_summary") or {}
        self.interpretability_artifacts: Dict[str, str] = data.get("interpretability_artifacts", {})
        self.workflow_trace_refs: Dict[str, str] = data.get("workflow_trace_refs", {})
        self.ready_for_final_output: bool = data.get("ready_for_final_output", False)


def load_final_output_input(ia: InterpretabilityAnalysis) -> FinalOutputInput:
    data = ia.final_output_input_json or {}

    if not data:
        raise FinalOutputInputInvalidException(
            "InterpretabilityAnalysis.final_output_input_json is empty."
        )

    fo_input = FinalOutputInput(data)

    if not fo_input.ready_for_final_output:
        raise FinalOutputInputInvalidException(
            "final_output_input_json.ready_for_final_output is not true."
        )

    if not fo_input.final_model_id:
        raise FinalOutputInputInvalidException("final_model_id is missing.")

    if not fo_input.model_artifact_path:
        raise FinalOutputInputInvalidException("model_artifact_path is missing.")

    logger.info(
        "Loaded final output input: model=%s trial=%s",
        fo_input.final_model_id,
        fo_input.final_trial_id,
    )
    return fo_input
