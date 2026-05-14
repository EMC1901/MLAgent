from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.database.session import get_session
from app.shared.registry.fp_capability_registry import (
    get_available_fp_capabilities,
    get_registry_snapshot_fp,
    CAPABILITY_GROUPS,
)
from app.modules.feature_preprocessing.schemas import (
    FeaturePreprocessingCreateRequest,
    PlanRequest,
    ExecuteRequest,
)
from app.modules.feature_preprocessing.service import FeaturePreprocessingService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(tags=["feature-preprocessing"])
service = FeaturePreprocessingService()

# ---- Error code classification ----

_NOT_FOUND_CODES = {
    "NOT_FOUND", "FEATURE_PREPROCESSING_NOT_FOUND",
    "TASK_NOT_FOUND", "TASK_NOT_READY",
    "INTERPRETATION_NOT_READY", "DATASET_PROFILE_NOT_READY",
    "WORKFLOW_PLAN_NOT_READY", "FEATURE_ENGINEERING_REQUIRED",
    "FEATURE_ENGINEERING_NOT_READY", "FEATURE_ARTIFACT_MISSING",
}


def _status_code(e: BusinessException) -> int:
    return 404 if e.error_code in _NOT_FOUND_CODES else 400


# ---- Capability Registry ----

@router.get("/api/feature-preprocessing/capabilities", response_model=dict)
def get_fp_capabilities():
    try:
        available = get_available_fp_capabilities()
        snapshot = get_registry_snapshot_fp()
        return success_response(
            "Feature Preprocessing capabilities retrieved.",
            data={
                "capability_groups": CAPABILITY_GROUPS,
                "available_capabilities": [
                    {
                        "capability_id": c.capability_id,
                        "display_name": c.display_name,
                        "capability_group": c.capability_group,
                        "operation_type": c.operation_type,
                        "supported_feature_types": c.supported_feature_types,
                        "requires_target": c.requires_target,
                        "fit_scope": c.fit_scope,
                        "allowed_pipeline_positions": c.allowed_pipeline_positions,
                        "parameters_schema": c.parameters_schema,
                        "default_parameters": c.default_parameters,
                        "risk_notes": c.risk_notes,
                        "fallback_capability_ids": c.fallback_capability_ids,
                        "status": c.status,
                    }
                    for c in available
                ],
                "snapshot": snapshot,
            },
        )
    except BusinessException as e:
        raise HTTPException(status_code=_status_code(e), detail={"message": e.message, "error_code": e.error_code})


# ---- Create (main flow) ----

@router.post("/api/feature-preprocessing/{task_id}", response_model=dict)
def create_feature_preprocessing(
    task_id: str,
    request: FeaturePreprocessingCreateRequest = FeaturePreprocessingCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.create_feature_preprocessing(session, task_id, request)
        return success_response(
            "Feature preprocessing completed successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=_status_code(e),
            detail={"message": e.message, "error_code": e.error_code},
        )


# ---- Plan (generate plan only, no execution) ----

@router.post("/api/feature-preprocessing/{task_id}/plan", response_model=dict)
def generate_preprocessing_plan(
    task_id: str,
    request: PlanRequest = PlanRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.plan_only(session, task_id, request)
        return success_response(
            "PreprocessingPlan generated successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=_status_code(e),
            detail={"message": e.message, "error_code": e.error_code},
        )


# ---- Execute (execute a validated plan) ----

@router.post("/api/feature-preprocessing/{task_id}/execute", response_model=dict)
def execute_preprocessing_plan(
    task_id: str,
    request: ExecuteRequest = ExecuteRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.execute_plan(session, task_id, request)
        return success_response(
            "PreprocessingPlan executed successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=_status_code(e),
            detail={"message": e.message, "error_code": e.error_code},
        )


# ---- Get by ID ----

@router.get("/api/feature-preprocessing/{preprocessing_id}", response_model=dict)
def get_feature_preprocessing(preprocessing_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_feature_preprocessing(session, preprocessing_id)
        return success_response(
            "Feature preprocessing retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=_status_code(e),
            detail={"message": e.message, "error_code": e.error_code},
        )


# ---- Get latest by task ----

@router.get("/api/tasks/{task_id}/feature-preprocessing", response_model=dict)
def get_latest_feature_preprocessing_by_task(task_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response(
            "Feature preprocessing retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=_status_code(e),
            detail={"message": e.message, "error_code": e.error_code},
        )


# ---- Rerun ----

@router.post("/api/feature-preprocessing/{task_id}/rerun", response_model=dict)
def rerun_feature_preprocessing(
    task_id: str,
    request: FeaturePreprocessingCreateRequest = FeaturePreprocessingCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_feature_preprocessing(session, task_id, request)
        return success_response(
            "Feature preprocessing re-run successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=_status_code(e),
            detail={"message": e.message, "error_code": e.error_code},
        )


# ---- Preview ----

@router.get("/api/feature-preprocessing/{preprocessing_id}/preview", response_model=dict)
def get_model_ready_preview(
    preprocessing_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_preview(session, preprocessing_id)
        return success_response(
            "Model-ready preview retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=_status_code(e),
            detail={"message": e.message, "error_code": e.error_code},
        )


# ---- Sub-resource: Plan ----

@router.get("/api/feature-preprocessing/{preprocessing_id}/plan", response_model=dict)
def get_preprocessing_plan(
    preprocessing_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_plan(session, preprocessing_id)
        return success_response(
            "PreprocessingPlan retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=_status_code(e),
            detail={"message": e.message, "error_code": e.error_code},
        )


# ---- Sub-resource: Rationale ----

@router.get("/api/feature-preprocessing/{preprocessing_id}/rationale", response_model=dict)
def get_preprocessing_rationale(
    preprocessing_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_rationale(session, preprocessing_id)
        return success_response(
            "Decision rationale retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=_status_code(e),
            detail={"message": e.message, "error_code": e.error_code},
        )


# ---- Sub-resource: Execution Report ----

@router.get("/api/feature-preprocessing/{preprocessing_id}/execution-report", response_model=dict)
def get_execution_report(
    preprocessing_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_execution_report(session, preprocessing_id)
        return success_response(
            "Execution report retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=_status_code(e),
            detail={"message": e.message, "error_code": e.error_code},
        )


# ---- Sub-resource: Removed Features ----

@router.get("/api/feature-preprocessing/{preprocessing_id}/removed-features", response_model=dict)
def get_removed_features(
    preprocessing_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_removed_features(session, preprocessing_id)
        return success_response(
            "Removed features retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=_status_code(e),
            detail={"message": e.message, "error_code": e.error_code},
        )


# ---- Sub-resource: Feature Lineage ----

@router.get("/api/feature-preprocessing/{preprocessing_id}/feature-lineage", response_model=dict)
def get_feature_lineage(
    preprocessing_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_feature_lineage(session, preprocessing_id)
        return success_response(
            "Feature lineage retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=_status_code(e),
            detail={"message": e.message, "error_code": e.error_code},
        )


# ---- Sub-resource: Artifact Manifest ----

@router.get("/api/feature-preprocessing/{preprocessing_id}/artifact-manifest", response_model=dict)
def get_artifact_manifest(
    preprocessing_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_artifact_manifest(session, preprocessing_id)
        return success_response(
            "Artifact manifest retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=_status_code(e),
            detail={"message": e.message, "error_code": e.error_code},
        )


# ---- Sub-resource: Provenance ----

@router.get("/api/feature-preprocessing/{preprocessing_id}/provenance", response_model=dict)
def get_preprocessing_provenance(
    preprocessing_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_provenance(session, preprocessing_id)
        return success_response(
            "Preprocessing provenance retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=_status_code(e),
            detail={"message": e.message, "error_code": e.error_code},
        )
