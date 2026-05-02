import logging
import pandas as pd
import numpy as np
from typing import List

logger = logging.getLogger(__name__)


class FeatureQualityResult(dict):
    """Typed wrapper for quality check results."""
    pass


def check_feature_quality(
    feature_df: pd.DataFrame,
    target_series: pd.Series = None,
    max_dimension: int = 2000,
    max_missing_ratio: float = 0.5,
    feature_groups: list = None,
) -> dict:
    """Check feature matrix quality and return a comprehensive quality dict.

    Per PRD §11.13, checks include:
      - Empty/null checks
      - Duplicate feature names
      - Missing values (total + per-column)
      - All-missing features
      - Constant features (single unique value)
      - Near-constant features (variance < 1e-8)
      - All-zero features
      - Non-numeric features
      - Infinite values
      - High-NaN-ratio features (>max_missing_ratio)
      - High-dimensionality warning (>max_dimension)
      - Feature-group-level quality summary
    """
    warnings = []
    errors = []

    if feature_df is None or feature_df.empty:
        return {
            "is_valid_feature_matrix": False,
            "missing_values": {"total_missing": 0, "columns_with_missing": []},
            "constant_features": [],
            "near_constant_features": [],
            "all_zero_features": [],
            "all_missing_features": [],
            "invalid_features": [],
            "dropped_features": [],
            "failed_samples": [],
            "per_group_summary": {},
            "warnings": ["Feature dataframe is empty."],
            "errors": ["FEATURE_MATRIX_INVALID: Feature dataframe is None or empty."],
        }

    n_samples, n_features = feature_df.shape

    # 1. Feature count check
    if n_features == 0:
        errors.append("FEATURE_MATRIX_INVALID: Feature count is 0.")
    if n_samples == 0:
        errors.append("FEATURE_MATRIX_INVALID: Sample count is 0.")

    # 2. High dimensionality check
    if n_features > max_dimension:
        warnings.append(
            f"HIGH_DIMENSIONAL_FEATURE_MATRIX: {n_features} features "
            f"(threshold: {max_dimension})."
        )

    # 3. Duplicate feature names
    dupes = feature_df.columns[feature_df.columns.duplicated()].tolist()
    if dupes:
        errors.append(f"FEATURE_NAME_CONFLICT: Duplicate feature column names: {dupes}")

    # 4. Missing values
    missing_per_col = feature_df.isnull().sum()
    total_missing = int(missing_per_col.sum())
    cols_with_missing = missing_per_col[missing_per_col > 0].index.tolist()

    # 5. All-missing features (100% NaN)
    all_missing = missing_per_col[missing_per_col == n_samples].index.tolist()

    # 6. Constant features (single unique value, excluding NaN)
    constant_features = []
    near_constant_features = []
    all_zero_features = []
    for col in feature_df.columns:
        vals = feature_df[col].dropna()
        n_unique = vals.nunique()
        if n_unique <= 1:
            constant_features.append(col)
        elif n_unique <= 3 and len(vals) > 0:
            try:
                if vals.var() < 1e-8:
                    near_constant_features.append(col)
            except Exception:
                pass
        if len(vals) > 0 and vals.max() == 0 and vals.min() == 0:
            all_zero_features.append(col)

    # 7. Non-numeric features
    invalid_features = []
    for col in feature_df.columns:
        if not pd.api.types.is_numeric_dtype(feature_df[col]):
            invalid_features.append(col)

    # 8. Infinite values
    inf_cols = []
    for col in feature_df.columns:
        if pd.api.types.is_numeric_dtype(feature_df[col]):
            if np.isinf(feature_df[col].dropna()).any():
                inf_cols.append(col)
    if inf_cols:
        warnings.append(f"Columns with infinite values: {inf_cols}")

    # 9. High-NaN-ratio features (>max_missing_ratio)
    high_missing = missing_per_col[
        missing_per_col > n_samples * max_missing_ratio
    ].index.tolist()
    if high_missing:
        warnings.append(
            f"HIGH_FEATURE_MISSING_RATIO: Columns with >{int(max_missing_ratio * 100)}% "
            f"missing values: {high_missing}"
        )

    # 10. Broad constant/near-constant warnings
    if constant_features:
        warnings.append(f"CONSTANT_FEATURES_DROPPED: {len(constant_features)} constant features.")
    if near_constant_features:
        warnings.append(
            f"Near-constant features (variance < 1e-8): {near_constant_features}"
        )

    # 11. Dropped features (all-missing + constant)
    dropped = list(set(all_missing + constant_features))

    # 12. Feature-group-level summary
    per_group_summary = {}
    if feature_groups:
        for group in feature_groups:
            gname = group.get("group_name", "unknown")
            gcols = group.get("feature_columns", [])
            gcols_in_df = [c for c in gcols if c in feature_df.columns]
            if not gcols_in_df:
                per_group_summary[gname] = {"status": "no_columns_in_matrix"}
                continue
            g_missing = int(feature_df[gcols_in_df].isnull().sum().sum())
            g_n_samples = len(feature_df)
            perf = group.get("status", "unknown")
            per_group_summary[gname] = {
                "status": perf,
                "n_features_in_matrix": len(gcols_in_df),
                "total_missing": g_missing,
                "missing_ratio": round(g_missing / max(g_n_samples * len(gcols_in_df), 1), 4),
            }

    # 13. Determine validity
    is_valid = True
    if errors:
        is_valid = False

    return {
        "is_valid_feature_matrix": is_valid,
        "missing_values": {
            "total_missing": total_missing,
            "columns_with_missing": cols_with_missing,
        },
        "constant_features": constant_features,
        "near_constant_features": near_constant_features,
        "all_zero_features": all_zero_features,
        "all_missing_features": all_missing,
        "invalid_features": invalid_features,
        "dropped_features": dropped,
        "failed_samples": [],
        "per_group_summary": per_group_summary,
        "warnings": warnings,
        "errors": errors,
    }
