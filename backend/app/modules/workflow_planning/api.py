from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.database.session import get_session
from app.modules.workflow_planning.schemas import WorkflowPlanCreateRequest
from app.modules.workflow_planning.service import WorkflowPlanningService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(tags=["workflow-planning"])
service = WorkflowPlanningService()


def _map_status_code(error_code: str) -> int:
    """Map business error codes to semantically correct HTTP status codes."""
    mapping = {
        "NOT_FOUND": 404,
        "WORKFLOW_PLAN_NOT_FOUND": 404,
        "LLM_CALL_FAILED": 502,
        "LLM_OUTPUT_PARSE_ERROR": 502,
        "WORKFLOW_PLAN_VALIDATION_FAILED": 422,
    }
    return mapping.get(error_code, 400)


@router.post("/api/workflow-plans/{task_id}", response_model=dict)
def create_workflow_plan(
    task_id: str,
    request: WorkflowPlanCreateRequest = WorkflowPlanCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.create_plan(session, task_id, request)
        return success_response("Workflow plan created successfully.", data=result.model_dump())
    except BusinessException as e:
        raise HTTPException(
            status_code=_map_status_code(e.error_code),
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/workflow-plans/{workflow_plan_id}", response_model=dict)
def get_workflow_plan(workflow_plan_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_plan(session, workflow_plan_id)
        return success_response("Workflow plan retrieved successfully.", data=result.model_dump())
    except BusinessException as e:
        raise HTTPException(
            status_code=_map_status_code(e.error_code),
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/tasks/{task_id}/workflow-plan", response_model=dict)
def get_latest_workflow_plan_by_task(task_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response("Workflow plan retrieved successfully.", data=result.model_dump())
    except BusinessException as e:
        raise HTTPException(
            status_code=_map_status_code(e.error_code),
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.post("/api/workflow-plans/{task_id}/rerun", response_model=dict)
def rerun_workflow_plan(
    task_id: str,
    request: WorkflowPlanCreateRequest = WorkflowPlanCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_plan(session, task_id, request)
        return success_response("Workflow plan re-run successfully.", data=result.model_dump())
    except BusinessException as e:
        raise HTTPException(
            status_code=_map_status_code(e.error_code),
            detail={"message": e.message, "error_code": e.error_code},
        )


# ---- New endpoints ----

@router.get("/api/workflow-plans/{workflow_plan_id}/feature-strategy", response_model=dict)
def get_feature_strategy(workflow_plan_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_feature_strategy(session, workflow_plan_id)
        return success_response("Feature strategy retrieved.", data=result.model_dump())
    except BusinessException as e:
        raise HTTPException(
            status_code=_map_status_code(e.error_code),
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/workflow-plans/{workflow_plan_id}/feature-strategy-rationale", response_model=dict)
def get_feature_strategy_rationale(workflow_plan_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_feature_strategy_rationale(session, workflow_plan_id)
        return success_response("Feature strategy rationale retrieved.", data=result.model_dump())
    except BusinessException as e:
        raise HTTPException(
            status_code=_map_status_code(e.error_code),
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/workflow-plans/{workflow_plan_id}/model-strategy", response_model=dict)
def get_model_strategy(workflow_plan_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_model_strategy(session, workflow_plan_id)
        return success_response("Model strategy retrieved.", data=result.model_dump())
    except BusinessException as e:
        raise HTTPException(
            status_code=_map_status_code(e.error_code),
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/workflow-plans/{workflow_plan_id}/preprocessing-intent", response_model=dict)
def get_preprocessing_intent(workflow_plan_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_preprocessing_intent(session, workflow_plan_id)
        return success_response("Preprocessing intent retrieved.", data=result.model_dump())
    except BusinessException as e:
        raise HTTPException(
            status_code=_map_status_code(e.error_code),
            detail={"message": e.message, "error_code": e.error_code},
        )
