from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.database.session import get_session
from app.modules.result_diagnosis.schemas import ResultDiagnosisCreateRequest
from app.modules.result_diagnosis.service import ResultDiagnosisService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(tags=["result-diagnosis"])
service = ResultDiagnosisService()


@router.post("/api/result-diagnoses/{task_id}", response_model=dict)
def create_result_diagnosis(
    task_id: str,
    request: ResultDiagnosisCreateRequest = ResultDiagnosisCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.create_result_diagnosis(session, task_id, request)
        return success_response(
            "Result diagnosis completed successfully.",
            data=result.model_dump() if hasattr(result, "model_dump") else result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "METRIC_EVALUATION_REQUIRED",
            "METRIC_EVALUATION_NOT_READY_FOR_DIAGNOSIS",
            "RESULT_DIAGNOSIS_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/result-diagnoses/{result_diagnosis_id}", response_model=dict)
def get_result_diagnosis(
    result_diagnosis_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_result_diagnosis(session, result_diagnosis_id)
        return success_response(
            "Result diagnosis retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("RESULT_DIAGNOSIS_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/tasks/{task_id}/result-diagnosis", response_model=dict)
def get_latest_result_diagnosis_by_task(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response(
            "Result diagnosis retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("RESULT_DIAGNOSIS_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.post("/api/result-diagnoses/{task_id}/rerun", response_model=dict)
def rerun_result_diagnosis(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_result_diagnosis(session, task_id)
        return success_response(
            "Result diagnosis re-run successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "METRIC_EVALUATION_REQUIRED",
            "METRIC_EVALUATION_NOT_READY_FOR_DIAGNOSIS",
            "RESULT_DIAGNOSIS_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/result-diagnoses/{result_diagnosis_id}/summary", response_model=dict)
def get_result_diagnosis_summary(
    result_diagnosis_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_summary(session, result_diagnosis_id)
        return success_response(
            "Result diagnosis summary retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("RESULT_DIAGNOSIS_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get(
    "/api/result-diagnoses/{result_diagnosis_id}/closed-loop-refinement-input",
    response_model=dict,
)
def get_closed_loop_refinement_input(
    result_diagnosis_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_closed_loop_refinement_input(session, result_diagnosis_id)
        return success_response(
            "Closed-loop refinement input retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in ("RESULT_DIAGNOSIS_NOT_FOUND",) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )
