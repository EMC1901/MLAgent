"""Read-only API endpoints for the Featurizer Registry.

These endpoints serve as the shared contract visibility layer — Workflow Planning
and Feature Engineering both consume this, and the frontend uses it to display
what featurization capabilities the system currently supports.
"""
from fastapi import APIRouter, Query, HTTPException
from app.shared.registry.featurizer_registry import (
    get_all_featurizers,
    get_available_featurizers,
    get_featurizer_by_id,
    get_planned_featurizers,
    validate_registry,
    check_all_dependencies,
    get_featurizer_effective_status,
)
from app.shared.registry.schemas import (
    FeaturizerDetailResponse,
    DependenciesStatusResponse,
)
from app.shared.common.response import success_response

registry_router = APIRouter(tags=["registry"])


@registry_router.get("/api/registries/featurizers", response_model=dict)
def list_featurizers(
    input_modality: str = Query(None, description="Filter by input modality"),
    task_type: str = Query(None, description="Filter by task type"),
    status: str = Query(None, description="Filter by status: available, planned, etc."),
    feature_type: str = Query(None, description="Filter by feature type"),
    requires_dependency: str = Query(None, description="Filter by required dependency (e.g. matminer)"),
    mvp_supported: bool = Query(None, description="Filter by MVP support status"),
):
    """Query the Featurizer Registry.

    Without filters, returns all featurizers with their full Spec including
    dependency_status. With input_modality and status=available, returns only
    executable featurizers.
    """
    if status and status != "all":
        all_specs = get_all_featurizers()
        filtered = [s for s in all_specs if get_featurizer_effective_status(s) == status]
        if input_modality:
            filtered = [s for s in filtered if input_modality in s.input_modalities]
        if task_type:
            filtered = [s for s in filtered if task_type in s.supported_task_types]
    else:
        filtered = get_all_featurizers()
        if input_modality:
            filtered = [s for s in filtered if input_modality in s.input_modalities]
        if task_type:
            filtered = [s for s in filtered if task_type in s.supported_task_types]

    if feature_type:
        filtered = [s for s in filtered if s.feature_type == feature_type]
    if requires_dependency:
        filtered = [s for s in filtered if requires_dependency in s.requires_dependencies]
    if mvp_supported is not None:
        filtered = [s for s in filtered if s.mvp_supported == mvp_supported]

    data = {
        "featurizers": [s.model_dump() for s in filtered],
        "total_available": len(
            [s for s in filtered if get_featurizer_effective_status(s) == "available"]
        ),
        "total_planned": len([s for s in filtered if s.status == "planned"]),
    }
    return success_response("Featurizer registry retrieved successfully.", data=data)


@registry_router.get("/api/registries/featurizers/validate", response_model=dict)
def validate_featurizer_registry():
    """Run self-consistency checks on the Registry. Returns any issues found."""
    issues = validate_registry()
    return success_response(
        "Registry validation complete.",
        data={"is_valid": len(issues) == 0, "issues": issues},
    )


@registry_router.get("/api/registries/featurizers/{featurizer_id}", response_model=dict)
def get_featurizer_detail(featurizer_id: str):
    """Get detailed information about a specific featurizer.

    Returns the full FeaturizerSpec, dependency_status, and effective_status
    (which considers whether required dependencies are actually installed).
    """
    spec = get_featurizer_by_id(featurizer_id)
    if spec is None:
        raise HTTPException(
            status_code=404,
            detail={"message": f"Featurizer '{featurizer_id}' not found.", "error_code": "FEATURIZER_NOT_FOUND"},
        )

    eff_status = get_featurizer_effective_status(spec)
    detail = FeaturizerDetailResponse(
        spec=spec,
        dependency_status=spec.dependency_status,
        effective_status=eff_status,
    )
    return success_response(
        f"Featurizer '{featurizer_id}' retrieved successfully.",
        data=detail.model_dump(),
    )


@registry_router.get("/api/registries/featurizers/dependencies", response_model=dict)
def get_dependency_status():
    """Check and return the installation status of all featurizer dependencies.

    Returns per-package status (installed/not_installed) and version.
    """
    deps = check_all_dependencies()
    return success_response(
        "Featurizer dependencies checked successfully.",
        data=DependenciesStatusResponse(dependencies=deps).model_dump(),
    )
