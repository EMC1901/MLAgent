import concurrent.futures
import logging
import time
import numpy as np
from typing import List, Dict, Any, Optional
from scipy.stats import pearsonr, spearmanr

logger = logging.getLogger(__name__)

_CORRELATION_TIMEOUT = 60  # seconds
_MAX_ROWS = 2000  # downsample to this many rows for stability + speed


def _diag(msg, *args):
    """Diagnostic log — uses logger.debug for unified log control."""
    formatted = msg % args if args else msg
    logger.debug("[ia-corr] %s", formatted)


def _compute_impl(X, y, feature_columns, top_n_features) -> Dict[str, Any]:
    if X is None or feature_columns is None or len(feature_columns) == 0:
        return {"feature_correlation_matrix": [], "feature_names": [],
                "target_correlations": [], "high_correlation_pairs": []}

    selected = [f for f in feature_columns if f in X.columns][:top_n_features]
    if not selected:
        return {"feature_correlation_matrix": [], "feature_names": [],
                "target_correlations": [], "high_correlation_pairs": []}

    # Downsample to avoid slow/memory-heavy correlation on large datasets
    n_rows = len(X)
    if n_rows > _MAX_ROWS:
        rng = np.random.RandomState(42)
        idx = rng.choice(n_rows, size=_MAX_ROWS, replace=False)
        X = X.iloc[idx]
        if y is not None:
            y = np.asarray(y)[idx]
        _diag("downsampled %d -> %d rows for correlation", n_rows, _MAX_ROWS)

    X_sub = X[selected].select_dtypes(include=["number"])
    selected = list(X_sub.columns)
    _diag("correlation: %d rows x %d numeric features", len(X_sub), len(selected))

    # Feature correlation matrix
    t0 = time.time()
    corr = X_sub.corr(method="pearson")
    corr_values = np.nan_to_num(corr.values, nan=0.0)
    matrix = corr_values.tolist()
    _diag("feature-feature corr matrix done in %.1fs", time.time() - t0)

    # Feature-target correlations
    t0 = time.time()
    target_correlations = []
    if y is not None:
        y_arr = np.asarray(y, dtype=float).flatten()
        min_len = min(len(y_arr), len(X_sub))
        y_arr = y_arr[:min_len]
        for i, f in enumerate(selected):
            if i % 10 == 0:
                _diag("target corr progress: %d/%d", i, len(selected))
            x_arr = X_sub[f].values[:min_len].astype(float)
            try:
                pr, _ = pearsonr(x_arr, y_arr)
                sr, _ = spearmanr(x_arr, y_arr)
            except Exception:
                pr, sr = 0.0, 0.0
            target_correlations.append({
                "feature_name": f,
                "pearson_r": round(float(pr), 4) if not np.isnan(pr) else 0.0,
                "spearman_rho": round(float(sr), 4) if not np.isnan(sr) else 0.0,
            })
        target_correlations.sort(key=lambda x: abs(x["pearson_r"]), reverse=True)
    _diag("target correlations done in %.1fs (%d features)", time.time() - t0, len(selected))

    # Highly correlated feature pairs
    high_pairs = []
    n = len(selected)
    for i in range(n):
        for j in range(i + 1, n):
            if abs(corr_values[i][j]) > 0.85:
                high_pairs.append({
                    "feature_1": selected[i], "feature_2": selected[j],
                    "correlation": round(float(corr_values[i][j]), 4),
                })
    high_pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
    high_pairs = high_pairs[:20]

    logger.info("Correlation analysis — %d features, %d target correlations, %d high-correlation pairs",
                 len(selected), len(target_correlations), len(high_pairs))
    return {
        "feature_correlation_matrix": matrix,
        "feature_names": selected,
        "target_correlations": target_correlations,
        "high_correlation_pairs": high_pairs,
    }


def compute_correlation_analysis(
    X, y, feature_columns: List[str], top_n_features: int = 30,
) -> Dict[str, Any]:
    """Compute correlation analysis with a timeout guard."""
    _diag("starting — rows=%d features=%d top_n=%d",
          len(X) if hasattr(X, "__len__") else 0,
          len(feature_columns) if feature_columns else 0,
          top_n_features)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            _compute_impl, X, y, feature_columns, top_n_features,
        )
        try:
            result = future.result(timeout=_CORRELATION_TIMEOUT)
            return result
        except concurrent.futures.TimeoutError:
            logger.error("Correlation analysis timed out after %ds", _CORRELATION_TIMEOUT)
            _diag("TIMEOUT after %ds — returning partial fallback", _CORRELATION_TIMEOUT)
        except Exception as e:
            logger.error("Correlation analysis failed: %s", str(e))
            _diag("FAILED: %s", str(e))

    # Fallback on timeout or failure
    return {
        "feature_correlation_matrix": [],
        "feature_names": [],
        "target_correlations": [],
        "high_correlation_pairs": [],
        "error": f"Correlation analysis did not complete within {_CORRELATION_TIMEOUT}s",
    }

