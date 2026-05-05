from typing import Optional
from sqlmodel import Session
from app.modules.metric_evaluation.model import MetricEvaluation
from app.modules.metric_evaluation.repository import MetricEvaluationRepository
from app.modules.result_diagnosis.exceptions import (
    MetricEvaluationRequiredException,
    MetricEvaluationNotReadyException,
)


def build_result_diagnosis_context(
    session: Session,
    task_id: str,
    metric_evaluation_id: Optional[str] = None,
) -> MetricEvaluation:
    me_repo = MetricEvaluationRepository()

    if metric_evaluation_id:
        me = me_repo.get_by_id(session, metric_evaluation_id)
    else:
        me = me_repo.get_latest_by_task_id(session, task_id)

    if not me:
        raise MetricEvaluationRequiredException(
            f"No MetricEvaluation found for task '{task_id}'. "
            "Run Metric Evaluation first."
        )

    accepted_statuses = {"evaluated", "evaluated_with_warning", "partially_evaluated"}
    if me.status not in accepted_statuses:
        raise MetricEvaluationNotReadyException(
            f"MetricEvaluation '{me.id}' status is '{me.status}'. "
            f"Expected one of: {', '.join(sorted(accepted_statuses))}."
        )

    if not me.ready_for_result_diagnosis:
        raise MetricEvaluationNotReadyException(
            f"MetricEvaluation '{me.id}' is not ready for result diagnosis. "
            "Ensure result_diagnosis_input has been built."
        )

    return me
