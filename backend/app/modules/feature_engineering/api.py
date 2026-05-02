from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
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
        return success_response(
            "Feature engineering completed successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "FEATURE_ENGINEERING_NOT_FOUND",
            "TASK_NOT_FOUND", "TASK_NOT_READY",
            "INTERPRETATION_NOT_READY", "DATASET_PROFILE_NOT_READY",
            "WORKFLOW_PLAN_NOT_READY",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/feature-engineering/{feature_engineering_id}", response_model=dict)
def get_feature_engineering(feature_engineering_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_feature_engineering(session, feature_engineering_id)
        return success_response(
            "Feature engineering retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "FEATURE_ENGINEERING_NOT_FOUND"
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/tasks/{task_id}/feature-engineering", response_model=dict)
def get_latest_feature_engineering_by_task(task_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response(
            "Feature engineering retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "FEATURE_ENGINEERING_NOT_FOUND"
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.post("/api/feature-engineering/{task_id}/rerun", response_model=dict)
def rerun_feature_engineering(
    task_id: str,
    request: FeatureEngineeringCreateRequest = FeatureEngineeringCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_feature_engineering(session, task_id, request)
        return success_response(
            "Feature engineering re-run successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "FEATURE_ENGINEERING_NOT_FOUND",
            "TASK_NOT_FOUND", "TASK_NOT_READY",
            "INTERPRETATION_NOT_READY", "DATASET_PROFILE_NOT_READY",
            "WORKFLOW_PLAN_NOT_READY",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/feature-engineering/{feature_engineering_id}/preview", response_model=dict)
def get_feature_matrix_preview(
    feature_engineering_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_preview(session, feature_engineering_id)
        return success_response(
            "Feature preview retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "FEATURE_ENGINEERING_NOT_FOUND"
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )
