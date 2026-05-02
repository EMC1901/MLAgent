from sqlmodel import Session
from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.task_interpretation.repository import TaskInterpretationRepository
from app.modules.dataset_profile.repository import DatasetProfileRepository
from app.modules.workflow_planning.repository import WorkflowPlanRepository
from app.modules.feature_engineering.exceptions import (
    FeatureEngineeringUpstreamNotReadyException,
    FeatureStrategyMissingException,
)


def build_feature_engineering_context(session: Session, task_id: str) -> dict:
    task_repo = TaskSpecificationRepository()
    interp_repo = TaskInterpretationRepository()
    profile_repo = DatasetProfileRepository()
    plan_repo = WorkflowPlanRepository()

    # 1. Task Specification
    task_spec = task_repo.get_by_id(session, task_id)
    if not task_spec:
        raise FeatureEngineeringUpstreamNotReadyException(
            f"Task specification with id {task_id} not found.",
            "TASK_NOT_FOUND",
        )
    if task_spec.status not in ("valid", "valid_with_warning"):
        raise FeatureEngineeringUpstreamNotReadyException(
            f"Task {task_id} status is '{task_spec.status}'. "
            "Only 'valid' or 'valid_with_warning' tasks can proceed.",
            "TASK_NOT_READY",
        )

    # 2. Task Interpretation
    interp = interp_repo.get_latest_by_task_id(session, task_id)
    if not interp:
        raise FeatureEngineeringUpstreamNotReadyException(
            f"No interpretation found for task {task_id}.",
            "INTERPRETATION_NOT_READY",
        )
    if interp.status not in ("interpreted", "interpreted_with_warning"):
        raise FeatureEngineeringUpstreamNotReadyException(
            f"Interpretation for task {task_id} status is '{interp.status}'.",
            "INTERPRETATION_NOT_READY",
        )

    # 3. Dataset Profile
    profile = profile_repo.get_latest_by_task_id(session, task_id)
    if not profile:
        raise FeatureEngineeringUpstreamNotReadyException(
            f"No dataset profile found for task {task_id}.",
            "DATASET_PROFILE_NOT_READY",
        )
    if profile.status not in ("profiled", "profiled_with_warning"):
        raise FeatureEngineeringUpstreamNotReadyException(
            f"Dataset profile for task {task_id} status is '{profile.status}'.",
            "DATASET_PROFILE_NOT_READY",
        )
    if not profile.is_usable_for_ml:
        raise FeatureEngineeringUpstreamNotReadyException(
            f"Dataset for task {task_id} is not usable for ML.",
            "DATASET_NOT_USABLE_FOR_ML",
        )

    # 4. Workflow Plan
    plan = plan_repo.get_latest_by_task_id(session, task_id)
    if not plan:
        raise FeatureEngineeringUpstreamNotReadyException(
            f"No workflow plan found for task {task_id}.",
            "WORKFLOW_PLAN_NOT_READY",
        )
    if plan.status not in ("planned", "planned_with_warning"):
        raise FeatureEngineeringUpstreamNotReadyException(
            f"Workflow plan for task {task_id} status is '{plan.status}'.",
            "WORKFLOW_PLAN_NOT_READY",
        )

    plan_json = plan.plan_json or {}
    feature_strategy = plan_json.get("feature_strategy")
    if not feature_strategy:
        raise FeatureStrategyMissingException(
            "Feature strategy is missing in the workflow plan."
        )

    interp_json = interp.interpretation_json or {}
    profile_json = profile.profile_json or {}
    task_spec_json = task_spec.task_spec_json or {}

    context = {
        "task_id": task_id,
        "interpretation_id": interp.id,
        "dataset_profile_id": profile.id,
        "workflow_plan_id": plan.id,
        "task_context": {
            "task_type": task_spec.task_type,
            "target_column": task_spec.target_column,
            "evaluation_metric": task_spec.evaluation_metric,
            "input_type": task_spec.input_type,
            "user_priority": task_spec_json.get("user_priority", []),
            "constraints": task_spec_json.get("constraints", []),
        },
        "interpretation_context": {
            "interpreted_task_type": interp.interpreted_task_type,
            "interpreted_input_modality": interp.interpreted_input_modality,
            "interpreted_material_domain": interp.interpreted_material_domain,
            "warnings": interp_json.get("warnings", []),
        },
        "data_context": {
            "dataset_source": profile_json.get("dataset_source"),
            "dataset_schema": profile_json.get("dataset_schema"),
            "input_columns": profile_json.get("dataset_schema", {}).get("input_columns", []),
            "target_column": profile.target_column,
            "input_modality": profile.input_modality,
            "is_usable_for_ml": profile.is_usable_for_ml,
            "workflow_planning_input": profile_json.get("workflow_planning_input"),
        },
        "feature_context": {
            "feature_strategy": feature_strategy,
            "feature_type": feature_strategy.get("feature_type"),
            "recommended_featurizers": feature_strategy.get("recommended_featurizers", []),
            "feature_scaling_required": feature_strategy.get("feature_scaling_required", False),
            "feature_selection_required": feature_strategy.get("feature_selection_required", False),
        },
    }

    return context
