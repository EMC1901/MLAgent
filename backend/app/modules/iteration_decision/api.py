from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.database.session import get_session
from app.modules.iteration_decision.schemas import IterationDecisionCreateRequest
from app.modules.iteration_decision.service import IterationDecisionService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(tags=["iteration-decision"])
service = IterationDecisionService()


@router.post("/api/iteration-decisions/{task_id}", response_model=dict)
def create_iteration_decision(
    task_id: str,
    request: IterationDecisionCreateRequest = IterationDecisionCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.create_decision(session, task_id, request)
        return success_response(
            "Iteration decision completed successfully.",
            data=result.model_dump() if hasattr(result, "model_dump") else result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "METRIC_EVALUATION_REQUIRED",
            "METRIC_EVALUATION_NOT_READY",
            "ITERATION_DECISION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/iteration-decisions/{iteration_decision_id}", response_model=dict)
def get_iteration_decision(
    iteration_decision_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_decision(session, iteration_decision_id)
        return success_response(
            "Iteration decision retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("ITERATION_DECISION_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/tasks/{task_id}/iteration-decision", response_model=dict)
def get_latest_iteration_decision_by_task(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response(
            "Iteration decision retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("ITERATION_DECISION_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.post("/api/iteration-decisions/{task_id}/rerun", response_model=dict)
def rerun_iteration_decision(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_decision(session, task_id)
        return success_response(
            "Iteration decision re-run successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "METRIC_EVALUATION_REQUIRED",
            "METRIC_EVALUATION_NOT_READY",
            "ITERATION_DECISION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/iteration-decisions/{iteration_decision_id}/summary", response_model=dict)
def get_iteration_decision_summary(
    iteration_decision_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_summary(session, iteration_decision_id)
        return success_response(
            "Iteration decision summary retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("ITERATION_DECISION_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/tasks/{task_id}/iteration-decision/needs-fresh", response_model=dict)
def check_needs_fresh_decision(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.needs_fresh_decision(session, task_id)
        return success_response(
            "Fresh decision check completed.",
            data=result,
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=400,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get(
    "/api/iteration-decisions/{iteration_decision_id}/revised-workflow-plan",
    response_model=dict,
)
def get_revised_workflow_plan(
    iteration_decision_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_revised_workflow_plan(session, iteration_decision_id)
        return success_response(
            "Revised workflow plan retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("ITERATION_DECISION_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.post("/api/iteration-decisions/{iteration_decision_id}/adopt", response_model=dict)
def adopt_revised_plan(
    iteration_decision_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.adopt_revised_plan(session, iteration_decision_id)
        return success_response(
            "Revised plan adopted successfully as new WorkflowPlan.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("ITERATION_DECISION_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )
