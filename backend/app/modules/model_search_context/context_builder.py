from sqlmodel import Session
from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.task_interpretation.repository import TaskInterpretationRepository
from app.modules.dataset_profile.repository import DatasetProfileRepository
from app.modules.workflow_planning.repository import WorkflowPlanRepository
from app.modules.feature_engineering.repository import FeatureEngineeringRepository
from app.modules.feature_preprocessing.repository import FeaturePreprocessingRepository
from app.modules.model_search_context.exceptions import UpstreamNotReadyException


def build_model_search_context(session: Session, task_id: str) -> dict:
    task_repo = TaskSpecificationRepository()
    interp_repo = TaskInterpretationRepository()
    profile_repo = DatasetProfileRepository()
    plan_repo = WorkflowPlanRepository()
    fe_repo = FeatureEngineeringRepository()
    fmp_repo = FeaturePreprocessingRepository()

    # 1. Task Specification
    task_spec = task_repo.get_by_id(session, task_id)
    if not task_spec:
        raise UpstreamNotReadyException(
            f"Task specification with id {task_id} not found.", "TASK_NOT_FOUND"
        )
    if task_spec.status not in ("valid", "valid_with_warning"):
        raise UpstreamNotReadyException(
            f"Task {task_id} status is '{task_spec.status}'. "
            "Only 'valid' or 'valid_with_warning' tasks can proceed.",
            "TASK_NOT_READY",
        )

    # 2. Task Interpretation
    interp = interp_repo.get_latest_by_task_id(session, task_id)
    if not interp:
        raise UpstreamNotReadyException(
            f"No interpretation found for task {task_id}.", "INTERPRETATION_NOT_READY"
        )
    if interp.status not in ("interpreted", "interpreted_with_warning"):
        raise UpstreamNotReadyException(
            f"Interpretation for task {task_id} status is '{interp.status}'.",
            "INTERPRETATION_NOT_READY",
        )

    # 3. Dataset Profile
    profile = profile_repo.get_latest_by_task_id(session, task_id)
    if not profile:
        raise UpstreamNotReadyException(
            f"No dataset profile found for task {task_id}.", "DATASET_PROFILE_NOT_READY"
        )
    if profile.status not in ("profiled", "profiled_with_warning"):
        raise UpstreamNotReadyException(
            f"Dataset profile for task {task_id} status is '{profile.status}'.",
            "DATASET_PROFILE_NOT_READY",
        )

    # 4. Workflow Plan
    plan = plan_repo.get_latest_by_task_id(session, task_id)
    if not plan:
        raise UpstreamNotReadyException(
            f"No workflow plan found for task {task_id}.", "WORKFLOW_PLAN_NOT_READY"
        )
    if plan.status not in ("planned", "planned_with_warning"):
        raise UpstreamNotReadyException(
            f"Workflow plan for task {task_id} status is '{plan.status}'.",
            "WORKFLOW_PLAN_NOT_READY",
        )

    # 5. Feature Engineering
    fe = fe_repo.get_latest_by_task_id(session, task_id)
    if not fe:
        raise UpstreamNotReadyException(
            f"No feature engineering found for task {task_id}.", "FEATURE_ENGINEERING_NOT_READY"
        )
    if fe.status not in ("completed", "completed_with_warning"):
        raise UpstreamNotReadyException(
            f"Feature engineering for task {task_id} status is '{fe.status}'. "
            "Expected 'completed' or 'completed_with_warning'.",
            "FEATURE_ENGINEERING_NOT_READY",
        )

    # 6. Feature Preprocessing
    fmp = fmp_repo.get_latest_by_task_id(session, task_id)
    if not fmp:
        raise UpstreamNotReadyException(
            f"No feature preprocessing found for task {task_id}.", "FEATURE_PREPROCESSING_NOT_READY"
        )
    if fmp.status not in ("preprocessed", "preprocessed_with_warning", "success"):
        raise UpstreamNotReadyException(
            f"Feature preprocessing for task {task_id} status is '{fmp.status}'. "
            "Expected 'preprocessed' or 'preprocessed_with_warning'.",
            "FEATURE_PREPROCESSING_NOT_READY",
        )
    if not fmp.is_ready_for_model_search:
        raise UpstreamNotReadyException(
            f"Feature preprocessing for task {task_id} is not ready for model search.",
            "NOT_READY_FOR_MODEL_SEARCH",
        )

    task_spec_json = task_spec.task_spec_json or {}
    interp_json = interp.interpretation_json or {}
    plan_json = plan.plan_json or {}
    fe_json = fe.feature_json or {}
    fmp_json = fmp.preprocessing_json or {}

    target_column = (
        fmp.target_column
        or fe.target_column
        or task_spec.target_column
    )

    context = {
        "task_id": task_id,
        "interpretation_id": interp.id,
        "dataset_profile_id": profile.id,
        "workflow_plan_id": plan.id,
        "feature_engineering_id": fe.id,
        "feature_preprocessing_id": fmp.id,
        "task_context": {
            "task_type": task_spec.task_type,
            "target_column": target_column,
            "primary_metric": task_spec.evaluation_metric,
            "user_priority": task_spec_json.get("user_priority", []),
        },
        "plan_context": {
            "plan_json": plan_json,
            "model_strategy": plan_json.get("model_strategy", {}),
            "validation_strategy": plan_json.get("validation_strategy", {}),
            "evaluation_strategy": plan_json.get("evaluation_strategy", {}),
            "hpo_strategy": plan_json.get("hpo_strategy", {}),
            "interpretability_strategy": plan_json.get("interpretability_strategy", {}),
            "iteration_guidance": plan_json.get("iteration_guidance", {}),
        },
        "feature_engineering_context": {
            "feature_engineering_id": fe.id,
            "artifact_path": fe.artifact_path,
            "feature_json": fe_json,
            "n_samples": fe.n_samples,
            "n_features": fe.n_features,
        },
        "feature_preprocessing_context": {
            "preprocessing_id": fmp.id,
            "preprocessing_json": fmp_json,
            "model_ready_artifact_path": fmp.model_ready_artifact_path,
            "preprocessor_artifact_id": fmp.preprocessor_artifact_id,
            "n_samples": fmp.n_samples,
            "n_raw_features": fmp.n_raw_features,
            "n_final_features": fmp.n_final_features,
            "target_column": fmp.target_column,
            "is_ready_for_model_search": fmp.is_ready_for_model_search,
        },
    }

    return context
