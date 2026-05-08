import logging
from typing import Any, List, Optional
import numpy as np
import pandas as pd

from app.modules.interpretability_analysis.schemas import LocalExplanationItem

logger = logging.getLogger(__name__)


def build_local_explanations(
    X: pd.DataFrame,
    y_true: Optional[pd.Series],
    y_pred: Optional[np.ndarray],
    feature_columns: List[str],
    shap_values: Optional[np.ndarray] = None,
    max_explanations: int = 10,
) -> List[LocalExplanationItem]:
    items: List[LocalExplanationItem] = []

    n_total = len(X)
    if n_total == 0:
        return items

    sample_indices = _select_representative_samples(X, y_pred, max_explanations)
    shap_available = shap_values is not None and len(shap_values) >= max(sample_indices) + 1

    for idx in sample_indices:
        if idx >= n_total:
            continue

        sample_id = str(X.index[idx]) if hasattr(X, "index") else str(idx)
        true_val = float(y_true.iloc[idx]) if y_true is not None and idx < len(y_true) else None
        pred_val = float(y_pred[idx]) if y_pred is not None and idx < len(y_pred) else None
        error = float(abs(true_val - pred_val)) if true_val is not None and pred_val is not None else None

        top_pos = []
        top_neg = []
        local_shap: dict = {}

        if shap_available and idx < len(shap_values):
            sample_shap = shap_values[idx]
            nf = min(len(sample_shap), len(feature_columns))
            shap_pairs = list(zip(feature_columns[:nf], sample_shap[:nf]))
            shap_pairs.sort(key=lambda x: x[1], reverse=True)

            top_pos = [
                {"feature": name, "contribution": float(val)}
                for name, val in shap_pairs[:3] if val > 0
            ]
            top_neg = [
                {"feature": name, "contribution": float(val)}
                for name, val in shap_pairs[-3:] if val < 0
            ]
            top_neg.sort(key=lambda x: x["contribution"])
            local_shap = {name: float(val) for name, val in shap_pairs}

        summary_parts = []
        if top_pos:
            summary_parts.append(f"Top positive: {', '.join(f['feature'] for f in top_pos)}")
        if top_neg:
            summary_parts.append(f"Top negative: {', '.join(f['feature'] for f in top_neg)}")
        summary = "; ".join(summary_parts) if summary_parts else "No SHAP data available."

        items.append(LocalExplanationItem(
            sample_id=sample_id,
            y_true=true_val,
            y_pred=pred_val,
            prediction_error=error,
            top_positive_features=top_pos,
            top_negative_features=top_neg,
            local_shap_values=local_shap,
            local_explanation_summary=summary,
        ))

    logger.info("Built %d local explanations out of %d samples.", len(items), n_total)
    return items


def _select_representative_samples(
    X: pd.DataFrame,
    y_pred: Optional[np.ndarray] = None,
    max_samples: int = 10,
) -> List[int]:
    n = len(X)
    if n <= max_samples:
        return list(range(n))

    indices = list(range(n))
    selected: List[int] = [n // 2]
    step = n // max_samples
    for i in range(max_samples - 1):
        pos = (i + 1) * step
        if pos < n:
            selected.append(pos)
    selected = selected[:max_samples]

    if y_pred is not None and len(y_pred) == n:
        preds = list(y_pred)
        if len(preds) > max_samples:
            min_idx = int(np.argmin(preds))
            max_idx = int(np.argmax(preds))
            for idx in (min_idx, max_idx):
                if idx not in selected:
                    selected.append(idx)
            selected = selected[:max_samples]

    return sorted(set(selected))
