import numpy as np
from typing import Dict, Optional
from app.modules.metric_evaluation.metric_registry import (
    is_metric_supported,
    get_metrics_for_task_type,
)
from app.modules.metric_evaluation.exceptions import (
    MetricNotSupportedException,
    MetricCalculationException,
)


def _safe_divide(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return a / b


def calculate_metric(y_true: np.ndarray, y_pred: np.ndarray, metric_name: str) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    if metric_name == "MAE":
        return float(np.mean(np.abs(y_true - y_pred)))
    elif metric_name == "MSE":
        return float(np.mean((y_true - y_pred) ** 2))
    elif metric_name == "RMSE":
        return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    elif metric_name == "R2":
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        if ss_tot == 0:
            return 0.0
        return float(1 - ss_res / ss_tot)
    elif metric_name == "MAPE":
        mask = y_true != 0
        if mask.sum() == 0:
            return float("nan")
        return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)
    elif metric_name == "Accuracy":
        return float(np.mean(y_true == y_pred))
    elif metric_name == "Precision":
        tp = np.sum((y_pred == 1) & (y_true == 1))
        fp = np.sum((y_pred == 1) & (y_true == 0))
        denom = tp + fp
        return float(tp / denom) if denom > 0 else 0.0
    elif metric_name == "Recall":
        tp = np.sum((y_pred == 1) & (y_true == 1))
        fn = np.sum((y_pred == 0) & (y_true == 1))
        denom = tp + fn
        return float(tp / denom) if denom > 0 else 0.0
    elif metric_name == "F1":
        precision = calculate_metric(y_true, y_pred, "Precision")
        recall = calculate_metric(y_true, y_pred, "Recall")
        if precision + recall == 0:
            return 0.0
        return float(2 * precision * recall / (precision + recall))
    else:
        raise MetricNotSupportedException(
            f"Metric '{metric_name}' is not supported."
        )


def calculate_all_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    task_type: str,
    metric_names: Optional[list] = None,
) -> Dict[str, float]:
    if metric_names is None:
        from app.modules.metric_evaluation.metric_registry import get_default_metrics
        metric_names = get_default_metrics(task_type)

    results = {}
    for name in metric_names:
        if not is_metric_supported(name, task_type):
            continue
        try:
            value = calculate_metric(y_true, y_pred, name)
            results[name] = value if np.isfinite(value) else float("nan")
        except Exception:
            results[name] = float("nan")
    return results
