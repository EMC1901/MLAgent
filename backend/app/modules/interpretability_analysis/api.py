from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.database.session import get_session
from app.modules.interpretability_analysis.schemas import InterpretabilityAnalysisCreateRequest
from app.modules.interpretability_analysis.service import InterpretabilityAnalysisService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(tags=["interpretability-analysis"])
service = InterpretabilityAnalysisService()


@router.post("/api/interpretability-analyses/{task_id}", response_model=dict)
def create_interpretability_analysis(
    task_id: str,
    request: InterpretabilityAnalysisCreateRequest = InterpretabilityAnalysisCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.create_interpretability_analysis(session, task_id, request)
        return success_response(
            "Interpretability analysis completed successfully.",
            data=result.model_dump() if hasattr(result, "model_dump") else result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "FINAL_PIPELINE_SELECTION_REQUIRED",
            "FINAL_SELECTION_NOT_READY_FOR_INTERPRETABILITY",
            "INTERPRETABILITY_ANALYSIS_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/interpretability-analyses/{interpretability_analysis_id}", response_model=dict)
def get_interpretability_analysis(
    interpretability_analysis_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_interpretability_analysis(session, interpretability_analysis_id)
        return success_response(
            "Interpretability analysis retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("INTERPRETABILITY_ANALYSIS_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/tasks/{task_id}/interpretability-analysis", response_model=dict)
def get_latest_interpretability_analysis_by_task(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response(
            "Latest interpretability analysis retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("INTERPRETABILITY_ANALYSIS_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.post("/api/interpretability-analyses/{task_id}/rerun", response_model=dict)
def rerun_interpretability_analysis(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_interpretability_analysis(session, task_id)
        return success_response(
            "Interpretability analysis re-run completed successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "FINAL_PIPELINE_SELECTION_REQUIRED",
            "FINAL_SELECTION_NOT_READY_FOR_INTERPRETABILITY",
            "INTERPRETABILITY_ANALYSIS_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get(
    "/api/interpretability-analyses/{interpretability_analysis_id}/feature-importance",
    response_model=dict,
)
def get_feature_importance(
    interpretability_analysis_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_feature_importance(session, interpretability_analysis_id)
        return success_response(
            "Feature importance retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("INTERPRETABILITY_ANALYSIS_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get(
    "/api/interpretability-analyses/{interpretability_analysis_id}/shap-summary",
    response_model=dict,
)
def get_shap_summary(
    interpretability_analysis_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_shap_summary(session, interpretability_analysis_id)
        return success_response(
            "SHAP summary retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("INTERPRETABILITY_ANALYSIS_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get(
    "/api/interpretability-analyses/{interpretability_analysis_id}/local-explanations",
    response_model=dict,
)
def get_local_explanations(
    interpretability_analysis_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_local_explanations(session, interpretability_analysis_id)
        return success_response(
            "Local explanations retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("INTERPRETABILITY_ANALYSIS_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get(
    "/api/interpretability-analyses/{interpretability_analysis_id}/final-output-input",
    response_model=dict,
)
def get_final_output_input(
    interpretability_analysis_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_final_output_input(session, interpretability_analysis_id)
        return success_response(
            "Final output input retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("INTERPRETABILITY_ANALYSIS_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )
