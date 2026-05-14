from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import Optional
from app.shared.database.session import get_session
from app.modules.feature_engineering.schemas import FeatureEngineeringCreateRequest
from app.modules.feature_engineering.service import FeatureEngineeringService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(tags=["feature-engineering"])
service = FeatureEngineeringService()


@router.post("/api/feature-engineering/{task_id}", response_model=dict)
def create_feature_engineering(
    task_id: str,
    request: FeatureEngineeringCreateRequest = FeatureEngineeringCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.create_feature_engineering(session, task_id, request)
        return success_response("Feature engineering completed successfully.", data=result.model_dump())
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "FEATURE_ENGINEERING_NOT_FOUND", "TASK_NOT_FOUND", "TASK_NOT_READY",
            "INTERPRETATION_NOT_READY", "DATASET_PROFILE_NOT_READY", "WORKFLOW_PLAN_NOT_READY",
        ) else 400
        raise HTTPException(status_code=status_code, detail={"message": e.message, "error_code": e.error_code})


@router.get("/api/feature-engineering/{feature_engineering_id}", response_model=dict)
def get_feature_engineering(feature_engineering_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_feature_engineering(session, feature_engineering_id)
        return success_response("Feature engineering retrieved successfully.", data=result.model_dump())
    except BusinessException as e:
        status_code = 404 if e.error_code in ("NOT_FOUND", "FEATURE_ENGINEERING_NOT_FOUND") else 400
        raise HTTPException(status_code=status_code, detail={"message": e.message, "error_code": e.error_code})


@router.get("/api/tasks/{task_id}/feature-engineering", response_model=dict)
def get_latest_feature_engineering_by_task(task_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response("Feature engineering retrieved successfully.", data=result.model_dump())
    except BusinessException as e:
        status_code = 404 if e.error_code in ("NOT_FOUND", "FEATURE_ENGINEERING_NOT_FOUND") else 400
        raise HTTPException(status_code=status_code, detail={"message": e.message, "error_code": e.error_code})


@router.post("/api/feature-engineering/{task_id}/rerun", response_model=dict)
def rerun_feature_engineering(
    task_id: str,
    request: FeatureEngineeringCreateRequest = FeatureEngineeringCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_feature_engineering(session, task_id, request)
        return success_response("Feature engineering re-run successfully.", data=result.model_dump())
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "FEATURE_ENGINEERING_NOT_FOUND", "TASK_NOT_FOUND", "TASK_NOT_READY",
            "INTERPRETATION_NOT_READY", "DATASET_PROFILE_NOT_READY", "WORKFLOW_PLAN_NOT_READY",
        ) else 400
        raise HTTPException(status_code=status_code, detail={"message": e.message, "error_code": e.error_code})


@router.get("/api/feature-engineering/{feature_engineering_id}/preview", response_model=dict)
def get_feature_matrix_preview(feature_engineering_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_preview(session, feature_engineering_id)
        return success_response("Feature preview retrieved successfully.", data=result.model_dump())
    except BusinessException as e:
        status_code = 404 if e.error_code in ("NOT_FOUND", "FEATURE_ENGINEERING_NOT_FOUND") else 400
        raise HTTPException(status_code=status_code, detail={"message": e.message, "error_code": e.error_code})


# ---- New endpoints ----

@router.get("/api/feature-engineering/capabilities", response_model=dict)
def get_fe_capabilities(
    input_modality: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    feature_family: Optional[str] = Query(None),
):
    from app.shared.registry.fe_capability_registry import get_available_fe_capabilities, get_all_fe_capabilities
    available = get_available_fe_capabilities(input_modality=input_modality, task_type=task_type, feature_family=feature_family)
    all_caps = get_all_fe_capabilities()
    return success_response("FE capabilities retrieved.", data={
        "capabilities": [c.model_dump() for c in all_caps],
        "available": [c.model_dump() for c in available],
        "total_count": len(all_caps),
        "available_count": len(available),
    })


@router.get("/api/feature-engineering/{feature_engineering_id}/execution-report", response_model=dict)
def get_execution_report(feature_engineering_id: str, session: Session = Depends(get_session)):
    try:
        fe = service.fe_repo.get_by_id(session, feature_engineering_id)
        if not fe:
            raise HTTPException(status_code=404, detail={"message": "Not found.", "error_code": "NOT_FOUND"})
        report = fe.execution_report_json or (fe.feature_json or {}).get("execution_report") or {}
        return success_response("Execution report retrieved.", data={"feature_engineering_id": feature_engineering_id, "execution_report": report})
    except BusinessException as e:
        raise HTTPException(status_code=400, detail={"message": e.message, "error_code": e.error_code})


@router.get("/api/feature-engineering/{feature_engineering_id}/feature-groups", response_model=dict)
def get_feature_groups(feature_engineering_id: str, session: Session = Depends(get_session)):
    try:
        fe = service.fe_repo.get_by_id(session, feature_engineering_id)
        if not fe:
            raise HTTPException(status_code=404, detail={"message": "Not found.", "error_code": "NOT_FOUND"})
        groups = fe.feature_groups_json or (fe.feature_json or {}).get("feature_groups", [])
        return success_response("Feature groups retrieved.", data={"feature_engineering_id": feature_engineering_id, "feature_groups": groups})
    except BusinessException as e:
        raise HTTPException(status_code=400, detail={"message": e.message, "error_code": e.error_code})


@router.get("/api/feature-engineering/{feature_engineering_id}/quality-profile", response_model=dict)
def get_quality_profile(feature_engineering_id: str, session: Session = Depends(get_session)):
    try:
        fe = service.fe_repo.get_by_id(session, feature_engineering_id)
        if not fe:
            raise HTTPException(status_code=404, detail={"message": "Not found.", "error_code": "NOT_FOUND"})
        profile = fe.quality_profile_json or (fe.feature_json or {}).get("feature_quality_profile") or {}
        return success_response("Quality profile retrieved.", data={"feature_engineering_id": feature_engineering_id, "feature_quality_profile": profile})
    except BusinessException as e:
        raise HTTPException(status_code=400, detail={"message": e.message, "error_code": e.error_code})


@router.get("/api/feature-engineering/{feature_engineering_id}/preprocessing-decision-input", response_model=dict)
def get_preprocessing_decision_input(feature_engineering_id: str, session: Session = Depends(get_session)):
    try:
        fe = service.fe_repo.get_by_id(session, feature_engineering_id)
        if not fe:
            raise HTTPException(status_code=404, detail={"message": "Not found.", "error_code": "NOT_FOUND"})
        dinput = fe.preprocessing_decision_input_json or (fe.feature_json or {}).get("feature_preprocessing_decision_input", {})
        return success_response("Preprocessing decision input retrieved.", data={"feature_engineering_id": feature_engineering_id, "feature_preprocessing_decision_input": dinput})
    except BusinessException as e:
        raise HTTPException(status_code=400, detail={"message": e.message, "error_code": e.error_code})


@router.get("/api/feature-engineering/{feature_engineering_id}/provenance", response_model=dict)
def get_provenance(feature_engineering_id: str, session: Session = Depends(get_session)):
    try:
        fe = service.fe_repo.get_by_id(session, feature_engineering_id)
        if not fe:
            raise HTTPException(status_code=404, detail={"message": "Not found.", "error_code": "NOT_FOUND"})
        prov = fe.provenance_json or (fe.feature_json or {}).get("feature_provenance") or {}
        return success_response("Provenance retrieved.", data={"feature_engineering_id": feature_engineering_id, "feature_provenance": prov})
    except BusinessException as e:
        raise HTTPException(status_code=400, detail={"message": e.message, "error_code": e.error_code})
