from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.database.session import get_session
from app.modules.pipeline_execution.schemas import (
    PipelineExecutionCreateRequest,
    PipelineExecutionResponse,
    PipelineExecutionSummaryResponse,
)
from app.modules.pipeline_execution.service import PipelineExecutionService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(tags=["pipeline-execution"])
service = PipelineExecutionService()


@router.post("/api/pipeline-executions/{task_id}", response_model=dict)
def create_pipeline_execution(
    task_id: str,
    request: PipelineExecutionCreateRequest = PipelineExecutionCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.create_pipeline_execution(session, task_id, request)
        return success_response(
            "Pipeline execution completed successfully.",
            data=result.model_dump() if hasattr(result, "model_dump") else result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "PIPELINE_EXECUTION_NOT_FOUND",
            "PIPELINE_GENERATION_REQUIRED",
            "PIPELINE_GENERATION_NOT_READY",
            "PIPELINE_GENERATION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/pipeline-executions/{pipeline_execution_id}", response_model=dict)
def get_pipeline_execution(
    pipeline_execution_id: str, session: Session = Depends(get_session),
):
    try:
        result = service.get_pipeline_execution(session, pipeline_execution_id)
        return success_response(
            "Pipeline execution retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "PIPELINE_EXECUTION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/tasks/{task_id}/pipeline-execution", response_model=dict)
def get_latest_pipeline_execution_by_task(
    task_id: str, session: Session = Depends(get_session),
):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response(
            "Pipeline execution retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "PIPELINE_EXECUTION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.post("/api/pipeline-executions/{task_id}/rerun", response_model=dict)
def rerun_pipeline_execution(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_pipeline_execution(session, task_id)
        return success_response(
            "Pipeline execution re-run successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "PIPELINE_EXECUTION_NOT_FOUND",
            "PIPELINE_GENERATION_REQUIRED",
            "PIPELINE_GENERATION_NOT_READY",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/pipeline-executions/{pipeline_execution_id}/summary", response_model=dict)
def get_pipeline_execution_summary(
    pipeline_execution_id: str, session: Session = Depends(get_session),
):
    try:
        result = service.get_summary(session, pipeline_execution_id)
        return success_response(
            "Pipeline execution summary retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "PIPELINE_EXECUTION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/pipeline-executions/{pipeline_execution_id}/trials", response_model=dict)
def get_pipeline_execution_trials(
    pipeline_execution_id: str, session: Session = Depends(get_session),
):
    try:
        result = service.get_trials(session, pipeline_execution_id)
        return success_response(
            "Trial results retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "PIPELINE_EXECUTION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/pipeline-executions/{pipeline_execution_id}/metric-evaluation-input", response_model=dict)
def get_metric_evaluation_input(
    pipeline_execution_id: str, session: Session = Depends(get_session),
):
    try:
        result = service.get_metric_evaluation_input(session, pipeline_execution_id)
        return success_response(
            "Metric evaluation input retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "PIPELINE_EXECUTION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/pipeline-executions/{pipeline_execution_id}/logs", response_model=dict)
def get_pipeline_execution_logs(
    pipeline_execution_id: str, session: Session = Depends(get_session),
):
    try:
        result = service.get_logs(session, pipeline_execution_id)
        return success_response(
            "Pipeline execution logs retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "PIPELINE_EXECUTION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )
