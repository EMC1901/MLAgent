import uuid
from datetime import datetime
from typing import Dict, Any
from app.modules.workflow_planning.enums import WorkflowPlanStatus
from app.shared.registry.fe_capability_registry import get_registry_snapshot


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

    # Registry snapshot
    registry_snapshot = get_registry_snapshot()

    # Feature strategy from validated plan
    feature_strategy = validated_plan.get("feature_strategy", {})

    plan_dict = {
        "workflow_plan_id": plan_id,
        "task_id": task_id,
        "interpretation_id": interpretation_id,
        "dataset_profile_id": dataset_profile_id,
        "status": status,
        "planning_mode": "llm_guided",
        "task_summary": validated_plan.get("task_summary", {}),
        "data_strategy": validated_plan.get("data_strategy", {}),
        "feature_strategy": {
            # Legacy fields
            "feature_type": feature_strategy.get("feature_type"),
            "executable_featurizers": feature_strategy.get("executable_featurizers", []),
            "semantic_featurizers": feature_strategy.get("semantic_featurizers", []),
            "unsupported_future_featurizers": feature_strategy.get("unsupported_future_featurizers", []),
            "recommended_featurizers": feature_strategy.get("recommended_featurizers", []),
            "requires_structure_features": feature_strategy.get("requires_structure_features", False),
            "feature_selection_required": feature_strategy.get("feature_selection_required", False),
            "feature_scaling_required": feature_strategy.get("feature_scaling_required", False),
            # New capability-aware fields
            "strategy_id": feature_strategy.get("strategy_id", f"fs_{plan_id}"),
            "strategy_version": feature_strategy.get("strategy_version", "1.0.0"),
            "input_modality_assessment": feature_strategy.get("input_modality_assessment"),
            "selected_feature_actions": feature_strategy.get("selected_feature_actions", []),
            "rejected_feature_actions": feature_strategy.get("rejected_feature_actions", []),
            "fallback_strategy": feature_strategy.get("fallback_strategy"),
            "feature_group_expectations": feature_strategy.get("feature_group_expectations", []),
        },
        "preprocessing_intent": validated_plan.get("preprocessing_intent", {}),
        "model_strategy": validated_plan.get("model_strategy", {}),
        "validation_strategy": validated_plan.get("validation_strategy", {}),
        "evaluation_strategy": validated_plan.get("evaluation_strategy", {}),
        "hpo_strategy": validated_plan.get("hpo_strategy", {}),
        "interpretability_strategy": validated_plan.get("interpretability_strategy", {}),
        "pipeline_generation_input": validated_plan.get("pipeline_generation_input", {}),
        "workflow_rationale": validated_plan.get("workflow_rationale", {}),
        "execution_hints": validated_plan.get("execution_hints"),
        "fe_registry_snapshot_version": registry_snapshot["snapshot_version"],
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
