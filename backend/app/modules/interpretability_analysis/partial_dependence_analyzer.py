import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


def compute_partial_dependence(
    model,
    X: Optional[pd.DataFrame],
    feature_columns: List[str],
    top_n_features: int = 10,
    top_n_interactions: int = 3,
    grid_resolution: int = 30,
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
    import time
    logger.info("PDP — top_n_features=%d top_n_interactions=%d grid=%d",
                 top_n_features, top_n_interactions, grid_resolution)
    t0 = time.time()
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

    n_features = min(top_n_features, len(feature_indices))
    selected_idx = feature_indices[:n_features]
    selected_names = valid_feature_names[:n_features]

    # sklearn partial_dependence misbehaves with integer-typed columns
    # (numpy percentile rounding → malformed grid arrays → PiB allocations).
    # Convert the selected columns to float64 before calling.
    X_pdp = X.astype({col: "float64" for col in X.select_dtypes(include=["integer"]).columns})

    pdp_1d: List[Dict[str, Any]] = []
    try:
        pd_result = partial_dependence(
            model, X_pdp, features=selected_idx, kind="average", grid_resolution=grid_resolution
        )
        for i, (name, idx) in enumerate(zip(selected_names, selected_idx)):
            grid = pd_result["grid_values"][i].tolist()
            values = pd_result["average"][i].tolist()
            pdp_1d.append({
                "feature_name": name,
                "grid_values": grid,
                "pdp_values": values,
            })
    except Exception as e:
        logger.warning("1D PDP computation failed: %s", str(e))

    # 2D PDP for top feature pairs
    pdp_2d: List[Dict[str, Any]] = []
    n_pairs = min(top_n_interactions, n_features * (n_features - 1) // 2)
    if n_pairs > 0 and n_features >= 2:
        pair_indices = _select_top_pairs(selected_idx, n_features, n_pairs)
        for (i1, i2) in pair_indices:
            try:
                pd_pair = partial_dependence(
                    model, X_pdp, features=[(i1, i2)], kind="average",
                    grid_resolution=max(10, grid_resolution // 2),
                )
                grid1 = pd_pair["grid_values"][0][0].tolist()
                grid2 = pd_pair["grid_values"][0][1].tolist()
                matrix = pd_pair["average"][0].tolist()
                f1_name = feature_columns[i1] if i1 < len(feature_columns) else f"f{i1}"
                f2_name = feature_columns[i2] if i2 < len(feature_columns) else f"f{i2}"
                pdp_2d.append({
                    "feature_1": f1_name,
                    "feature_2": f2_name,
                    "grid_1": grid1,
                    "grid_2": grid2,
                    "pdp_matrix": matrix,
                })
            except Exception as e:
                logger.warning("2D PDP for pair (%d, %d) failed: %s", i1, i2, str(e))

    logger.info("PDP done — %d 1D + %d 2D plots in %.1fs",
                 len(pdp_1d), len(pdp_2d), time.time() - t0)
    return {"pdp_1d": pdp_1d, "pdp_2d": pdp_2d}


def _select_top_pairs(
    selected_idx: List[int],
    n_features: int,
    n_pairs: int,
) -> List[Tuple[int, int]]:
    """
    Select the top feature pairs for 2D PDP from the given index list.
    Prioritizes the first few features.
    """
    pairs = []
    max_first = min(3, n_features)
    for i in range(max_first):
        for j in range(i + 1, n_features):
            if len(pairs) >= n_pairs:
                return pairs
            pairs.append((selected_idx[i], selected_idx[j]))
    return pairs
