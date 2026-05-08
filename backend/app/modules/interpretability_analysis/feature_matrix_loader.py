import os
import logging
from typing import List, Tuple, Optional
import pandas as pd

from app.modules.interpretability_analysis.exceptions import FeatureMatrixLoadException

logger = logging.getLogger(__name__)


def load_feature_matrix(
    matrix_path: str,
    feature_columns: List[str],
    target_column: Optional[str] = None,
    max_samples: Optional[int] = None,
) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
    if not os.path.exists(matrix_path):
        raise FeatureMatrixLoadException(f"Feature matrix not found at: {matrix_path}")

    allowed_dir = os.path.normpath("/app/artifacts")
    normalized = os.path.normpath(matrix_path)
    if ".." in normalized or not normalized.startswith(allowed_dir):
        raise FeatureMatrixLoadException(
            f"Feature matrix path is outside allowed directory: {matrix_path}"
        )

    try:
        if matrix_path.endswith(".parquet"):
            df = pd.read_parquet(normalized)
        elif matrix_path.endswith(".csv"):
            df = pd.read_csv(normalized)
        else:
            raise FeatureMatrixLoadException(f"Unsupported matrix format: {matrix_path}")

    except Exception as e:
        raise FeatureMatrixLoadException(f"Failed to load feature matrix: {str(e)}")

    # If feature_columns is empty, derive all numeric columns (except target) from the matrix
    fc = list(feature_columns) if feature_columns else []
    if not fc:
        fc = [
            c for c in df.select_dtypes(include=["number"]).columns
            if c != target_column
        ]
        if not fc:
            raise FeatureMatrixLoadException("No numeric feature columns found in matrix.")
        logger.info("Derived %d feature columns from matrix.", len(fc))

    missing_features = [c for c in fc if c not in df.columns]
    if missing_features:
        raise FeatureMatrixLoadException(
            f"Feature columns missing from matrix: {', '.join(missing_features[:10])}"
        )

    X = df[fc].copy()

    for col in X.select_dtypes(include=["object", "category"]).columns:
        logger.warning("Dropping non-numeric column: %s", col)
        X = X.drop(columns=[col])
    feature_columns_final = [c for c in X.columns]

    y = None
    if target_column and target_column in df.columns:
        y = df[target_column].copy()

    if max_samples and len(X) > max_samples:
        sampled_indices = X.sample(n=max_samples, random_state=42).index
        X = X.loc[sampled_indices]
        if y is not None:
            y = y.loc[sampled_indices]
        logger.info("Sampled %d rows from %d total", max_samples, len(df))

    logger.info(
        "Loaded feature matrix: %d samples, %d features", len(X), len(feature_columns_final)
    )
    return X, y
