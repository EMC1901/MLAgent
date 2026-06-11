import logging
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

logger = logging.getLogger(__name__)


def _canonical_metric_name(name: str) -> str:
    """Normalise metric name: replace hyphens with underscores so that
    'ROC-AUC' and 'ROC_AUC' resolve to the same canonical key."""
    return name.replace("-", "_")


def _safe_divide(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return a / b


def calculate_metric(y_true: np.ndarray, y_pred: np.ndarray, metric_name: str, y_score: np.ndarray = None) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    if y_score is not None:
        y_score = np.asarray(y_score, dtype=float)

    metric_name = _canonical_metric_name(metric_name)

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
    elif metric_name == "ROC_AUC":
        if y_score is None:
            logger.warning("ROC_AUC requires y_score (predict_proba), got None — returning NaN")
            return float("nan")
        unique_classes = np.unique(y_true)
        if len(unique_classes) > 2:
            logger.warning(
                "Multi-class ROC-AUC (n_classes=%d) is not yet supported — returning NaN",
                len(unique_classes),
            )
            return float("nan")
        try:
            from sklearn.metrics import roc_auc_score
            return float(roc_auc_score(y_true, y_score))
        except Exception as exc:
            logger.warning("ROC_AUC calculation failed: %s", exc)
            return float("nan")
    else:
        raise MetricNotSupportedException(
            f"Metric '{metric_name}' is not supported."
        )


def calculate_all_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    task_type: str,
    metric_names: Optional[list] = None,
    y_score: np.ndarray = None,
) -> Dict[str, float]:
    if metric_names is None:
        from app.modules.metric_evaluation.metric_registry import get_default_metrics
        metric_names = get_default_metrics(task_type)

    results = {}
    for name in metric_names:
        canonical = _canonical_metric_name(name)
        if not is_metric_supported(canonical, task_type):
            continue
        try:
            value = calculate_metric(y_true, y_pred, canonical, y_score=y_score)
            results[canonical] = value if np.isfinite(value) else float("nan")
        except Exception:
            results[canonical] = float("nan")
    return results
