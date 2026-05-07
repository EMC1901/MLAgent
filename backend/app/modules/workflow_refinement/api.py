from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.database.session import get_session
from app.modules.workflow_refinement.schemas import WorkflowRefinementCreateRequest
from app.modules.workflow_refinement.service import WorkflowRefinementService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(tags=["workflow-refinement"])
service = WorkflowRefinementService()


@router.post("/api/workflow-refinements/{task_id}", response_model=dict)
def create_workflow_refinement(
    task_id: str,
    request: WorkflowRefinementCreateRequest = WorkflowRefinementCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.create_workflow_refinement(session, task_id, request)
        return success_response(
            "Workflow refinement completed successfully.",
            data=result.model_dump() if hasattr(result, "model_dump") else result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "RESULT_DIAGNOSIS_REQUIRED",
            "RESULT_DIAGNOSIS_NOT_READY_FOR_WORKFLOW_REFINEMENT",
            "WORKFLOW_REFINEMENT_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/workflow-refinements/{workflow_refinement_id}", response_model=dict)
def get_workflow_refinement(
    workflow_refinement_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_workflow_refinement(session, workflow_refinement_id)
        return success_response(
            "Workflow refinement retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("WORKFLOW_REFINEMENT_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/tasks/{task_id}/workflow-refinement", response_model=dict)
def get_latest_workflow_refinement_by_task(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response(
            "Workflow refinement retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("WORKFLOW_REFINEMENT_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.post("/api/workflow-refinements/{task_id}/rerun", response_model=dict)
def rerun_workflow_refinement(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_workflow_refinement(session, task_id)
        return success_response(
            "Workflow refinement re-run successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "RESULT_DIAGNOSIS_REQUIRED",
            "RESULT_DIAGNOSIS_NOT_READY_FOR_WORKFLOW_REFINEMENT",
            "WORKFLOW_REFINEMENT_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get(
    "/api/workflow-refinements/{workflow_refinement_id}/revised-workflow-plan",
    response_model=dict,
)
def get_revised_workflow_plan(
    workflow_refinement_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_revised_workflow_plan(session, workflow_refinement_id)
        return success_response(
            "Revised workflow plan retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("WORKFLOW_REFINEMENT_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get(
    "/api/workflow-refinements/{workflow_refinement_id}/iteration-rerun-plan",
    response_model=dict,
)
def get_iteration_rerun_plan(
    workflow_refinement_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_iteration_rerun_plan(session, workflow_refinement_id)
        return success_response(
            "Iteration rerun plan retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("WORKFLOW_REFINEMENT_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get(
    "/api/workflow-refinements/{workflow_refinement_id}/final-pipeline-selection-input",
    response_model=dict,
)
def get_final_pipeline_selection_input(
    workflow_refinement_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_final_pipeline_selection_input(session, workflow_refinement_id)
        return success_response(
            "Final pipeline selection input retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("WORKFLOW_REFINEMENT_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get(
    "/api/result-diagnoses/{rd_id}/iteration-context",
    response_model=dict,
)
def get_iteration_context_for_diagnosis(
    rd_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_iteration_context_for_diagnosis(session, rd_id)
        return success_response(
            "Iteration context retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=400,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.post(
    "/api/workflow-refinements/{workflow_refinement_id}/adopt",
    response_model=dict,
)
def adopt_revised_plan(
    workflow_refinement_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.adopt_revised_plan(session, workflow_refinement_id)
        return success_response(
            "Revised plan adopted successfully as new WorkflowPlan.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "WORKFLOW_REFINEMENT_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )
