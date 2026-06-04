import logging
import numpy as np
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def analyze_residuals(
    y_true,
    y_pred,
    X=None,
    feature_columns: Optional[List[str]] = None,
    n_bins: int = 30,
    n_error_segments: int = 5,
) -> Dict[str, Any]:
    """
    Compute residual statistics, histogram bins, and systematic error segments.

    Args:
        y_true: Ground-truth target values (array-like or pandas Series).
        y_pred: Predicted target values (array-like or pandas Series).
        X: Feature matrix (unused for basic stats, used for systematic error segments).
        feature_columns: List of feature names (reserved for future use).
        n_bins: Number of histogram bins for residual distribution.
        n_error_segments: Number of quantile-based segments for systematic error detection.

    Returns:
        Dict with residuals, predicted_values, r_squared, rmse, residual_mean,
        residual_std, histogram_bins, systematic_error_segments.
    """
    if y_true is None or y_pred is None:
        logger.info("Residual analysis skipped: y_true or y_pred is None.")
        return {
            "residuals": [],
            "predicted_values": [],
            "r_squared": 0.0,
            "rmse": 0.0,
            "residual_mean": 0.0,
            "residual_std": 0.0,
            "histogram_bins": [],
            "systematic_error_segments": [],
        }

    # Attempt index-based alignment when both are pandas Series
    aligned = False
    if HAS_PANDAS and isinstance(y_true, pd.Series) and isinstance(y_pred, pd.Series):
        common_idx = y_true.index.intersection(y_pred.index)
        n_common = len(common_idx)
        if n_common > 0:
            if n_common < min(len(y_true), len(y_pred)):
                logger.info(
                    "Aligning by index: %d common indices out of %d / %d",
                    n_common, len(y_true), len(y_pred),
                )
            yt = y_true.loc[common_idx].values.astype(float).flatten()
            yp = y_pred.loc[common_idx].values.astype(float).flatten()
            aligned = True
        else:
            logger.warning(
                "No common indices between y_true (%d) and y_pred (%d), falling back to positional alignment.",
                len(y_true), len(y_pred),
            )

    if not aligned:
        yt = np.asarray(y_true, dtype=float).flatten()
        yp = np.asarray(y_pred, dtype=float).flatten()
        min_len = min(len(yt), len(yp))
        if len(yt) != len(yp):
            logger.warning(
                "y_true (%d) and y_pred (%d) have different lengths, truncating to %d. "
                "This may misalign samples — predictions may not correspond to targets at the same row position.",
                len(yt), len(yp), min_len,
            )
        if min_len == 0:
            logger.warning("Residual analysis skipped: aligned array length is 0.")
            return {
                "residuals": [],
                "predicted_values": [],
                "r_squared": 0.0,
                "rmse": 0.0,
                "residual_mean": 0.0,
                "residual_std": 0.0,
                "histogram_bins": [],
                "systematic_error_segments": [],
            }
        yt = yt[:min_len]
        yp = yp[:min_len]

    residuals = (yt - yp).tolist()
    predicted_values = yp.tolist()
    r = np.asarray(residuals)

    # R-squared and RMSE
    ss_res = np.sum(r ** 2)
    ss_tot = np.sum((yt - np.mean(yt)) ** 2)
    r_squared = round(float(1.0 - ss_res / ss_tot), 4) if ss_tot > 0 else 0.0
    rmse = round(float(np.sqrt(np.mean(r ** 2))), 6)

    residual_mean = round(float(np.mean(r)), 6)
    residual_std = round(float(np.std(r)), 6)

    # Histogram bins
    hist, bin_edges = np.histogram(r, bins=n_bins)
    histogram_bins: List[Dict[str, Any]] = []
    for i in range(len(hist)):
        histogram_bins.append({
            "bin_start": round(float(bin_edges[i]), 6),
            "bin_end": round(float(bin_edges[i + 1]), 6),
            "count": int(hist[i]),
        })

    # Systematic error segments: partition predicted values into quantiles
    systematic_segments: List[Dict[str, Any]] = []
    try:
        abs_errors = np.abs(r)
        quantiles = np.percentile(
            yp, np.linspace(0, 100, n_error_segments + 1).tolist()
        )
        for qi in range(len(quantiles) - 1):
            if qi == len(quantiles) - 2:
                mask = (yp >= quantiles[qi]) & (yp <= quantiles[qi + 1])
            else:
                mask = (yp >= quantiles[qi]) & (yp < quantiles[qi + 1])
            if mask.sum() < 5:
                continue
            seg_mean_error = round(float(np.mean(abs_errors[mask])), 6)
            seg_n = int(mask.sum())
            systematic_segments.append({
                "segment_description": (
                    f"predicted in [{quantiles[qi]:.3g}, {quantiles[qi + 1]:.3g}]"
                ),
                "mean_absolute_error": seg_mean_error,
                "n_samples": seg_n,
            })
    except Exception as e:
        logger.warning("Systematic error detection failed: %s", str(e))

    n_segments = len(systematic_segments)
    logger.info(
        "Residual analysis computed: R^2=%.4f, RMSE=%.6f, residual_mean=%.6f, "
        "residual_std=%.6f, histogram_bins=%d, error_segments=%d.",
        r_squared, rmse, residual_mean, residual_std, len(histogram_bins), n_segments,
    )
    return {
        "residuals": residuals,
        "predicted_values": predicted_values,
        "r_squared": r_squared,
        "rmse": rmse,
        "residual_mean": residual_mean,
        "residual_std": residual_std,
        "histogram_bins": histogram_bins,
        "systematic_error_segments": systematic_segments,
    }
