import logging
from typing import Dict, Any, Optional
from sqlmodel import Session
from app.modules.iteration_decision.exceptions import MetricEvaluationRequiredException, MetricEvaluationNotReadyException

logger = logging.getLogger(__name__)


def gather_metrics_context(session: Session, task_id: str, metric_evaluation_id: Optional[str] = None) -> Dict[str, Any]:
    """Load and validate the MetricEvaluation record and its diagnosis input."""
    from app.modules.metric_evaluation.repository import MetricEvaluationRepository
    me_repo = MetricEvaluationRepository()

    if metric_evaluation_id:
        me = me_repo.get_by_id(session, metric_evaluation_id)
    else:
        me = me_repo.get_latest_by_task_id(session, task_id)

    if not me:
        raise MetricEvaluationRequiredException(
            f"No MetricEvaluation found for task '{task_id}'. Run Metric Evaluation first."
        )

    accepted = {"evaluated", "evaluated_with_warning", "partially_evaluated"}
    if me.status not in accepted:
        raise MetricEvaluationNotReadyException(
            f"MetricEvaluation '{me.id}' status is '{me.status}'. Expected one of: {accepted}."
        )

    di_input = me.result_diagnosis_input_json or {}
    best_val = getattr(me, "best_primary_metric_value", None)
    best_model = getattr(me, "best_model_id", None)

    logger.info("Metrics context loaded — id=%s status=%s best=%s metric=%.4f",
                 me.id, me.status, best_model,
                 best_val if best_val is not None else float("nan"))

    return {
        "metric_evaluation_id": me.id,
        "pipeline_execution_id": getattr(me, "pipeline_execution_id", None),
        "status": me.status,
        "primary_metric": getattr(me, "primary_metric", None),
        "metric_direction": getattr(me, "metric_direction", "minimize"),
        "best_model_id": best_model,
        "best_trial_id": getattr(me, "best_trial_id", None),
        "best_pipeline_spec_id": getattr(me, "best_pipeline_spec_id", None),
        "best_primary_metric_value": best_val,
        "evaluation_json": me.evaluation_json,
        "metric_summary_json": getattr(me, "metric_summary_json", None),
        "model_ranking_json": getattr(me, "model_ranking_json", None),
        "result_diagnosis_input_json": di_input,
        "ready_for_result_diagnosis": getattr(me, "ready_for_result_diagnosis", False),
    }
