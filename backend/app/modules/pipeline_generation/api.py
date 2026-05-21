from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.database.session import get_session
from app.modules.pipeline_generation.schemas import PipelineGenerationCreateRequest
from app.modules.pipeline_generation.service import PipelineGenerationService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(tags=["pipeline-generation"])
service = PipelineGenerationService()


@router.post("/api/pipeline-generations/{task_id}", response_model=dict)
def create_pipeline_generation(
    task_id: str,
    request: PipelineGenerationCreateRequest = PipelineGenerationCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.create_pipeline_generation(session, task_id, request)
        return success_response(
            "Pipeline generation created successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "PIPELINE_GENERATION_NOT_FOUND",
            "TASK_NOT_FOUND", "MODEL_SEARCH_CONTEXT_REQUIRED",
            "MODEL_SEARCH_CONTEXT_NOT_READY", "PIPELINE_GENERATION_INPUT_MISSING",
            "ARTIFACT_RESOLVE_FAILED",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/pipeline-generations/{pipeline_generation_id}", response_model=dict)
def get_pipeline_generation(
    pipeline_generation_id: str, session: Session = Depends(get_session),
):
    try:
        result = service.get_pipeline_generation(session, pipeline_generation_id)
        return success_response(
            "Pipeline generation retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "PIPELINE_GENERATION_NOT_FOUND"
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/tasks/{task_id}/pipeline-generation", response_model=dict)
def get_latest_pipeline_generation_by_task(
    task_id: str, session: Session = Depends(get_session),
):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response(
            "Pipeline generation retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "PIPELINE_GENERATION_NOT_FOUND"
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.post("/api/pipeline-generations/{task_id}/rerun", response_model=dict)
def rerun_pipeline_generation(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_pipeline_generation(session, task_id)
        return success_response(
            "Pipeline generation re-run successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "PIPELINE_GENERATION_NOT_FOUND",
            "TASK_NOT_FOUND", "MODEL_SEARCH_CONTEXT_REQUIRED",
            "MODEL_SEARCH_CONTEXT_NOT_READY", "PIPELINE_GENERATION_INPUT_MISSING",
            "ARTIFACT_RESOLVE_FAILED",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/pipeline-generations/{pipeline_generation_id}/summary", response_model=dict)
def get_pipeline_generation_summary(
    pipeline_generation_id: str, session: Session = Depends(get_session),
):
    try:
        result = service.get_summary(session, pipeline_generation_id)
        return success_response(
            "Pipeline generation summary retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "PIPELINE_GENERATION_NOT_FOUND"
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/pipeline-generations/{pipeline_generation_id}/execution-input", response_model=dict)
def get_pipeline_generation_execution_input(
    pipeline_generation_id: str, session: Session = Depends(get_session),
):
    try:
        result = service.get_execution_input(session, pipeline_generation_id)
        return success_response(
            "Execution input retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "NOT_FOUND", "PIPELINE_GENERATION_NOT_FOUND"
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )
