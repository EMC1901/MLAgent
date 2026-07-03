import os
import logging
from typing import Optional, List
import pandas as pd

from app.modules.interpretability_analysis.exceptions import PredictionArtifactLoadException

logger = logging.getLogger(__name__)

PREDICTION_VALUE_COLUMNS = {
    "y_true",
    "y_pred",
    "prediction",
    "pred",
    "predicted",
    "y_pred_label",
}


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
        combined = pd.concat(dfs, ignore_index=True, sort=False)
        combined = _index_by_sample_id(combined)
        logger.info(
            "Combined %d prediction artifacts: %d total rows (index_source=%s)",
            len(paths),
            len(combined),
            combined.attrs.get("index_source", "dataframe_index"),
        )
        return combined
    return pd.DataFrame()


def _index_by_sample_id(df: pd.DataFrame) -> pd.DataFrame:
    """Use prediction sample_id as row index when available.

    Prediction artifacts are written with index=False, so the parquet DataFrame
    index is not the training sample id. Downstream alignment must use the
    explicit sample_id column instead.
    """
    if "sample_id" not in df.columns:
        logger.warning(
            "Prediction artifacts do not contain sample_id; falling back to DataFrame index."
        )
        df.attrs["index_source"] = "dataframe_index"
        return df

    duplicate_count = int(df["sample_id"].duplicated().sum())
    if duplicate_count:
        logger.warning(
            "Prediction artifacts contain %d duplicate sample_id rows; aggregating "
            "numeric prediction columns by mean and metadata columns by first value.",
            duplicate_count,
        )
        aggregations = {}
        for col in df.columns:
            if col == "sample_id":
                continue
            if col in PREDICTION_VALUE_COLUMNS and pd.api.types.is_numeric_dtype(df[col]):
                aggregations[col] = "mean"
            else:
                aggregations[col] = "first"
        df = df.groupby("sample_id", as_index=False, sort=False).agg(aggregations)

    df = df.set_index("sample_id", drop=False)
    df.attrs["index_source"] = "sample_id"
    return df
