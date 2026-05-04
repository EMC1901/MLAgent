"""Data Matrix Loader — loads model-ready features and constructs X/y."""

import os
import pandas as pd
from typing import Tuple
from app.modules.pipeline_execution.exceptions import TrainingDataLoadException


def load_model_ready_matrix(
    matrix_path: str,
    feature_columns: list,
    target_column: str,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Load the model-ready parquet and extract X, y.

    Args:
        matrix_path: Path to model_ready_features.parquet.
        feature_columns: List of feature column names.
        target_column: Target column name.

    Returns:
        (X, y) as DataFrame and Series.

    Raises:
        TrainingDataLoadException on any load/validation failure.
    """
    # Path safety
    if not matrix_path:
        raise TrainingDataLoadException("Model-ready matrix path is empty.")
    normalized = os.path.normpath(matrix_path)
    if ".." in normalized.split(os.sep):
        raise TrainingDataLoadException(
            f"Path traversal detected in matrix path: {matrix_path}"
        )

    if not os.path.exists(matrix_path):
        raise TrainingDataLoadException(
            f"Model-ready matrix not found at: {matrix_path}"
        )

    if not matrix_path.endswith(".parquet"):
        raise TrainingDataLoadException(
            f"Unsupported file format. Expected .parquet, got: {matrix_path}"
        )

    try:
        df = pd.read_parquet(matrix_path)
    except Exception as e:
        raise TrainingDataLoadException(f"Failed to read parquet: {e}")

    if df.empty:
        raise TrainingDataLoadException("Model-ready matrix is empty.")

    # Validate feature columns
    missing_features = [c for c in feature_columns if c not in df.columns]
    if missing_features:
        raise TrainingDataLoadException(
            f"Feature columns missing from data: {missing_features[:10]}"
        )

    # Validate target column
    if target_column not in df.columns:
        raise TrainingDataLoadException(
            f"Target column '{target_column}' not found in data. "
            f"Available columns: {list(df.columns)[:20]}"
        )

    # Check for NaN in target
    if df[target_column].isna().any():
        raise TrainingDataLoadException(
            "Target column contains NaN values. "
            "Data preprocessing should have handled this."
        )

    X = df[feature_columns].copy()
    y = df[target_column].copy()

    if len(X) != len(y):
        raise TrainingDataLoadException(
            f"X and y sample counts do not match: {len(X)} vs {len(y)}"
        )

    if len(X) == 0:
        raise TrainingDataLoadException("Data matrix has zero samples after feature/target extraction.")

    return X, y
