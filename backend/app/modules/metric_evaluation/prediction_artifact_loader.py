import os
from typing import List, Dict, Any
import pandas as pd
from app.modules.metric_evaluation.exceptions import PredictionArtifactLoadException


REQUIRED_COLUMNS = [
    "sample_id",
    "trial_id",
    "pipeline_spec_id",
    "fold_index",
    "y_true",
    "y_pred",
    "model_id",
]

ALLOWED_BASE_DIR = os.path.normpath("/app/artifacts/training")


def _validate_path_safety(filepath: str) -> None:
    if ".." in filepath:
        raise PredictionArtifactLoadException(
            f"Invalid prediction artifact path (contains '..'): {filepath}"
        )
    normalized = os.path.normpath(filepath)
    if not normalized.startswith(ALLOWED_BASE_DIR):
        raise PredictionArtifactLoadException(
            f"Prediction artifact path outside allowed directory: {filepath}"
        )
    if not os.path.exists(normalized):
        raise PredictionArtifactLoadException(
            f"Prediction artifact file not found: {filepath}"
        )
    if not normalized.endswith(".parquet"):
        raise PredictionArtifactLoadException(
            f"Prediction artifact must be a parquet file: {filepath}"
        )


def load_prediction_artifact(filepath: str) -> pd.DataFrame:
    _validate_path_safety(filepath)
    try:
        df = pd.read_parquet(filepath)
    except Exception as e:
        raise PredictionArtifactLoadException(
            f"Failed to read prediction parquet '{filepath}': {str(e)}"
        )

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise PredictionArtifactLoadException(
            f"Prediction file '{filepath}' missing required columns: {missing_cols}"
        )

    if len(df) == 0:
        raise PredictionArtifactLoadException(
            f"Prediction file '{filepath}' is empty."
        )

    if not pd.api.types.is_numeric_dtype(df["y_true"]):
        raise PredictionArtifactLoadException(
            f"Column 'y_true' in '{filepath}' is not numeric."
        )
    if not pd.api.types.is_numeric_dtype(df["y_pred"]):
        raise PredictionArtifactLoadException(
            f"Column 'y_pred' in '{filepath}' is not numeric."
        )

    if df["y_true"].isna().any() or df["y_pred"].isna().any():
        raise PredictionArtifactLoadException(
            f"Prediction file '{filepath}' contains NaN values in y_true or y_pred."
        )
    if (df["y_true"].isin([float("inf"), float("-inf")]).any() or
            df["y_pred"].isin([float("inf"), float("-inf")]).any()):
        raise PredictionArtifactLoadException(
            f"Prediction file '{filepath}' contains infinite values in y_true or y_pred."
        )

    return df


def load_prediction_artifacts(
    prediction_artifact_paths: List[str],
) -> Dict[str, pd.DataFrame]:
    frames: Dict[str, pd.DataFrame] = {}
    for path in prediction_artifact_paths:
        df = load_prediction_artifact(path)
        frames[path] = df
    return frames


def build_prediction_frame_map(
    prediction_frames: Dict[str, pd.DataFrame],
    trial_results: List[Dict[str, Any]],
) -> Dict[str, Dict[int, pd.DataFrame]]:
    """Build a map of trial_id -> {fold_index -> DataFrame}."""
    trial_fold_map: Dict[str, Dict[int, pd.DataFrame]] = {}

    trial_to_path: Dict[str, List[str]] = {}
    for t in trial_results:
        tid = t.get("trial_id", "")
        ppath = t.get("prediction_artifact_path", "")
        if tid and ppath:
            trial_to_path.setdefault(tid, []).append(ppath)

    for path, df in prediction_frames.items():
        for tid in df["trial_id"].unique():
            if tid not in trial_fold_map:
                trial_fold_map[tid] = {}
            for fold_idx in df["fold_index"].unique():
                fold_df = df[(df["trial_id"] == tid) & (df["fold_index"] == fold_idx)]
                if len(fold_df) > 0:
                    trial_fold_map[tid][int(fold_idx)] = fold_df

    return trial_fold_map
