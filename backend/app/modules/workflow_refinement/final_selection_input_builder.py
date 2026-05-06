import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def build_final_selection_input(
    wr_id: str,
    task_id: str,
    decision: str,
    llm_fpsi: Optional[Dict[str, Any]],
    best_me_id: Optional[str] = None,
    best_model_id: Optional[str] = None,
    best_trial_id: Optional[str] = None,
    best_pipeline_spec_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the FinalPipelineSelectionInput for downstream consumption."""

    if decision != "proceed_next_stage" and not llm_fpsi:
        return {
            "workflow_refinement_id": wr_id,
            "task_id": task_id,
            "decision": decision,
            "candidate_metric_evaluation_ids": [],
            "candidate_pipeline_execution_ids": [],
            "best_metric_evaluation_id": best_me_id,
            "current_best_model_id": best_model_id,
            "current_best_trial_id": best_trial_id,
            "current_best_pipeline_spec_id": best_pipeline_spec_id,
            "selection_policy": {},
            "constraints": {},
            "ready_for_final_pipeline_selection": False,
        }

    if llm_fpsi:
        return {
            "workflow_refinement_id": wr_id,
            "task_id": task_id,
            "decision": decision,
            "candidate_metric_evaluation_ids": llm_fpsi.get("candidate_metric_evaluation_ids") or [],
            "candidate_pipeline_execution_ids": llm_fpsi.get("candidate_pipeline_execution_ids") or [],
            "best_metric_evaluation_id": llm_fpsi.get("best_metric_evaluation_id") or best_me_id,
            "current_best_model_id": llm_fpsi.get("current_best_model_id") or best_model_id,
            "current_best_trial_id": llm_fpsi.get("current_best_trial_id") or best_trial_id,
            "current_best_pipeline_spec_id": llm_fpsi.get("current_best_pipeline_spec_id") or best_pipeline_spec_id,
            "selection_policy": llm_fpsi.get("selection_policy") or {},
            "constraints": llm_fpsi.get("constraints") or {},
            "ready_for_final_pipeline_selection": llm_fpsi.get(
                "ready_for_final_pipeline_selection",
                decision == "proceed_next_stage",
            ),
        }

    return {
        "workflow_refinement_id": wr_id,
        "task_id": task_id,
        "decision": decision,
        "candidate_metric_evaluation_ids": [],
        "candidate_pipeline_execution_ids": [],
        "best_metric_evaluation_id": best_me_id,
        "current_best_model_id": best_model_id,
        "current_best_trial_id": best_trial_id,
        "current_best_pipeline_spec_id": best_pipeline_spec_id,
        "selection_policy": {},
        "constraints": {},
        "ready_for_final_pipeline_selection": decision == "proceed_next_stage",
    }
