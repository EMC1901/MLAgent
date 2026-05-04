from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.database.session import get_session
from app.modules.model_search_context.schemas import ModelSearchContextCreateRequest
from app.modules.model_search_context.service import ModelSearchContextService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(tags=["model-search-context"])
service = ModelSearchContextService()


@router.post("/api/model-search-contexts/{task_id}", response_model=dict)
def create_model_search_context(
    task_id: str,
    request: ModelSearchContextCreateRequest = ModelSearchContextCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.create_model_search_context(session, task_id, request)
        return success_response(
            "Model search context created successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "MODEL_SEARCH_CONTEXT_NOT_FOUND",
            "TASK_NOT_FOUND", "TASK_NOT_READY",
            "INTERPRETATION_NOT_READY", "DATASET_PROFILE_NOT_READY",
            "WORKFLOW_PLAN_NOT_READY", "FEATURE_ENGINEERING_NOT_READY",
            "FEATURE_PREPROCESSING_NOT_READY", "NOT_READY_FOR_MODEL_SEARCH",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/model-search-contexts/{context_id}", response_model=dict)
def get_model_search_context(context_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_model_search_context(session, context_id)
        return success_response(
            "Model search context retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "MODEL_SEARCH_CONTEXT_NOT_FOUND"
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/tasks/{task_id}/model-search-context", response_model=dict)
def get_latest_model_search_context_by_task(
    task_id: str, session: Session = Depends(get_session),
):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response(
            "Model search context retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "MODEL_SEARCH_CONTEXT_NOT_FOUND"
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.post("/api/model-search-contexts/{task_id}/rerun", response_model=dict)
def rerun_model_search_context(
    task_id: str,
    request: ModelSearchContextCreateRequest = ModelSearchContextCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_model_search_context(session, task_id, request)
        return success_response(
            "Model search context re-run successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "MODEL_SEARCH_CONTEXT_NOT_FOUND",
            "TASK_NOT_FOUND", "TASK_NOT_READY",
            "INTERPRETATION_NOT_READY", "DATASET_PROFILE_NOT_READY",
            "WORKFLOW_PLAN_NOT_READY", "FEATURE_ENGINEERING_NOT_READY",
            "FEATURE_PREPROCESSING_NOT_READY", "NOT_READY_FOR_MODEL_SEARCH",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )
