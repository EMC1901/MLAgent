"""Fold Runner — trains a model on a single fold and generates predictions."""

import time
import numpy as np
import pandas as pd
from app.modules.pipeline_execution.model_factory import create_model
from app.modules.pipeline_execution.prediction_writer import save_predictions
from app.modules.pipeline_execution.training_artifact_manager import save_model
from app.modules.pipeline_execution.schemas import FoldResultDTO


def run_fold(
    X,
    y,
    train_indices: np.ndarray,
    val_indices: np.ndarray,
    fold_index: int,
    model_id: str,
    task_type: str,
    params: dict,
    trial_id: str,
    pipeline_spec_id: str,
    exec_dir: str,
    save_predictions_flag: bool = True,
    save_model_flag: bool = True,
) -> FoldResultDTO:
    """Execute a single fold: train model, predict, save artifacts.

    Returns:
        FoldResultDTO with results and artifact paths.
    """
    started = time.time()
    result = FoldResultDTO(
        fold_index=fold_index,
        train_size=len(train_indices),
        validation_size=len(val_indices),
        status="running",
    )

    try:
        # Subset data
        X_train = X.iloc[train_indices] if hasattr(X, "iloc") else X[train_indices]
        y_train = y.iloc[train_indices] if hasattr(y, "iloc") else y[train_indices]
        X_val = X.iloc[val_indices] if hasattr(X, "iloc") else X[val_indices]
        y_val = y.iloc[val_indices] if hasattr(y, "iloc") else y[val_indices]

        # Create and train model
        model = create_model(model_id, task_type, params)
        model.fit(X_train, y_train)

        # Predict
        y_pred = model.predict(X_val)

        # For classification, also get probabilities if available
        y_pred_proba = None
        class_labels = None
        if task_type == "classification":
            if hasattr(model, "predict_proba"):
                try:
                    y_pred_proba = model.predict_proba(X_val)
                    if hasattr(model, "classes_"):
                        class_labels = model.classes_.tolist()
                except Exception:
                    pass

        # Compute basic raw metrics (for reference only; final metrics in Metric Evaluation)
        raw_metrics = _compute_raw_metrics(y_val, y_pred, task_type)

        # Save prediction artifact
        pred_path = None
        if save_predictions_flag:
            pred_dir = f"{exec_dir}/predictions"
            pred_path = save_predictions(
                y_true=y_val,
                y_pred=y_pred,
                sample_indices=val_indices.tolist() if hasattr(val_indices, "tolist") else list(val_indices),
                trial_id=trial_id,
                pipeline_spec_id=pipeline_spec_id,
                fold_index=fold_index,
                model_id=model_id,
                output_dir=pred_dir,
                task_type=task_type,
                y_pred_proba=y_pred_proba,
                class_labels=class_labels,
            )

        # Save model artifact
        model_path = None
        if save_model_flag:
            model_path = save_model(model, trial_id, fold_index, exec_dir)

        result.status = "completed"
        result.prediction_artifact_path = pred_path
        result.model_artifact_path = model_path
        result.raw_metric_values = raw_metrics

    except Exception as e:
        result.status = "failed"
        result.error_message = str(e)

    result.duration_seconds = round(time.time() - started, 3)
    return result


def _compute_raw_metrics(y_true, y_pred, task_type: str) -> dict:
    """Compute raw metrics for reference. Final metrics are in Metric Evaluation."""
    metrics = {}
    try:
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        yt = np.array(y_true).flatten()
        yp = np.array(y_pred).flatten()
        metrics["mae"] = float(mean_absolute_error(yt, yp))
        metrics["mse"] = float(mean_squared_error(yt, yp))
        metrics["rmse"] = float(mean_squared_error(yt, yp, squared=False) if hasattr(mean_squared_error, "__kwdefaults__") else np.sqrt(metrics["mse"]))
        metrics["r2"] = float(r2_score(yt, yp))
    except Exception:
        pass

    if task_type == "classification":
        try:
            from sklearn.metrics import accuracy_score
            acc = float(accuracy_score(np.array(y_true).flatten(), np.array(y_pred).flatten()))
            metrics["accuracy"] = acc
        except Exception:
            pass

    return metrics
