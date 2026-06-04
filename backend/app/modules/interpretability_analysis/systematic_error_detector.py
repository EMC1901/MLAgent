import logging
import numpy as np
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def detect_systematic_errors(
    X,
    y_true,
    y_pred,
    feature_columns: Optional[List[str]] = None,
    top_n_segments: int = 5,
    n_quantiles: int = 5,
) -> List[Dict[str, Any]]:
    """
    Detect systematic error patterns by segmenting data on feature values.

    For the top features, splits data into quantiles and checks if error rates
    differ significantly across segments (indicating the model performs worse
    in certain regions of feature space).
    """
    if X is None or y_true is None or y_pred is None or not feature_columns:
        return []

    yt = np.asarray(y_true, dtype=float).flatten()
    yp = np.asarray(y_pred, dtype=float).flatten()
    min_len = min(len(yt), len(yp), len(X))
    yt = yt[:min_len]
    yp = yp[:min_len]
    abs_errors = np.abs(yt - yp)

    # Focus on top important features (first 15)
    candidates = [f for f in feature_columns[:15] if f in X.columns]
    if not candidates:
        return []

    segments = []
    for feature in candidates:
        x_vals = X[feature].values[:min_len].astype(float)
        if np.std(x_vals) < 1e-10:
            continue

        try:
            quantile_edges = np.percentile(x_vals, np.linspace(0, 100, n_quantiles + 1))
            for qi in range(n_quantiles):
                low, high = quantile_edges[qi], quantile_edges[qi + 1]
                if qi == n_quantiles - 1:
                    mask = (x_vals >= low) & (x_vals <= high)
                else:
                    mask = (x_vals >= low) & (x_vals < high)
                if mask.sum() < 5:
                    continue
                seg_mean = round(float(np.mean(abs_errors[mask])), 6)
                seg_std = round(float(np.std(abs_errors[mask])), 6)
                overall_mean = float(np.mean(abs_errors))
                ratio = round(seg_mean / overall_mean, 3) if overall_mean > 0 else 1.0
                segments.append({
                    "feature_name": feature,
                    "quantile": qi,
                    "value_range": f"[{low:.3g}, {high:.3g}]",
                    "n_samples": int(mask.sum()),
                    "mean_abs_error": seg_mean,
                    "error_ratio_to_overall": ratio,
                })
        except Exception as e:
            logger.debug("Systematic error segment for %s failed: %s", feature, str(e))

    # Sort by error ratio descending (worst segments first)
    segments.sort(key=lambda s: s["error_ratio_to_overall"], reverse=True)

    # Deduplicate: keep only the worst quantile per feature
    seen_features = set()
    top_segments = []
    for seg in segments:
        if seg["feature_name"] not in seen_features:
            seen_features.add(seg["feature_name"])
            top_segments.append(seg)
        if len(top_segments) >= top_n_segments:
            break

    # Add possible cause hints
    for seg in top_segments:
        ratio = seg["error_ratio_to_overall"]
        if ratio > 2.0:
            seg["possible_cause"] = (
                f"Model performs significantly worse in this region "
                f"({ratio:.1f}x higher error than average). "
                "Consider: insufficient training data in this range, extrapolation, "
                "or missing feature interactions."
            )
        elif ratio > 1.5:
            seg["possible_cause"] = (
                f"Model error is elevated ({ratio:.1f}x) in this region. "
                "May indicate mild extrapolation or non-linear effects."
            )
        else:
            seg["possible_cause"] = "Error is near or below average in this region."

    logger.info("Systematic error detection — %d total segments, %d top results",
                 len(segments), len(top_segments))
    return top_segments
