from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.shared.database.session import get_session
from app.modules.metric_evaluation.schemas import (
    MetricEvaluationCreateRequest,
    MetricEvaluationResponse,
    MetricEvaluationSummaryResponse,
)
from app.modules.metric_evaluation.service import MetricEvaluationService
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException

router = APIRouter(tags=["metric-evaluation"])
service = MetricEvaluationService()


@router.post("/api/metric-evaluations/{task_id}", response_model=dict)
def create_metric_evaluation(
    task_id: str,
    request: MetricEvaluationCreateRequest = MetricEvaluationCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.create_metric_evaluation(session, task_id, request)
        return success_response(
            "Metric evaluation completed successfully.",
            data=result.model_dump() if hasattr(result, "model_dump") else result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "METRIC_EVALUATION_NOT_FOUND",
            "PIPELINE_EXECUTION_REQUIRED",
            "PIPELINE_EXECUTION_NOT_READY_FOR_METRIC_EVALUATION",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/metric-evaluations/{metric_evaluation_id}", response_model=dict)
def get_metric_evaluation(
    metric_evaluation_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_metric_evaluation(session, metric_evaluation_id)
        return success_response(
            "Metric evaluation retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "METRIC_EVALUATION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/tasks/{task_id}/metric-evaluation", response_model=dict)
def get_latest_metric_evaluation_by_task(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response(
            "Metric evaluation retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "METRIC_EVALUATION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.post("/api/metric-evaluations/{task_id}/rerun", response_model=dict)
def rerun_metric_evaluation(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_metric_evaluation(session, task_id)
        return success_response(
            "Metric evaluation re-run successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "METRIC_EVALUATION_NOT_FOUND",
            "PIPELINE_EXECUTION_REQUIRED",
            "PIPELINE_EXECUTION_NOT_READY_FOR_METRIC_EVALUATION",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/metric-evaluations/{metric_evaluation_id}/summary", response_model=dict)
def get_metric_evaluation_summary(
    metric_evaluation_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_summary(session, metric_evaluation_id)
        return success_response(
            "Metric evaluation summary retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "METRIC_EVALUATION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/metric-evaluations/{metric_evaluation_id}/ranking", response_model=dict)
def get_metric_evaluation_ranking(
    metric_evaluation_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_ranking(session, metric_evaluation_id)
        return success_response(
            "Model ranking retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "METRIC_EVALUATION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/metric-evaluations/{metric_evaluation_id}/trials", response_model=dict)
def get_metric_evaluation_trials(
    metric_evaluation_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_trials(session, metric_evaluation_id)
        return success_response(
            "Trial metrics retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "METRIC_EVALUATION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/api/metric-evaluations/{metric_evaluation_id}/folds", response_model=dict)
def get_metric_evaluation_folds(
    metric_evaluation_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_folds(session, metric_evaluation_id)
        return success_response(
            "Fold metrics retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "METRIC_EVALUATION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get(
    "/api/metric-evaluations/{metric_evaluation_id}/result-diagnosis-input",
    response_model=dict,
)
def get_result_diagnosis_input(
    metric_evaluation_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_result_diagnosis_input(session, metric_evaluation_id)
        return success_response(
            "Result diagnosis input retrieved successfully.",
            data=result,
        )
    except BusinessException as e:
        status_code = 404 if e.error_code in (
            "METRIC_EVALUATION_NOT_FOUND",
        ) else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )
