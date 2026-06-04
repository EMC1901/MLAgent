import logging
import traceback
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

logger = logging.getLogger(__name__)

router = APIRouter(tags=["pipeline-execution"])
service = PipelineExecutionService()


@router.post("/api/pipeline-executions/{task_id}", response_model=dict)
def create_pipeline_execution(
    task_id: str,
    request: PipelineExecutionCreateRequest = PipelineExecutionCreateRequest(),
    session: Session = Depends(get_session),
):
    logger.info("POST /api/pipeline-executions/%s", task_id)
    try:
        result = service.create_pipeline_execution(session, task_id, request)
        logger.info("done — pe_id=%s status=%s", result.pipeline_execution_id, result.status)
        return success_response(
            "Pipeline execution completed successfully.",
            data=result.model_dump() if hasattr(result, "model_dump") else result,
        )
    except BusinessException as e:
        logger.error("BusinessException: %s (%s)", e.message, e.error_code)
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
    except Exception:
        logger.error("UNHANDLED EXCEPTION:\n%s", traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal server error during pipeline execution.", "error_code": "INTERNAL_ERROR"},
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
    except Exception:
        logger.error("UNHANDLED EXCEPTION in get_pipeline_execution:\n%s", traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal server error.", "error_code": "INTERNAL_ERROR"},
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
    except Exception:
        logger.error("UNHANDLED EXCEPTION in get_latest_pipeline_execution:\n%s", traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal server error.", "error_code": "INTERNAL_ERROR"},
        )


@router.post("/api/pipeline-executions/{task_id}/rerun", response_model=dict)
def rerun_pipeline_execution(
    task_id: str,
    session: Session = Depends(get_session),
):
    logger.info("RERUN /api/pipeline-executions/%s/rerun", task_id)
    try:
        result = service.rerun_pipeline_execution(session, task_id)
        logger.info("rerun done — pe_id=%s status=%s", result.pipeline_execution_id, result.status)
        return success_response(
            "Pipeline execution re-run successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        logger.error("BusinessException in rerun: %s (%s)", e.message, e.error_code)
        status_code = 404 if e.error_code in (
            "PIPELINE_EXECUTION_NOT_FOUND",
            "PIPELINE_GENERATION_REQUIRED",
            "PIPELINE_GENERATION_NOT_READY",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )
    except Exception:
        logger.error("UNHANDLED EXCEPTION in rerun:\n%s", traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal server error during pipeline re-run.", "error_code": "INTERNAL_ERROR"},
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
    except Exception:
        logger.error("UNHANDLED EXCEPTION in get_summary:\n%s", traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal server error.", "error_code": "INTERNAL_ERROR"},
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
    except Exception:
        logger.error("UNHANDLED EXCEPTION in get_trials:\n%s", traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal server error.", "error_code": "INTERNAL_ERROR"},
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
    except Exception:
        logger.error("UNHANDLED EXCEPTION in get_metric_evaluation_input:\n%s", traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal server error.", "error_code": "INTERNAL_ERROR"},
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
    except Exception:
        logger.error("UNHANDLED EXCEPTION in get_logs:\n%s", traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal server error.", "error_code": "INTERNAL_ERROR"},
        )
