import logging
from typing import Optional
from sqlmodel import Session
from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.model_search_context.repository import ModelSearchContextRepository
from app.shared.registry.model_registry import (
    get_model_families_for_task_type,
    get_all_model_families,
)
from app.shared.registry.hpo_registry import (
    get_all_hpo_methods,
)
from app.modules.model_search.schemas import LLMModelSearchContext
from app.modules.model_search.exceptions import (
    ModelSearchContextRequiredException,
    ModelSearchContextNotReadyException,
    ModelReadyInputNotReadyException,
    ModelRegistryUnavailableException,
    HPORegistryUnavailableException,
)

logger = logging.getLogger(__name__)


def build_model_search_context(
    session: Session,
    task_id: str,
) -> dict:
    """Read upstream context and registries. Returns dict with keys:
    - task_id
    - model_search_context_id
    - workflow_plan_id
    - feature_preprocessing_id
    - task_type
    - primary_metric
    - model_ready_matrix_path
    - target_column
    - feature_columns
    - n_samples
    - n_features
    - updated_model_strategy
    - updated_hpo_strategy
    - updated_validation_strategy
    - updated_evaluation_strategy
    - preprocessing_summary
    - feature_group_summary
    - allowed_model_families
    - allowed_hpo_methods
    """
    task_repo = TaskSpecificationRepository()
    msc_repo = ModelSearchContextRepository()

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

    context_json = msc.context_json or {}
    msc_input = context_json.get("model_search_context_input") or {}

    if not msc_input.get("ready_for_model_search_plan", False):
        raise ModelReadyInputNotReadyException()

    task_type = msc_input.get("task_type") or "regression"
    primary_metric = msc_input.get("primary_metric") or ""

    allowed_model_families = get_model_families_for_task_type(task_type)
    if not allowed_model_families:
        allowed_model_families = get_all_model_families()
    if not allowed_model_families:
        raise ModelRegistryUnavailableException()

    allowed_hpo_methods = get_all_hpo_methods()
    if not allowed_hpo_methods:
        raise HPORegistryUnavailableException()

    return {
        "task_id": task_id,
        "model_search_context_id": msc.id,
        "workflow_plan_id": msc.workflow_plan_id,
        "feature_preprocessing_id": msc.feature_preprocessing_id,
        "task_type": task_type,
        "primary_metric": primary_metric,
        "model_ready_matrix_path": msc_input.get("model_ready_matrix_path"),
        "target_column": msc_input.get("target_column"),
        "feature_columns": msc_input.get("feature_columns", []),
        "n_samples": msc.n_samples or 0,
        "n_features": msc.n_final_features or 0,
        "updated_model_strategy": context_json.get("updated_model_strategy", {}),
        "updated_hpo_strategy": context_json.get("updated_hpo_strategy", {}),
        "updated_validation_strategy": context_json.get("updated_validation_strategy", {}),
        "updated_evaluation_strategy": context_json.get("updated_evaluation_strategy", {}),
        "preprocessing_summary": _extract_preprocessing_summary(context_json),
        "feature_group_summary": _extract_feature_group_summary(context_json),
        "allowed_model_families": allowed_model_families,
        "allowed_hpo_methods": allowed_hpo_methods,
    }


def _extract_preprocessing_summary(context_json: dict) -> dict:
    ps = context_json.get("preprocessing_summary") or {}
    if hasattr(ps, "model_dump"):
        ps = ps.model_dump()
    return {
        "imputation_executed": ps.get("imputation_executed", False),
        "scaling_executed": ps.get("scaling_executed", False),
        "feature_selection_executed": ps.get("feature_selection_executed", False),
        "categorical_encoding_executed": ps.get("categorical_encoding_executed", False),
        "preprocessing_pipeline_artifact_id": ps.get("preprocessing_pipeline_artifact_id"),
    }


def _extract_feature_group_summary(context_json: dict) -> dict:
    fgs = context_json.get("feature_group_summary") or {}
    if hasattr(fgs, "model_dump"):
        fgs = fgs.model_dump()
    return {
        "retained_groups": fgs.get("retained_groups", []),
        "dropped_groups": fgs.get("dropped_groups", []),
        "partially_retained_groups": fgs.get("partially_retained_groups", []),
    }
