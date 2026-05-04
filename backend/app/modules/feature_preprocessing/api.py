from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.database.session import get_session
from app.modules.feature_preprocessing.schemas import FeaturePreprocessingCreateRequest
from app.modules.feature_preprocessing.service import FeaturePreprocessingService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(tags=["feature-preprocessing"])
service = FeaturePreprocessingService()


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
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "FEATURE_PREPROCESSING_NOT_FOUND",
            "TASK_NOT_FOUND", "TASK_NOT_READY",
            "INTERPRETATION_NOT_READY", "DATASET_PROFILE_NOT_READY",
            "WORKFLOW_PLAN_NOT_READY", "FEATURE_ENGINEERING_REQUIRED",
            "FEATURE_ENGINEERING_NOT_READY", "FEATURE_ARTIFACT_MISSING",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/feature-preprocessing/{preprocessing_id}", response_model=dict)
def get_feature_preprocessing(preprocessing_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_feature_preprocessing(session, preprocessing_id)
        return success_response(
            "Feature preprocessing retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "FEATURE_PREPROCESSING_NOT_FOUND"
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/tasks/{task_id}/feature-preprocessing", response_model=dict)
def get_latest_feature_preprocessing_by_task(task_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response(
            "Feature preprocessing retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "FEATURE_PREPROCESSING_NOT_FOUND"
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


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
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "FEATURE_PREPROCESSING_NOT_FOUND",
            "TASK_NOT_FOUND", "TASK_NOT_READY",
            "INTERPRETATION_NOT_READY", "DATASET_PROFILE_NOT_READY",
            "WORKFLOW_PLAN_NOT_READY", "FEATURE_ENGINEERING_REQUIRED",
            "FEATURE_ENGINEERING_NOT_READY", "FEATURE_ARTIFACT_MISSING",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


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
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "FEATURE_PREPROCESSING_NOT_FOUND"
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )
