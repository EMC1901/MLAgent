import logging
from typing import Any, List, Optional
import numpy as np
import pandas as pd

from app.modules.interpretability_analysis.schemas import HighErrorSampleAnalysis

logger = logging.getLogger(__name__)


def analyze_high_error_samples(
    X: pd.DataFrame,
    y_true: Optional[pd.Series],
    y_pred: Optional[np.ndarray],
    feature_columns: List[str],
    shap_values: Optional[np.ndarray] = None,
    max_samples: int = 10,
) -> List[HighErrorSampleAnalysis]:
    items: List[HighErrorSampleAnalysis] = []

    if y_true is None or y_pred is None or len(y_true) != len(y_pred):
        logger.warning("Cannot analyze high-error samples: missing or mismatched predictions.")
        return items

    # Defensive: X and y must be row-aligned. If not, this is a caller bug.
    n_x = len(X)
    if len(y_true) != n_x:
        logger.warning(
            "High-error analysis: X has %d rows but y_true has %d — data not aligned. "
            "Align y_true/y_pred to X indices before calling this function.",
            n_x, len(y_true),
        )
        # Best-effort: take the intersection by positional overlap
        n = min(n_x, len(y_true))
        y_true = y_true.iloc[:n]
        y_pred = np.asarray(y_pred)[:n]
        if shap_values is not None and len(shap_values) > n:
            shap_values = shap_values[:n]
        if n == 0:
            return items

    errors = np.abs(np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float))
    n = len(errors)

    top_n = min(max_samples, n)
    if top_n == 0:
        return items
    high_error_indices = np.argsort(errors)[::-1][:top_n]

    for rank, idx in enumerate(high_error_indices, start=1):
        abs_err = float(errors[idx])
        rel_err = float(abs_err / (abs(y_true.iloc[idx]) + 1e-10)) if y_true.iloc[idx] != 0 else None

        factors = []
        if rel_err and rel_err > 1.0:
            factors.append("Relative error exceeds 100% - prediction may be unusable for this sample.")
        if abs_err > np.median(errors) * 3:
            factors.append("Error is an outlier (>3x median) - possible anomalous sample.")
        if shap_values is not None and idx < len(shap_values):
            sample_shap = np.abs(shap_values[idx])
            if len(sample_shap) > 0:
                top_shap_idx = int(np.argmax(sample_shap))
                if top_shap_idx < len(feature_columns):
                    factors.append(
                        f"Feature '{feature_columns[top_shap_idx]}' has unusually high SHAP contribution for this sample."
                    )

        pattern_parts = []
        if len(feature_columns) > 0 and idx < len(X):
            sample = X.iloc[idx]
            extremes = []
            for col in feature_columns[:5]:
                if col in sample.index:
                    val = sample[col]
                    col_vals = X[col].dropna()
                    if len(col_vals) > 1:
                        pct = (col_vals < val).mean()
                        if pct > 0.95:
                            extremes.append(f"{col} is in top {((1-pct)*100):.0f}%")
                        elif pct < 0.05:
                            extremes.append(f"{col} is in bottom {((pct)*100):.0f}%")
            if extremes:
                pattern_parts.append("Extreme values: " + ", ".join(extremes))

        pattern_summary = "; ".join(pattern_parts) if pattern_parts else "No unusual feature patterns detected."

        review_suggestion = (
            f"Sample with absolute error {abs_err:.4f}. "
            f"Review if this sample has data quality issues, is an outlier, "
            f"or if its feature values are outside the training distribution."
        )

        items.append(HighErrorSampleAnalysis(
            sample_id=str(X.index[idx]) if hasattr(X, "index") else str(idx),
            absolute_error=abs_err,
            relative_error=rel_err,
            error_rank=rank,
            possible_error_factors=factors if factors else ["No specific error factors identified."],
            feature_pattern_summary=pattern_summary,
            review_suggestion=review_suggestion,
        ))

    logger.info("Analyzed %d high-error samples.", len(items))
    return items
