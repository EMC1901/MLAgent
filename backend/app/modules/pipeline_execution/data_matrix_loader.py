"""Data Matrix Loader — loads model-ready features and constructs X/y."""

import logging
import os
import pandas as pd
from typing import Optional, Tuple
from app.modules.pipeline_execution.exceptions import TrainingDataLoadException

logger = logging.getLogger(__name__)


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

    logger.debug("loading parquet from %s ...", matrix_path)
    try:
        df = pd.read_parquet(matrix_path)
    except Exception as e:
        raise TrainingDataLoadException(f"Failed to read parquet: {e}")
    logger.debug("parquet loaded: shape=(%d, %d)", df.shape[0], df.shape[1])

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


def load_intermediate_matrix(
    matrix_path: str,
    feature_columns: list,
    target_column: str,
) -> tuple:
    """Load intermediate (post-global-phase) feature matrix.

    Same as load_model_ready_matrix but with clearer naming for the
    two-phase fold-safe flow. The matrix at this path has only been
    through dataset_profile_only operations — fold_only operations
    are applied later inside each CV fold.
    """
    return load_model_ready_matrix(matrix_path, feature_columns, target_column)


def resolve_fold_pipeline_spec_path(matrix_path: str) -> Optional[str]:
    """Given the model-ready matrix path, derive the fold_pipeline_spec.json path.

    Returns the path if it exists, None otherwise.
    """
    import os
    if not matrix_path:
        return None
    artifact_dir = os.path.dirname(matrix_path)
    spec_path = os.path.join(artifact_dir, "fold_pipeline_spec.json")
    if os.path.exists(spec_path):
        return spec_path
    return None
