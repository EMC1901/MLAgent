import pandas as pd
import numpy as np


def build_feature_matrix(
    raw_dataframe: pd.DataFrame,
    feature_dataframe: pd.DataFrame,
    target_column: str,
) -> pd.DataFrame:
    """Combine sample_id, features, and target into a standard feature matrix.

    Non-numeric columns (e.g., pymatgen Composition objects) are dropped
    because they cannot be serialized to parquet format.
    """

    # Drop non-numeric columns that cannot be serialized (e.g., Composition objects)
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
    """Build feature schema info from the feature dataframe and quality results."""
    numeric_count = 0
    categorical_count = 0
    for col in feature_dataframe.columns:
        if pd.api.types.is_numeric_dtype(feature_dataframe[col]):
            numeric_count += 1
        else:
            categorical_count += 1

    return {
        "feature_columns": list(feature_dataframe.columns),
        "feature_groups": feature_groups or [],
        "numeric_feature_count": numeric_count,
        "categorical_feature_count": categorical_count,
        "constant_feature_count": len(quality_result.get("constant_features", [])),
        "all_missing_feature_count": len(quality_result.get("all_missing_features", [])),
    }
