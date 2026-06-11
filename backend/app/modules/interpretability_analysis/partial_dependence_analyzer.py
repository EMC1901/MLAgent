import logging
import time
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Shared worker cap for PDP parallelism.
# 1D and 2D run sequentially, so no nesting — a single pool is alive at a time.
_PDP_MAX_WORKERS = 2


def compute_partial_dependence(
    model,
    X: Optional[pd.DataFrame],
    feature_columns: List[str],
    top_n_features: int = 10,
    top_n_interactions: int = 2,
    grid_resolution: int = 20,
) -> Dict[str, Any]:
    """
    Compute 1D PDP for top N features and 2D PDP for top feature pairs.

    Args:
        model: Trained model with a predict method (or sklearn-compatible).
        X: Feature matrix as a pandas DataFrame.
        feature_columns: Ordered list of feature column names.
        top_n_features: Max number of features for 1D PDP.
        top_n_interactions: Max number of feature pairs for 2D PDP.
        grid_resolution: Number of grid points for 1D PDP.

    Returns:
        Dict with "pdp_1d" (list of dicts) and "pdp_2d" (list of dicts).
    """
    t0 = time.time()
    logger.info("PDP — top_n_features=%d top_n_interactions=%d grid=%d",
                 top_n_features, top_n_interactions, grid_resolution)
    try:
        from sklearn.inspection import partial_dependence
    except ImportError:
        logger.warning("sklearn.inspection not available; PDP computation skipped.")
        return {"pdp_1d": [], "pdp_2d": []}

    if X is None or len(feature_columns) == 0:
        logger.info("PDP skipped: no feature matrix or no feature columns provided.")
        return {"pdp_1d": [], "pdp_2d": []}

    feature_indices = []
    valid_feature_names = []
    for f in feature_columns:
        if f in X.columns:
            feature_indices.append(list(X.columns).index(f))
            valid_feature_names.append(f)
        else:
            logger.debug("Feature '%s' not found in X.columns; skipping for PDP.", f)

    if not feature_indices:
        logger.warning("No valid feature indices found in X for PDP.")
        return {"pdp_1d": [], "pdp_2d": []}

    # sklearn partial_dependence misbehaves with integer-typed columns
    # (numpy percentile rounding → malformed grid arrays → PiB allocations).
    X_pdp = X.astype({col: "float64" for col in X.select_dtypes(include=["integer", "bool"]).columns})

    # Filter out features too narrow for PDP grid construction
    low_var = []
    filtered_idx = []
    filtered_names = []
    for idx, name in zip(feature_indices, valid_feature_names):
        col_vals = X_pdp[name].dropna()
        if col_vals.nunique() < 2:
            low_var.append(name)
            continue
        if pd.api.types.is_numeric_dtype(X_pdp[name]):
            q5 = col_vals.quantile(0.05)
            q95 = col_vals.quantile(0.95)
            denom = max(abs(q95), abs(q5), 1e-10)
            if (q95 - q5) / denom < 1e-6:
                low_var.append(name)
                continue
        filtered_idx.append(idx)
        filtered_names.append(name)
    if low_var:
        logger.info("PDP: skipping %d low-variance features: %s",
                     len(low_var), low_var[:10])
    feature_indices = filtered_idx
    valid_feature_names = filtered_names

    if not feature_indices:
        logger.warning("PDP skipped: all top features filtered out (low variance).")
        return {"pdp_1d": [], "pdp_2d": []}

    n_features = min(top_n_features, len(feature_indices))
    selected_idx = feature_indices[:n_features]
    selected_names = valid_feature_names[:n_features]

    # Map X column index → feature name for reliable lookup in 2D PDP.
    col_idx_to_name = dict(zip(feature_indices, valid_feature_names))

    # ── 1D PDP ──────────────────────────────────────────────────────────
    pdp_1d: List[Dict[str, Any]] = []
    t0_1d = time.time()
    if selected_idx:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def _compute_1d_feature(feature_spec):
            fidx, fname = feature_spec
            t_feat = time.time()
            result = partial_dependence(
                model, X_pdp, features=[fidx],
                kind="average", grid_resolution=grid_resolution,
            )
            item = {
                "feature_name": fname,
                "grid_values": result["grid_values"][0].tolist(),
                "pdp_values": result["average"][0].tolist(),
            }
            logger.debug("PDP 1D [%s] done in %.1fs",
                         fname, time.time() - t_feat)
            return item

        feature_specs = list(zip(selected_idx, selected_names))
        results = {}
        with ThreadPoolExecutor(max_workers=_PDP_MAX_WORKERS) as pool:
            futures = {pool.submit(_compute_1d_feature, fs): fs for fs in feature_specs}
            for future in as_completed(futures):
                fidx, fname = futures[future]
                try:
                    results[fidx] = future.result()
                except Exception as e:
                    logger.warning(
                        "1D PDP feature failed (idx=%d name=%s): %s",
                        fidx, fname, str(e),
                    )

        for fidx, _ in feature_specs:
            if fidx in results:
                pdp_1d.append(results[fidx])
    logger.info("PDP 1D done — %d features in %.1fs", len(pdp_1d), time.time() - t0_1d)

    # ── 2D PDP ──────────────────────────────────────────────────────────
    pdp_2d: List[Dict[str, Any]] = []
    n_pairs = min(top_n_interactions, n_features * (n_features - 1) // 2)
    if n_pairs > 0 and n_features >= 2:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        pair_indices = _select_top_pairs(selected_idx, n_features, n_pairs)
        grid_2d = max(grid_resolution // 2, 5)

        def _compute_2d_pdp(pair):
            i1, i2 = pair
            pd_pair = partial_dependence(
                model, X_pdp, features=[(i1, i2)], kind="average",
                grid_resolution=grid_2d,
            )
            # grid_values is [(grid_i1, grid_i2)] for a single pair
            grids = pd_pair["grid_values"][0]
            grid1 = grids[0].tolist()
            grid2 = grids[1].tolist()
            matrix = pd_pair["average"][0].tolist()
            f1 = col_idx_to_name.get(i1, f"f{i1}")
            f2 = col_idx_to_name.get(i2, f"f{i2}")
            return {
                "feature_1": f1, "feature_2": f2,
                "grid_1": grid1, "grid_2": grid2, "pdp_matrix": matrix,
            }

        results = {}
        with ThreadPoolExecutor(max_workers=min(n_pairs, _PDP_MAX_WORKERS)) as pool:
            futures = {pool.submit(_compute_2d_pdp, p): p for p in pair_indices}
            for future in as_completed(futures):
                pair = futures[future]
                try:
                    results[pair] = future.result()
                except Exception as e:
                    logger.warning("2D PDP for pair (%d, %d) failed: %s",
                                   pair[0], pair[1], str(e))
        for pair in pair_indices:
            if pair in results:
                pdp_2d.append(results[pair])

    logger.info("PDP done — %d 1D + %d 2D plots in %.1fs",
                 len(pdp_1d), len(pdp_2d), time.time() - t0)
    return {"pdp_1d": pdp_1d, "pdp_2d": pdp_2d}


def _select_top_pairs(
    selected_idx: List[int],
    n_features: int,
    n_pairs: int,
) -> List[Tuple[int, int]]:
    """Select top feature pairs for 2D PDP. Prioritizes the first few features."""
    pairs = []
    max_first = min(3, n_features)
    for i in range(max_first):
        for j in range(i + 1, n_features):
            if len(pairs) >= n_pairs:
                return pairs
            pairs.append((selected_idx[i], selected_idx[j]))
    return pairs
