from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.database.session import get_session
from app.modules.task_interpretation.schemas import (
    TaskInterpretationCreateRequest,
    TaskInterpretationResponse,
)
from app.modules.task_interpretation.service import TaskInterpretationService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(tags=["task-interpretation"])
service = TaskInterpretationService()


@router.post("/api/task-interpretations/{task_id}", response_model=dict)
def create_task_interpretation(
    task_id: str,
    request: TaskInterpretationCreateRequest = TaskInterpretationCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.create_interpretation(session, task_id, request)
        return success_response("Task interpretation created successfully.", data=result.model_dump())
    except BusinessException as e:
        status_code = 404 if e.error_code in ("NOT_FOUND", "INTERPRETATION_NOT_FOUND") else 400
        raise HTTPException(status_code=status_code, detail={"message": e.message, "error_code": e.error_code})


@router.get("/api/task-interpretations/{interpretation_id}", response_model=dict)
def get_task_interpretation(interpretation_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_interpretation(session, interpretation_id)
        return success_response("Task interpretation retrieved successfully.", data=result.model_dump())
    except BusinessException as e:
        status_code = 404 if e.error_code in ("NOT_FOUND", "INTERPRETATION_NOT_FOUND") else 400
        raise HTTPException(status_code=status_code, detail={"message": e.message, "error_code": e.error_code})


@router.get("/api/tasks/{task_id}/interpretation", response_model=dict)
def get_latest_interpretation_by_task(task_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response("Task interpretation retrieved successfully.", data=result.model_dump())
    except BusinessException as e:
        status_code = 404 if e.error_code in ("NOT_FOUND", "INTERPRETATION_NOT_FOUND") else 400
        raise HTTPException(status_code=status_code, detail={"message": e.message, "error_code": e.error_code})


@router.post("/api/task-interpretations/{task_id}/rerun", response_model=dict)
def rerun_task_interpretation(
    task_id: str,
    request: TaskInterpretationCreateRequest = TaskInterpretationCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_interpretation(session, task_id, request)
        return success_response("Task interpretation re-run successfully.", data=result.model_dump())
    except BusinessException as e:
        status_code = 404 if e.error_code in ("NOT_FOUND", "INTERPRETATION_NOT_FOUND") else 400
        raise HTTPException(status_code=status_code, detail={"message": e.message, "error_code": e.error_code})
