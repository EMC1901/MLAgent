import logging
from sqlmodel import Session
from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.task_interpretation.repository import TaskInterpretationRepository
from app.modules.dataset_profile.repository import DatasetProfileRepository
from app.modules.workflow_planning.repository import WorkflowPlanRepository
from app.modules.feature_engineering.repository import FeatureEngineeringRepository
from app.modules.feature_preprocessing.exceptions import (
    FeaturePreprocessingUpstreamNotReadyException,
)

logger = logging.getLogger(__name__)


def build_preprocessing_context(session: Session, task_id: str) -> dict:
    task_repo = TaskSpecificationRepository()
    interp_repo = TaskInterpretationRepository()
    profile_repo = DatasetProfileRepository()
    plan_repo = WorkflowPlanRepository()
    fe_repo = FeatureEngineeringRepository()

    logger.debug("building context for task_id=%s", task_id)

    # 1. Task Specification
    logger.debug("checking task specification ...")
    task_spec = task_repo.get_by_id(session, task_id)
    if not task_spec:
        raise FeaturePreprocessingUpstreamNotReadyException(
            f"Task specification with id {task_id} not found.",
            "TASK_NOT_FOUND",
        )
    if task_spec.status not in ("valid", "valid_with_warning"):
        raise FeaturePreprocessingUpstreamNotReadyException(
            f"Task {task_id} status is '{task_spec.status}'. "
            "Only 'valid' or 'valid_with_warning' tasks can proceed.",
            "TASK_NOT_READY",
        )
    logger.debug("task spec OK — status=%s task_type=%s", task_spec.status, task_spec.task_type)

    # 2. Task Interpretation
    logger.debug("checking task interpretation ...")
    interp = interp_repo.get_latest_by_task_id(session, task_id)
    if not interp:
        raise FeaturePreprocessingUpstreamNotReadyException(
            f"No interpretation found for task {task_id}.",
            "INTERPRETATION_NOT_READY",
        )
    if interp.status not in ("interpreted", "interpreted_with_warning"):
        raise FeaturePreprocessingUpstreamNotReadyException(
            f"Interpretation for task {task_id} status is '{interp.status}'.",
            "INTERPRETATION_NOT_READY",
        )
    logger.debug("interpretation OK — status=%s modality=%s", interp.status, interp.interpreted_input_modality)

    # 3. Dataset Profile
    logger.debug("checking dataset profile ...")
    profile = profile_repo.get_latest_by_task_id(session, task_id)
    if not profile:
        raise FeaturePreprocessingUpstreamNotReadyException(
            f"No dataset profile found for task {task_id}.",
            "DATASET_PROFILE_NOT_READY",
        )
    if profile.status not in ("profiled", "profiled_with_warning"):
        raise FeaturePreprocessingUpstreamNotReadyException(
            f"Dataset profile for task {task_id} status is '{profile.status}'.",
            "DATASET_PROFILE_NOT_READY",
        )
    logger.debug("dataset profile OK — status=%s", profile.status)

    # 4. Workflow Plan
    logger.debug("checking workflow plan ...")
    plan = plan_repo.get_latest_by_task_id(session, task_id)
    if not plan:
        raise FeaturePreprocessingUpstreamNotReadyException(
            f"No workflow plan found for task {task_id}.",
            "WORKFLOW_PLAN_NOT_READY",
        )
    if plan.status not in ("planned", "planned_with_warning"):
        raise FeaturePreprocessingUpstreamNotReadyException(
            f"Workflow plan for task {task_id} status is '{plan.status}'.",
            "WORKFLOW_PLAN_NOT_READY",
        )
    logger.debug("workflow plan OK — status=%s", plan.status)

    # 5. Feature Engineering
    logger.debug("checking feature engineering ...")
    fe = fe_repo.get_latest_by_task_id(session, task_id)
    if not fe:
        raise FeaturePreprocessingUpstreamNotReadyException(
            f"No feature engineering found for task {task_id}.",
            "FEATURE_ENGINEERING_REQUIRED",
        )
    if fe.status not in ("completed", "completed_with_warning"):
        raise FeaturePreprocessingUpstreamNotReadyException(
            f"Feature engineering for task {task_id} status is '{fe.status}'.",
            "FEATURE_ENGINEERING_NOT_READY",
        )
    if not fe.artifact_path:
        raise FeaturePreprocessingUpstreamNotReadyException(
            f"Feature engineering for task {task_id} has no artifact path.",
            "FEATURE_ARTIFACT_MISSING",
        )
    logger.debug("feature engineering OK — status=%s artifact_path=%s n_features=%s",
          fe.status, fe.artifact_path, fe.n_features)

    fe_json = fe.feature_json or {}
    plan_json = plan.plan_json or {}
    interp_json = interp.interpretation_json or {}
    task_spec_json = task_spec.task_spec_json or {}

    # Extract target column
    target_column = (
        fe.target_column
        or fe_json.get("feature_matrix", {}).get("target_column")
        or task_spec.target_column
    )

    context = {
        "task_id": task_id,
        "interpretation_id": interp.id,
        "dataset_profile_id": profile.id,
        "workflow_plan_id": plan.id,
        "feature_engineering_id": fe.id,
        "task_context": {
            "task_type": task_spec.task_type,
            "target_column": target_column,
            "primary_metric": task_spec.evaluation_metric,
            "user_priority": task_spec_json.get("user_priority", []),
            "constraints": task_spec_json.get("constraints", []),
        },
        "interpretation_context": {
            "interpreted_task_type": interp.interpreted_task_type,
            "interpreted_input_modality": interp.interpreted_input_modality,
        },
        "data_context": {
            "target_column": target_column,
            "input_modality": profile.input_modality,
        },
        "plan_context": {
            "model_strategy": plan_json.get("model_strategy", {}),
            "validation_strategy": plan_json.get("validation_strategy", {}),
            "evaluation_strategy": plan_json.get("evaluation_strategy", {}),
            "hpo_strategy": plan_json.get("hpo_strategy", {}),
            "interpretability_strategy": plan_json.get("interpretability_strategy", {}),
            "feature_strategy": plan_json.get("feature_strategy", {}),
        },
        "feature_engineering_context": {
            "feature_engineering_id": fe.id,
            "artifact_id": fe.artifact_id,
            "artifact_path": fe.artifact_path,
            "feature_json": fe_json,
            "n_samples": fe.n_samples,
            "n_features": fe.n_features,
        },
    }

    logger.debug("context built successfully — task_type=%s target=%s n_samples=%s n_features=%s",
          context["task_context"]["task_type"],
          context["task_context"]["target_column"],
          context["feature_engineering_context"]["n_samples"],
          context["feature_engineering_context"]["n_features"])

    return context
