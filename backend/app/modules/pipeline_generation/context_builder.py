import logging
from sqlmodel import Session
from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.model_search.repository import ModelSearchPlanRepository
from app.modules.feature_preprocessing.repository import FeaturePreprocessingRepository
from app.shared.registry.model_registry import get_all_model_families, is_valid_model_family, get_model_spec
from app.shared.registry.hpo_registry import get_all_hpo_methods, is_valid_hpo_method
from app.modules.pipeline_generation.exceptions import (
    ModelSearchPlanRequiredException,
    ModelSearchPlanNotReadyException,
    PipelineGenerationInputMissingException,
)

logger = logging.getLogger(__name__)


def build_pipeline_generation_context(session: Session, task_id: str) -> dict:
    """Read upstream context: ModelSearchPlan, FeaturePreprocessing, Registries.
    Returns dict with all required inputs for pipeline generation.
    """
    task_repo = TaskSpecificationRepository()
    plan_repo = ModelSearchPlanRepository()
    fpp_repo = FeaturePreprocessingRepository()

    task_spec = task_repo.get_by_id(session, task_id)
    if not task_spec:
        from app.shared.common.exceptions import NotFoundException
        raise NotFoundException(f"Task specification with id {task_id} not found.")

    model_search_plan = plan_repo.get_latest_by_task_id(session, task_id)
    if not model_search_plan:
        raise ModelSearchPlanRequiredException(
            f"No model search plan found for task {task_id}."
        )

    if model_search_plan.status not in ("planned", "planned_with_warning"):
        raise ModelSearchPlanNotReadyException(
            f"Model search plan status is '{model_search_plan.status}', need 'planned' or 'planned_with_warning'."
        )

    if not model_search_plan.ready_for_pipeline_generation:
        raise ModelSearchPlanNotReadyException(
            "Model search plan ready_for_pipeline_generation is false."
        )

    plan_json = model_search_plan.plan_json or {}
    pg_input = plan_json.get("pipeline_generation_input") or {}

    if not pg_input:
        raise PipelineGenerationInputMissingException(
            "pipeline_generation_input is missing from model search plan."
        )

    feature_preprocessing = None
    fpp_id = model_search_plan.feature_preprocessing_id
    if fpp_id:
        feature_preprocessing = fpp_repo.get_by_id(session, fpp_id)

    model_ready_matrix_path = pg_input.get("model_ready_matrix_path") or (
        feature_preprocessing.model_ready_artifact_path if feature_preprocessing else None
    )
    preprocessor_artifact_path = pg_input.get("preprocessor_artifact_path") or (
        feature_preprocessing.preprocessor_artifact_path if feature_preprocessing else None
    )

    task_type = model_search_plan.task_type or "regression"
    primary_metric = model_search_plan.primary_metric or "MAE"

    allowed_model_families = get_all_model_families()
    allowed_hpo_methods = get_all_hpo_methods()

    return {
        "task_id": task_id,
        "model_search_plan_id": model_search_plan.id,
        "feature_preprocessing_id": fpp_id,
        "task_type": task_type,
        "primary_metric": primary_metric,
        "target_column": model_search_plan.target_column or pg_input.get("target_column"),
        "feature_columns": pg_input.get("feature_columns", []),
        "n_samples": model_search_plan.n_samples or 0,
        "n_features": model_search_plan.n_features or 0,
        "model_ready_matrix_path": model_ready_matrix_path,
        "preprocessor_artifact_path": preprocessor_artifact_path,
        "candidate_model_plan": pg_input.get("candidate_model_plan", {}),
        "hpo_plan": pg_input.get("hpo_plan", {}),
        "search_space_plan": pg_input.get("search_space_plan", {}),
        "validation_plan": pg_input.get("validation_plan", {}),
        "evaluation_plan": pg_input.get("evaluation_plan", {}),
        "allowed_model_families": allowed_model_families,
        "allowed_hpo_methods": allowed_hpo_methods,
        "pipeline_generation_input": pg_input,
        "plan_json": plan_json,
        "model_search_plan": model_search_plan,
        "feature_preprocessing": feature_preprocessing,
    }
