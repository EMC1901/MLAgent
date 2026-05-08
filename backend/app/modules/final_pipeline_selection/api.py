from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.database.session import get_session
from app.modules.final_pipeline_selection.schemas import FinalPipelineSelectionCreateRequest
from app.modules.final_pipeline_selection.service import FinalPipelineSelectionService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(tags=["final-pipeline-selection"])
service = FinalPipelineSelectionService()


@router.post("/api/final-pipeline-selections/{task_id}", response_model=dict)
def create_final_pipeline_selection(
    task_id: str,
    request: FinalPipelineSelectionCreateRequest = FinalPipelineSelectionCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.create_final_selection(session, task_id, request)
        return success_response(
            "Final pipeline selection completed successfully.",
            data=result.model_dump() if hasattr(result, "model_dump") else result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "WORKFLOW_REFINEMENT_REQUIRED",
            "WORKFLOW_REFINEMENT_NOT_READY_FOR_FINAL_SELECTION",
            "WORKFLOW_REFINEMENT_DECISION_INVALID",
            "FINAL_PIPELINE_SELECTION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/final-pipeline-selections/{final_pipeline_selection_id}", response_model=dict)
def get_final_pipeline_selection(
    final_pipeline_selection_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_final_selection(session, final_pipeline_selection_id)
        return success_response(
            "Final pipeline selection retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("FINAL_PIPELINE_SELECTION_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/tasks/{task_id}/final-pipeline-selection", response_model=dict)
def get_latest_final_pipeline_selection_by_task(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response(
            "Latest final pipeline selection retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("FINAL_PIPELINE_SELECTION_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.post("/api/final-pipeline-selections/{task_id}/rerun", response_model=dict)
def rerun_final_pipeline_selection(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_final_selection(session, task_id)
        return success_response(
            "Final pipeline selection re-run completed successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "WORKFLOW_REFINEMENT_REQUIRED",
            "WORKFLOW_REFINEMENT_NOT_READY_FOR_FINAL_SELECTION",
            "FINAL_PIPELINE_SELECTION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get(
    "/api/final-pipeline-selections/{final_pipeline_selection_id}/ranking",
    response_model=dict,
)
def get_candidate_ranking(
    final_pipeline_selection_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_candidate_ranking(session, final_pipeline_selection_id)
        return success_response(
            "Candidate ranking retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("FINAL_PIPELINE_SELECTION_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get(
    "/api/final-pipeline-selections/{final_pipeline_selection_id}/llm-explanation",
    response_model=dict,
)
def get_llm_selection_explanation(
    final_pipeline_selection_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_llm_explanation(session, final_pipeline_selection_id)
        return success_response(
            "LLM selection explanation retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("FINAL_PIPELINE_SELECTION_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get(
    "/api/final-pipeline-selections/{final_pipeline_selection_id}/artifact-manifest",
    response_model=dict,
)
def get_final_artifact_manifest(
    final_pipeline_selection_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_artifact_manifest(session, final_pipeline_selection_id)
        return success_response(
            "Final artifact manifest retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("FINAL_PIPELINE_SELECTION_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get(
    "/api/final-pipeline-selections/{final_pipeline_selection_id}/interpretability-analysis-input",
    response_model=dict,
)
def get_interpretability_analysis_input(
    final_pipeline_selection_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_interpretability_analysis_input(session, final_pipeline_selection_id)
        return success_response(
            "Interpretability analysis input retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("FINAL_PIPELINE_SELECTION_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )
