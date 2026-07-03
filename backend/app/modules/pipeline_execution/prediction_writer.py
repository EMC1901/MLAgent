"""Prediction Writer - saves validation and test predictions to parquet."""

import logging
import os
import pandas as pd
from app.modules.pipeline_execution.exceptions import TrainingArtifactSaveException

logger = logging.getLogger(__name__)


def save_predictions(
    y_true,
    y_pred,
    sample_indices,
    trial_id: str,
    pipeline_spec_id: str,
    fold_index: int,
    model_id: str,
    output_dir: str,
    task_type: str = "regression",
    y_pred_proba=None,
    class_labels=None,
    split: str = "validation",
    filename: str = None,
    extra_columns: dict = None,
) -> str:
    """Save prediction results as a parquet file.

    Returns:
        Path to the saved prediction file.
    """
    df = build_prediction_dataframe(
        y_true=y_true,
        y_pred=y_pred,
        sample_indices=sample_indices,
        trial_id=trial_id,
        pipeline_spec_id=pipeline_spec_id,
        fold_index=fold_index,
        model_id=model_id,
        task_type=task_type,
        y_pred_proba=y_pred_proba,
        class_labels=class_labels,
        split=split,
        extra_columns=extra_columns,
    )
    filename = filename or f"{trial_id}_fold_{fold_index}.parquet"
    return save_prediction_dataframe(df, output_dir, filename)


def build_prediction_dataframe(
    y_true,
    y_pred,
    sample_indices,
    trial_id: str,
    pipeline_spec_id: str,
    fold_index: int,
    model_id: str,
    task_type: str = "regression",
    y_pred_proba=None,
    class_labels=None,
    split: str = "validation",
    extra_columns: dict = None,
) -> pd.DataFrame:
    """Build prediction rows without writing them to disk."""
    try:
        import numpy as np
        y_true_vals = np.array(y_true).flatten()
        y_pred_vals = np.array(y_pred).flatten()
    except Exception as e:
        raise TrainingArtifactSaveException(f"Failed to convert predictions: {e}")

    df = pd.DataFrame({
        "sample_id": list(sample_indices),
        "trial_id": trial_id,
        "pipeline_spec_id": pipeline_spec_id,
        "fold_index": fold_index,
        "y_true": y_true_vals,
        "y_pred": y_pred_vals,
        "split": split,
        "model_id": model_id,
    })

    if extra_columns:
        for key, value in extra_columns.items():
            df[key] = value

    if task_type == "classification":
        df["y_pred_label"] = y_pred_vals
        if y_pred_proba is not None:
            try:
                proba_arr = np.array(y_pred_proba)
                if proba_arr.ndim == 1:
                    df["y_pred_proba"] = proba_arr
                elif proba_arr.ndim == 2:
                    for ci in range(proba_arr.shape[1]):
                        df[f"y_pred_proba_class_{ci}"] = proba_arr[:, ci]
            except Exception:
                pass
        if class_labels is not None:
            df["class_labels"] = str(list(class_labels))

    return df


def save_prediction_dataframe(df: pd.DataFrame, output_dir: str, filename: str) -> str:
    """Save a prediction DataFrame as parquet and return the file path."""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    try:
        df.to_parquet(filepath, index=False)
    except Exception as e:
        raise TrainingArtifactSaveException(f"Failed to write prediction parquet: {e}")

    return filepath