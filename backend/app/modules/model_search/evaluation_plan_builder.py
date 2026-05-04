import logging
from app.modules.model_search.schemas import EvaluationPlan
from app.modules.model_search.enums import TaskType, MetricDirection

logger = logging.getLogger(__name__)

# Metric direction mapping
_METRIC_DIRECTIONS = {
    "MAE": MetricDirection.MINIMIZE,
    "MSE": MetricDirection.MINIMIZE,
    "RMSE": MetricDirection.MINIMIZE,
    "R2": MetricDirection.MAXIMIZE,
    "MAPE": MetricDirection.MINIMIZE,
    "accuracy": MetricDirection.MAXIMIZE,
    "precision": MetricDirection.MAXIMIZE,
    "recall": MetricDirection.MAXIMIZE,
    "f1": MetricDirection.MAXIMIZE,
    "roc_auc": MetricDirection.MAXIMIZE,
}

# Default secondary metrics by task type
_DEFAULT_SECONDARY = {
    TaskType.REGRESSION: ["RMSE", "R2"],
    TaskType.CLASSIFICATION: ["accuracy", "f1"],
}


def build_evaluation_plan(
    primary_metric: str,
    task_type: str,
    updated_evaluation_strategy: dict,
) -> EvaluationPlan:
    """Build evaluation plan with metric direction and secondary metrics."""
    metric_direction = _METRIC_DIRECTIONS.get(primary_metric, MetricDirection.MINIMIZE)

    secondary = updated_evaluation_strategy.get(
        "secondary_metrics",
        _DEFAULT_SECONDARY.get(task_type, []),
    )

    return EvaluationPlan(
        primary_metric=primary_metric,
        metric_direction=metric_direction,
        secondary_metrics=list(secondary) if secondary else [],
        scorer_id=updated_evaluation_strategy.get("scorer_id"),
    )
