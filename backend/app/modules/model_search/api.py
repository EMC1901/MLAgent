from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.database.session import get_session
from app.modules.model_search.schemas import ModelSearchPlanCreateRequest
from app.modules.model_search.service import ModelSearchService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(tags=["model-search"])
service = ModelSearchService()


@router.post("/api/model-search-plans/{task_id}", response_model=dict)
def create_model_search_plan(
    task_id: str,
    request: ModelSearchPlanCreateRequest = ModelSearchPlanCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.create_model_search_plan(session, task_id, request)
        return success_response(
            "Model search plan created successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "MODEL_SEARCH_PLAN_NOT_FOUND",
            "TASK_NOT_FOUND", "MODEL_SEARCH_CONTEXT_REQUIRED",
            "MODEL_SEARCH_CONTEXT_NOT_READY", "MODEL_READY_INPUT_NOT_READY",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/model-search-plans/{model_search_plan_id}", response_model=dict)
def get_model_search_plan(model_search_plan_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_model_search_plan(session, model_search_plan_id)
        return success_response(
            "Model search plan retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "MODEL_SEARCH_PLAN_NOT_FOUND"
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/tasks/{task_id}/model-search-plan", response_model=dict)
def get_latest_model_search_plan_by_task(
    task_id: str, session: Session = Depends(get_session),
):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response(
            "Model search plan retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "MODEL_SEARCH_PLAN_NOT_FOUND"
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.post("/api/model-search-plans/{task_id}/rerun", response_model=dict)
def rerun_model_search_plan(
    task_id: str,
    request: ModelSearchPlanCreateRequest = ModelSearchPlanCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_model_search_plan(session, task_id, request)
        return success_response(
            "Model search plan re-run successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "MODEL_SEARCH_PLAN_NOT_FOUND",
            "TASK_NOT_FOUND", "MODEL_SEARCH_CONTEXT_REQUIRED",
            "MODEL_SEARCH_CONTEXT_NOT_READY", "MODEL_READY_INPUT_NOT_READY",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/model-search-plans/{model_search_plan_id}/summary", response_model=dict)
def get_model_search_plan_summary(
    model_search_plan_id: str, session: Session = Depends(get_session),
):
    try:
        result = service.get_plan_summary(session, model_search_plan_id)
        return success_response(
            "Model search plan summary retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "MODEL_SEARCH_PLAN_NOT_FOUND"
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )
