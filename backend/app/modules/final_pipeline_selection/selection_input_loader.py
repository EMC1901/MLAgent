import logging
from typing import Dict, Any, List

from app.modules.workflow_refinement.model import WorkflowRefinement
from app.modules.final_pipeline_selection.exceptions import FinalSelectionInputInvalidException

logger = logging.getLogger(__name__)


class FinalPipelineSelectionInput:
    def __init__(self, data: Dict[str, Any]):
        self.candidate_metric_evaluation_ids: List[str] = data.get(
            "candidate_metric_evaluation_ids", []
        )
        self.candidate_pipeline_execution_ids: List[str] = data.get(
            "candidate_pipeline_execution_ids", []
        )
        self.current_best_model_id: str = data.get("current_best_model_id") or ""
        self.current_best_trial_id: str = data.get("current_best_trial_id") or ""
        self.current_best_pipeline_spec_id: str = data.get("current_best_pipeline_spec_id") or ""
        self.selection_policy: Dict[str, Any] = data.get("selection_policy") or {}
        self.constraints: Dict[str, Any] = data.get("constraints") or {}
        self.best_metric_evaluation_id: str = data.get("best_metric_evaluation_id") or ""


def load_final_pipeline_selection_input(wr: WorkflowRefinement) -> FinalPipelineSelectionInput:
    data = wr.final_pipeline_selection_input_json or {}
    input_obj = FinalPipelineSelectionInput(data)

    if not input_obj.candidate_metric_evaluation_ids:
        raise FinalSelectionInputInvalidException(
            "candidate_metric_evaluation_ids is missing or empty."
        )
    if not input_obj.candidate_pipeline_execution_ids:
        raise FinalSelectionInputInvalidException(
            "candidate_pipeline_execution_ids is missing or empty."
        )
    if not input_obj.current_best_model_id:
        raise FinalSelectionInputInvalidException(
            "current_best_model_id is missing."
        )
    if not input_obj.current_best_trial_id:
        raise FinalSelectionInputInvalidException(
            "current_best_trial_id is missing."
        )
    if not input_obj.current_best_pipeline_spec_id:
        raise FinalSelectionInputInvalidException(
            "current_best_pipeline_spec_id is missing."
        )

    logger.info(
        "Loaded final selection input: %d metric evals, %d pipeline execs",
        len(input_obj.candidate_metric_evaluation_ids),
        len(input_obj.candidate_pipeline_execution_ids),
    )
    return input_obj
