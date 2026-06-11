import logging
from sqlmodel import Session
from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.model_search_context.repository import ModelSearchContextRepository
from app.modules.feature_preprocessing.repository import FeaturePreprocessingRepository
from app.shared.registry.model_registry import get_all_model_families, is_valid_model_family, get_model_spec
from app.shared.registry.hpo_registry import get_all_hpo_methods, is_valid_hpo_method
from app.modules.pipeline_generation.exceptions import (
    ModelSearchContextRequiredException,
    ModelSearchContextNotReadyException,
    PipelineGenerationInputMissingException,
)

logger = logging.getLogger(__name__)


def build_pipeline_generation_context(session: Session, task_id: str) -> dict:
    """Read upstream context: ModelSearchContext, FeaturePreprocessing, Registries.
    Returns dict with all required inputs for pipeline generation.
    """
    task_repo = TaskSpecificationRepository()
    msc_repo = ModelSearchContextRepository()
    fpp_repo = FeaturePreprocessingRepository()

    task_spec = task_repo.get_by_id(session, task_id)
    if not task_spec:
        from app.shared.common.exceptions import NotFoundException
        raise NotFoundException(f"Task specification with id {task_id} not found.")

    msc = msc_repo.get_latest_by_task_id(session, task_id)
    if not msc:
        raise ModelSearchContextRequiredException(
            f"No model search context found for task {task_id}."
        )

    if msc.status not in ("updated", "updated_with_warning"):
        raise ModelSearchContextNotReadyException(
            f"Model search context status is '{msc.status}', need 'updated' or 'updated_with_warning'."
        )

    if not msc.ready_for_pipeline_generation:
        raise ModelSearchContextNotReadyException(
            "Model search context ready_for_pipeline_generation is false."
        )

    context_json = msc.context_json or {}
    pg_input = context_json.get("pipeline_generation_input") or {}

    if not pg_input:
        raise PipelineGenerationInputMissingException(
            "pipeline_generation_input is missing from model search context."
        )

    # Diagnostic: log what was read from DB for search space
    ss_from_db = pg_input.get("search_space_plan", {})
    cm_from_db = pg_input.get("candidate_model_plan", {})
    ss_model_ids = [s.get("model_id") for s in ss_from_db.get("spaces", [])]
    cm_model_ids = [c.get("model_id") for c in cm_from_db.get("candidate_models", [])]
    logger.info(
        "PG context read from DB: search_space model_ids=%s | candidate model_ids=%s",
        ss_model_ids, cm_model_ids,
    )
    if set(ss_model_ids) != set(cm_model_ids):
        logger.warning(
            "PG context DB MISMATCH: search_space=%s candidates=%s (diff: space_only=%s cand_only=%s)",
            ss_model_ids, cm_model_ids,
            set(ss_model_ids) - set(cm_model_ids),
            set(cm_model_ids) - set(ss_model_ids),
        )

    feature_preprocessing = None
    fpp_id = msc.feature_preprocessing_id
    if fpp_id:
        feature_preprocessing = fpp_repo.get_by_id(session, fpp_id)

    model_ready_matrix_path = pg_input.get("model_ready_matrix_path") or (
        feature_preprocessing.model_ready_artifact_path if feature_preprocessing else None
    )
    preprocessor_artifact_path = pg_input.get("preprocessor_artifact_path") or (
        feature_preprocessing.preprocessor_artifact_path if feature_preprocessing else None
    )

    task_type = msc.task_type or "regression"
    primary_metric = msc.primary_metric or "MAE"

    allowed_model_families = get_all_model_families()
    allowed_hpo_methods = get_all_hpo_methods()

    # Read latest WorkflowPlan for iteration_guidance
    from app.modules.workflow_planning.repository import WorkflowPlanRepository
    wp_repo = WorkflowPlanRepository()
    iteration_guidance = {}
    wp = wp_repo.get_latest_by_task_id(session, task_id)
    if wp:
        plan_json = wp.plan_json or {}
        iteration_guidance = plan_json.get("iteration_guidance", {})

    feature_columns = pg_input.get("feature_columns", [])
    if not feature_columns and feature_preprocessing and feature_preprocessing.preprocessing_json:
        ms_input = feature_preprocessing.preprocessing_json.get("model_search_input") or {}
        feature_columns = ms_input.get("feature_columns", [])

    return {
        "task_id": task_id,
        "model_search_context_id": msc.id,
        "feature_preprocessing_id": fpp_id,
        "task_type": task_type,
        "primary_metric": primary_metric,
        "target_column": msc.target_column or pg_input.get("target_column"),
        "feature_columns": feature_columns,
        "n_samples": msc.n_samples or 0,
        "n_features": msc.n_final_features or 0,
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
        "context_json": context_json,
        "model_search_context": msc,
        "feature_preprocessing": feature_preprocessing,
        "iteration_guidance": iteration_guidance,
    }
