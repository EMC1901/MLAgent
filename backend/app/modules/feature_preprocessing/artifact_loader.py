import os
import logging
import pandas as pd
from app.modules.feature_preprocessing.exceptions import (
    FeatureArtifactLoadException,
    FeatureArtifactMissingException,
)


logger = logging.getLogger(__name__)


def load_raw_feature_matrix(file_path: str) -> dict:
    """Load the raw feature matrix artifact from the feature engineering output.

    Returns a dict with dataframe, n_samples, n_columns, candidate_feature_columns.
    """
    logger.debug("loading feature matrix from: %s", file_path)
    if not file_path:
        raise FeatureArtifactMissingException("Feature artifact file path is empty.")

    if not os.path.exists(file_path):
        raise FeatureArtifactMissingException(
            f"Feature artifact file not found: {file_path}"
        )

    try:
        if file_path.endswith(".parquet"):
            df = pd.read_parquet(file_path)
        elif file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            raise FeatureArtifactLoadException(
                f"Unsupported artifact format: {file_path}"
            )
    except Exception as e:
        logger.debug("FAILED to load feature artifact: %s", e)
        raise FeatureArtifactLoadException(
            f"Failed to load feature artifact: {e}"
        )

    if df is None or df.empty:
        raise FeatureArtifactLoadException("Loaded feature matrix is empty.")

    # Identify target column (typically the last column after sample_id)
    columns = list(df.columns)
    target_col = None
    candidate_features = []

    for col in columns:
        if col == "sample_id":
            continue
        candidate_features.append(col)

    # The target is typically the last non-sample_id column in the feature matrix
    if len(candidate_features) > 1:
        target_col = candidate_features[-1]
        candidate_features = candidate_features[:-1]
    elif len(candidate_features) == 1:
        target_col = candidate_features[0]
        candidate_features = []

    result = {
        "dataframe": df,
        "n_samples": len(df),
        "n_columns": len(columns),
        "columns": columns,
        "target_column": target_col,
        "candidate_feature_columns": candidate_features,
    }
    logger.debug("loaded: %d samples, %d total cols, %d candidate features, target=%s",
          result["n_samples"], result["n_columns"], len(candidate_features), target_col)
    return result
