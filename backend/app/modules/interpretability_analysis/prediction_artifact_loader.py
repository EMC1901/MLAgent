import os
import logging
from typing import Optional, List
import pandas as pd

from app.modules.interpretability_analysis.exceptions import PredictionArtifactLoadException

logger = logging.getLogger(__name__)


def load_prediction_artifact(prediction_path: str) -> pd.DataFrame:
    if not os.path.exists(prediction_path):
        raise PredictionArtifactLoadException(f"Prediction artifact not found at: {prediction_path}")

    allowed_dir = os.path.normpath("/app/artifacts")
    normalized = os.path.normpath(prediction_path)
    if ".." in normalized or not normalized.startswith(allowed_dir):
        raise PredictionArtifactLoadException(
            f"Prediction artifact path is outside allowed directory: {prediction_path}"
        )

    try:
        if prediction_path.endswith(".parquet"):
            df = pd.read_parquet(normalized)
        elif prediction_path.endswith(".csv"):
            df = pd.read_csv(normalized)
        else:
            df = pd.read_parquet(normalized)
    except Exception as e:
        raise PredictionArtifactLoadException(f"Failed to load prediction artifact: {str(e)}")

    logger.info("Loaded prediction artifact from %s: %d rows", prediction_path, len(df))
    return df


def load_all_prediction_artifacts(paths: List[str]) -> pd.DataFrame:
    dfs = []
    for p in paths:
        df = load_prediction_artifact(p)
        dfs.append(df)
    if dfs:
        combined = pd.concat(dfs, ignore_index=True)
        logger.info("Combined %d prediction artifacts: %d total rows", len(paths), len(combined))
        return combined
    return pd.DataFrame()
