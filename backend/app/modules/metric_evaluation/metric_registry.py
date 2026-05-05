from app.modules.metric_evaluation.enums import MetricDirection, TaskType


REGRESSION_METRICS = {
    "MAE": {
        "name": "MAE",
        "display_name": "Mean Absolute Error",
        "direction": MetricDirection.MINIMIZE,
        "task_types": [TaskType.REGRESSION],
    },
    "MSE": {
        "name": "MSE",
        "display_name": "Mean Squared Error",
        "direction": MetricDirection.MINIMIZE,
        "task_types": [TaskType.REGRESSION],
    },
    "RMSE": {
        "name": "RMSE",
        "display_name": "Root Mean Squared Error",
        "direction": MetricDirection.MINIMIZE,
        "task_types": [TaskType.REGRESSION],
    },
    "R2": {
        "name": "R2",
        "display_name": "R-squared",
        "direction": MetricDirection.MAXIMIZE,
        "task_types": [TaskType.REGRESSION],
    },
    "MAPE": {
        "name": "MAPE",
        "display_name": "Mean Absolute Percentage Error",
        "direction": MetricDirection.MINIMIZE,
        "task_types": [TaskType.REGRESSION],
    },
}

CLASSIFICATION_METRICS = {
    "Accuracy": {
        "name": "Accuracy",
        "display_name": "Accuracy",
        "direction": MetricDirection.MAXIMIZE,
        "task_types": [TaskType.CLASSIFICATION],
    },
    "Precision": {
        "name": "Precision",
        "display_name": "Precision",
        "direction": MetricDirection.MAXIMIZE,
        "task_types": [TaskType.CLASSIFICATION],
    },
    "Recall": {
        "name": "Recall",
        "display_name": "Recall",
        "direction": MetricDirection.MAXIMIZE,
        "task_types": [TaskType.CLASSIFICATION],
    },
    "F1": {
        "name": "F1",
        "display_name": "F1 Score",
        "direction": MetricDirection.MAXIMIZE,
        "task_types": [TaskType.CLASSIFICATION],
    },
    "ROC_AUC": {
        "name": "ROC_AUC",
        "display_name": "ROC AUC",
        "direction": MetricDirection.MAXIMIZE,
        "task_types": [TaskType.CLASSIFICATION],
    },
}

ALL_METRICS = {**REGRESSION_METRICS, **CLASSIFICATION_METRICS}


def get_metrics_for_task_type(task_type: str) -> dict:
    if task_type == TaskType.REGRESSION:
        return dict(REGRESSION_METRICS)
    elif task_type == TaskType.CLASSIFICATION:
        return dict(CLASSIFICATION_METRICS)
    return {}


def is_metric_supported(metric_name: str, task_type: str) -> bool:
    metrics = get_metrics_for_task_type(task_type)
    return metric_name in metrics


def get_metric_direction(metric_name: str) -> str:
    if metric_name in ALL_METRICS:
        return ALL_METRICS[metric_name]["direction"]
    return MetricDirection.MINIMIZE


def get_default_metrics(task_type: str) -> list:
    if task_type == TaskType.REGRESSION:
        return ["MAE", "MSE", "RMSE", "R2"]
    elif task_type == TaskType.CLASSIFICATION:
        return ["Accuracy", "Precision", "Recall", "F1"]
    return []
