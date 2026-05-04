import logging
import pandas as pd
import numpy as np
from typing import List
from app.modules.feature_preprocessing.enums import FeatureDropReason

logger = logging.getLogger(__name__)

# Columns to always drop (pymatgen intermediate objects, etc.)
KNOWN_INTERMEDIATE_COLUMNS = {
    "_pymatgen_composition",
    "_pymatgen_structure",
}


def validate_target_column(df: pd.DataFrame, target_column: str) -> bool:
    """Check that the target column exists in the dataframe."""
    return target_column in df.columns


def identify_invalid_features(df: pd.DataFrame, feature_columns: List[str]) -> List[dict]:
    """Identify non-numeric/object/datetime/list/dict columns that cannot be used for modeling.

    Returns list of {name, reason, action}.
    """
    dropped = []

    for col in feature_columns:
        if col not in df.columns:
            continue

        series = df[col]

        # 1. Known intermediate columns (pymatgen objects etc.)
        if col in KNOWN_INTERMEDIATE_COLUMNS:
            dropped.append({
                "name": col,
                "reason": FeatureDropReason.NON_NUMERIC_OBJECT,
                "action": "dropped",
            })
            continue

        # 2. Object dtype
        if series.dtype == object:
            dropped.append({
                "name": col,
                "reason": FeatureDropReason.NON_NUMERIC_OBJECT,
                "action": "dropped",
            })
            continue

        # 3. Datetime columns
        if pd.api.types.is_datetime64_any_dtype(series):
            dropped.append({
                "name": col,
                "reason": FeatureDropReason.NON_NUMERIC_OBJECT,
                "action": "dropped",
            })
            continue

        # 4. Check for dict/list values in object columns that snuck through
        if series.dtype == object:
            try:
                sample_vals = series.dropna().head(5)
                for v in sample_vals:
                    if isinstance(v, (dict, list, tuple, set)):
                        dropped.append({
                            "name": col,
                            "reason": FeatureDropReason.NON_NUMERIC_OBJECT,
                            "action": "dropped",
                        })
                        break
            except Exception:
                pass

    return dropped


def identify_all_missing_features(df: pd.DataFrame, feature_columns: List[str]) -> List[dict]:
    """Identify features where all values are NaN."""
    dropped = []
    n_samples = len(df)

    for col in feature_columns:
        if col not in df.columns:
            continue
        missing_count = df[col].isnull().sum()
        if missing_count == n_samples:
            dropped.append({
                "name": col,
                "reason": FeatureDropReason.ALL_MISSING,
                "action": "dropped",
            })

    return dropped


def identify_constant_features(df: pd.DataFrame, feature_columns: List[str]) -> List[dict]:
    """Identify features with only one unique non-null value."""
    dropped = []

    for col in feature_columns:
        if col not in df.columns:
            continue
        vals = df[col].dropna()
        if vals.nunique() <= 1:
            dropped.append({
                "name": col,
                "reason": FeatureDropReason.CONSTANT,
                "action": "dropped",
            })

    return dropped


def identify_high_missing_features(
    df: pd.DataFrame, feature_columns: List[str], max_missing_ratio: float = 0.5,
) -> List[dict]:
    """Identify features where missing ratio exceeds threshold."""
    dropped = []
    n_samples = len(df)
    if n_samples == 0:
        return dropped

    for col in feature_columns:
        if col not in df.columns:
            continue
        missing_ratio = df[col].isnull().sum() / n_samples
        if missing_ratio > max_missing_ratio:
            dropped.append({
                "name": col,
                "reason": FeatureDropReason.HIGH_MISSING,
                "action": "dropped",
            })

    return dropped


def handle_invalid_inf_values(df: pd.DataFrame, feature_columns: List[str]) -> dict:
    """Replace inf/-inf with NaN and identify columns that become too sparse."""
    processed_columns = []
    dropped_columns = []
    n_samples = len(df)

    for col in feature_columns:
        if col not in df.columns:
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue

        has_inf = np.isinf(df[col].dropna()).any()
        if has_inf:
            df[col] = df[col].replace([np.inf, -np.inf], np.nan)
            # Check if too many values became NaN after replacing inf
            new_missing_ratio = df[col].isnull().sum() / max(n_samples, 1)
            if new_missing_ratio > 0.5:
                dropped_columns.append({
                    "name": col,
                    "reason": FeatureDropReason.INVALID_INF,
                    "action": "dropped",
                })
            else:
                processed_columns.append(col)
        else:
            processed_columns.append(col)

    return {
        "processed_columns": processed_columns,
        "dropped_columns": dropped_columns,
        "dataframe": df,
    }
