from typing import Dict, Any
import logging

from app.modules.metric_evaluation.exceptions import MetricEvaluationInputInvalidException

logger = logging.getLogger(__name__)


REQUIRED_FIELDS = [
    "task_type",
    "target_column",
    "primary_metric",
    "metric_direction",
    "evaluation_plan",
    "trial_results",
    "prediction_artifacts",
]


def load_metric_evaluation_input(metric_input_json: Dict[str, Any]) -> Dict[str, Any]:
    if not metric_input_json:
        raise MetricEvaluationInputInvalidException(
            "metric_evaluation_input_json is empty or missing."
        )

    for field in REQUIRED_FIELDS:
        if field not in metric_input_json or metric_input_json[field] is None:
            raise MetricEvaluationInputInvalidException(
                f"Required field '{field}' is missing in metric_evaluation_input."
            )

    task_type = metric_input_json["task_type"]
    if task_type not in ("regression", "classification"):
        raise MetricEvaluationInputInvalidException(
            f"Invalid task_type '{task_type}'. Expected 'regression' or 'classification'."
        )

    trial_results = metric_input_json["trial_results"]
    if not isinstance(trial_results, list) or len(trial_results) == 0:
        raise MetricEvaluationInputInvalidException(
            "trial_results must be a non-empty list."
        )

    completed_trials = [
        t for t in trial_results
        if isinstance(t, dict) and t.get("status") == "completed"
    ]
    if len(completed_trials) == 0:
        raise MetricEvaluationInputInvalidException(
            "No completed trials found in trial_results. At least one is required."
        )

    prediction_artifacts = metric_input_json["prediction_artifacts"]
    if not isinstance(prediction_artifacts, list) or len(prediction_artifacts) == 0:
        raise MetricEvaluationInputInvalidException(
            "prediction_artifacts must be a non-empty list."
        )

    metric_direction = metric_input_json["metric_direction"]
    if metric_direction not in ("minimize", "maximize"):
        raise MetricEvaluationInputInvalidException(
            f"Invalid metric_direction '{metric_direction}'. Expected 'minimize' or 'maximize'."
        )

    # Cross-validate: does metric_direction match the expected direction for primary_metric?
    primary_metric = metric_input_json["primary_metric"]
    from app.modules.metric_evaluation.metric_registry import get_metric_direction
    expected_direction = get_metric_direction(primary_metric)
    if expected_direction != metric_direction:
        logger.warning(
            "metric_direction='%s' does not match expected direction '%s' "
            "for primary_metric='%s' — ranking may be incorrect.",
            metric_direction, expected_direction, primary_metric,
        )

    return metric_input_json
