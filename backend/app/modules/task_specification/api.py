from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.database.session import get_session
from app.modules.task_specification.schemas import (
    TaskSpecificationCreateRequest,
    TaskSpecificationUpdateRequest,
    TaskSpecificationResponse,
    ValidationResultResponse,
)
from app.modules.task_specification.service import TaskSpecificationService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(prefix="/api/tasks", tags=["task-specification"])
service = TaskSpecificationService()


@router.post("", response_model=dict)
def create_task(request: TaskSpecificationCreateRequest, session: Session = Depends(get_session)):
    try:
        result = service.create_task(session, request)
        return success_response("Task specification created successfully.", data=result.model_dump())
    except BusinessException as e:
        raise HTTPException(status_code=400, detail={"message": e.message, "error_code": e.error_code})


@router.get("/{task_id}", response_model=dict)
def get_task(task_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_task(session, task_id)
        return success_response("Task specification retrieved successfully.", data=result.model_dump())
    except BusinessException as e:
        status_code = 404 if e.error_code == "NOT_FOUND" else 400
        raise HTTPException(status_code=status_code, detail={"message": e.message, "error_code": e.error_code})


@router.put("/{task_id}", response_model=dict)
def update_task(task_id: str, request: TaskSpecificationUpdateRequest, session: Session = Depends(get_session)):
    try:
        result = service.update_task(session, task_id, request)
        return success_response("Task specification updated successfully.", data=result.model_dump())
    except BusinessException as e:
        status_code = 404 if e.error_code == "NOT_FOUND" else 400
        raise HTTPException(status_code=status_code, detail={"message": e.message, "error_code": e.error_code})


@router.post("/{task_id}/validate", response_model=dict)
def validate_task(task_id: str, session: Session = Depends(get_session)):
    try:
        result = service.validate_task(session, task_id)
        return success_response("Task specification validated successfully.", data=result.model_dump())
    except BusinessException as e:
        status_code = 404 if e.error_code == "NOT_FOUND" else 400
        raise HTTPException(status_code=status_code, detail={"message": e.message, "error_code": e.error_code})
