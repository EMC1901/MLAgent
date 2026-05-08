from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.database.session import get_session
from app.modules.final_output.schemas import FinalOutputCreateRequest
from app.modules.final_output.service import FinalOutputService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(tags=["final-output"])
service = FinalOutputService()


@router.post("/api/final-outputs/{task_id}", response_model=dict)
def create_final_output(
    task_id: str,
    request: FinalOutputCreateRequest = FinalOutputCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.create_final_output(session, task_id, request)
        return success_response(
            "Final output generated successfully.",
            data=result.model_dump() if hasattr(result, "model_dump") else result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "INTERPRETABILITY_ANALYSIS_REQUIRED",
            "INTERPRETABILITY_ANALYSIS_NOT_READY_FOR_FINAL_OUTPUT",
            "FINAL_OUTPUT_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/final-outputs/{final_output_id}", response_model=dict)
def get_final_output(
    final_output_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_final_output(session, final_output_id)
        return success_response(
            "Final output retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("FINAL_OUTPUT_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/tasks/{task_id}/final-output", response_model=dict)
def get_latest_final_output_by_task(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response(
            "Latest final output retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("FINAL_OUTPUT_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.post("/api/final-outputs/{task_id}/rerun", response_model=dict)
def rerun_final_output(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_final_output(session, task_id)
        return success_response(
            "Final output re-run completed successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "INTERPRETABILITY_ANALYSIS_REQUIRED",
            "INTERPRETABILITY_ANALYSIS_NOT_READY_FOR_FINAL_OUTPUT",
            "FINAL_OUTPUT_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/final-outputs/{final_output_id}/report", response_model=dict)
def get_final_report(
    final_output_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_report(session, final_output_id)
        return success_response(
            "Final report retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("FINAL_OUTPUT_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/final-outputs/{final_output_id}/workflow-trace", response_model=dict)
def get_workflow_trace(
    final_output_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_workflow_trace(session, final_output_id)
        return success_response(
            "Workflow trace retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("FINAL_OUTPUT_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/final-outputs/{final_output_id}/artifact-manifest", response_model=dict)
def get_artifact_manifest(
    final_output_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_artifact_manifest(session, final_output_id)
        return success_response(
            "Artifact manifest retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("FINAL_OUTPUT_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/final-outputs/{final_output_id}/downloads", response_model=dict)
def get_download_links(
    final_output_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_download_links(session, final_output_id)
        return success_response(
            "Download links retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("FINAL_OUTPUT_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )
