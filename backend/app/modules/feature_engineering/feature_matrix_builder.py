import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


def _sanitize_column_names(columns: List[str]) -> Tuple[List[str], Dict[str, str]]:
    """Clean column names and resolve collisions.

    - Replaces spaces with underscores.
    - Appends _2, _3, ... suffix when sanitized names collide
      (e.g. "a b" and "a_b" both map to "a_b").

    Returns (cleaned_names, old_to_new_mapping).
    """
    seen: Dict[str, int] = {}
    cleaned: List[str] = []
    mapping: Dict[str, str] = {}

    for col in columns:
        clean = col.replace(" ", "_")
        if clean in seen:
            seen[clean] += 1
            clean = f"{clean}_{seen[clean]}"
        else:
            seen[clean] = 0
        cleaned.append(clean)
        mapping[col] = clean

    return cleaned, mapping


def _is_bool_like(series: pd.Series) -> bool:
    """Check whether an object-dtype column is semantically boolean.

    Recognises True / False / 0 / 1 and their string variants.
    NaN / None values are ignored during the check.
    """
    if not pd.api.types.is_object_dtype(series):
        return False
    dropped = series.dropna()
    if len(dropped) == 0:
        return False
    return bool(dropped.isin([True, False, 0, 1, "True", "False", "true", "false"]).all())


def _normalize_bool_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert boolean and boolean-like columns to float64 in-place.

    Handles three cases:
    - numpy bool_          → float64 (True→1.0, False→0.0)
    - pandas BooleanDtype  → float64 (True→1.0, False→0.0, pd.NA→NaN)
    - object with all-bool-like values → float64 (True→1.0, ..., else NaN)

    Returns the DataFrame (same object, modified in-place) for call chaining.
    """
    for col in df.columns:
        if pd.api.types.is_bool_dtype(df[col]):
            df[col] = df[col].astype(float)
        elif _is_bool_like(df[col]):
            df[col] = df[col].map(
                lambda v: 1.0 if v in (True, 1, "True", "true")
                else 0.0 if v in (False, 0, "False", "false")
                else float("nan")
            )
    return df


def _remap_feature_groups_columns(
    feature_groups: list, mapping: Dict[str, str]
) -> list:
    """Update feature_columns references inside feature_groups after renaming."""
    if not feature_groups or not mapping:
        return feature_groups or []
    for fg in feature_groups:
        if isinstance(fg, dict) and "feature_columns" in fg:
            fg_cols = fg["feature_columns"]
            if isinstance(fg_cols, list):
                fg["feature_columns"] = [mapping.get(c, c) for c in fg_cols]
    return feature_groups


def build_feature_matrix(
    raw_dataframe: pd.DataFrame,
    feature_dataframe: pd.DataFrame,
    target_column: str,
) -> pd.DataFrame:
    """Combine sample_id, features, and target into a standard feature matrix.

    Non-numeric columns (e.g., pymatgen Composition objects) are dropped
    because they cannot be serialized to parquet format.

    Boolean and boolean-like columns are normalised to float64 before
    the numeric filter so they are not incorrectly excluded.
    Column names are sanitised (spaces → underscores, deduplicated) at entry.
    """
    # --- 1. Sanitize column names ---
    old_cols = list(feature_dataframe.columns)
    new_cols, _ = _sanitize_column_names(old_cols)
    if old_cols != new_cols:
        feature_dataframe = feature_dataframe.copy()
        feature_dataframe.columns = new_cols

    # --- 2. Normalise boolean columns to float64 ---
    _normalize_bool_columns(feature_dataframe)

    # --- 3. Drop non-numeric columns that cannot be serialised ---
    numeric_cols = []
    for col in feature_dataframe.columns:
        if pd.api.types.is_numeric_dtype(feature_dataframe[col]):
            numeric_cols.append(col)

    if len(numeric_cols) < len(feature_dataframe.columns):
        dropped = set(feature_dataframe.columns) - set(numeric_cols)
        feature_dataframe = feature_dataframe[numeric_cols].copy()

    matrix = feature_dataframe.copy()

    # Add sample_id
    matrix.insert(0, "sample_id", [f"sample_{i}" for i in range(len(matrix))])

    # Add target column
    if target_column and target_column in raw_dataframe.columns:
        matrix[target_column] = raw_dataframe[target_column].values
    elif target_column:
        matrix[target_column] = np.nan

    return matrix


def get_feature_schema(
    feature_dataframe: pd.DataFrame,
    quality_result: dict,
    feature_groups: list = None,
) -> dict:
    """Build feature schema info from the feature dataframe and quality results.

    Applies the same column-name sanitisation and bool normalisation as
    build_feature_matrix so that metadata is consistent with the parquet.
    """
    df = feature_dataframe.copy()

    # --- 1. Sanitize column names ---
    old_cols = list(df.columns)
    new_cols, name_mapping = _sanitize_column_names(old_cols)
    if old_cols != new_cols:
        df.columns = new_cols

    # --- 2. Normalise boolean columns ---
    _normalize_bool_columns(df)

    # --- 3. Remap feature_groups column references ---
    fg = _remap_feature_groups_columns(feature_groups, name_mapping)

    numeric_count = 0
    categorical_count = 0
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_count += 1
        else:
            categorical_count += 1

    return {
        "feature_columns": list(df.columns),
        "feature_groups": fg,
        "numeric_feature_count": numeric_count,
        "categorical_feature_count": categorical_count,
        "constant_feature_count": len(quality_result.get("constant_features", [])),
        "all_missing_feature_count": len(quality_result.get("all_missing_features", [])),
    }
