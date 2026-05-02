import uuid
from datetime import datetime
from typing import Dict, Any
from app.modules.workflow_planning.enums import WorkflowPlanStatus


def build_workflow_plan(
    task_id: str,
    interpretation_id: str,
    dataset_profile_id: str,
    validated_plan: Dict[str, Any],
    llm_request: Dict[str, Any],
    llm_response: Dict[str, Any],
    status: str = WorkflowPlanStatus.PLANNED,
) -> Dict[str, Any]:
    plan_id = f"plan_{uuid.uuid4().hex[:8]}"
    now = datetime.now()

    plan_dict = {
        "workflow_plan_id": plan_id,
        "task_id": task_id,
        "interpretation_id": interpretation_id,
        "dataset_profile_id": dataset_profile_id,
        "status": status,
        "planning_mode": "llm_guided",
        "task_summary": validated_plan.get("task_summary", {}),
        "data_strategy": validated_plan.get("data_strategy", {}),
        "feature_strategy": validated_plan.get("feature_strategy", {}),
        "model_strategy": validated_plan.get("model_strategy", {}),
        "validation_strategy": validated_plan.get("validation_strategy", {}),
        "evaluation_strategy": validated_plan.get("evaluation_strategy", {}),
        "hpo_strategy": validated_plan.get("hpo_strategy", {}),
        "interpretability_strategy": validated_plan.get("interpretability_strategy", {}),
        "pipeline_generation_input": validated_plan.get("pipeline_generation_input", {}),
        "planning_warnings": validated_plan.get("planning_warnings", []),
        "planning_assumptions": validated_plan.get("planning_assumptions", []),
        "llm_reasoning_summary": validated_plan.get("llm_reasoning_summary", ""),
        "confidence_score": validated_plan.get("confidence_score"),
        "llm_request": llm_request,
        "llm_response": llm_response,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    return plan_dict
