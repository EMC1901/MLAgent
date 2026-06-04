"""Fold Runner — trains a model on a single fold and generates predictions."""

import logging
import time
import traceback
import concurrent.futures
import numpy as np
import pandas as pd
from app.modules.pipeline_execution.model_factory import create_model
from app.modules.pipeline_execution.prediction_writer import save_predictions
from app.modules.pipeline_execution.training_artifact_manager import save_model
from app.modules.pipeline_execution.schemas import FoldResultDTO

logger = logging.getLogger(__name__)

_DEFAULT_FOLD_TIMEOUT = 30  # seconds per fold


class FoldTimeoutError(Exception):
    """Raised when model.fit() exceeds the per-fold time limit."""
    pass


def _fit_with_timeout(model, X_train, y_train, fit_kwargs, timeout_seconds):
    """Run model.fit() in a daemon thread with a hard timeout.

    sklearn models don't support interruption natively, so we run fit in a
    separate thread.  If it exceeds *timeout_seconds* the fold is marked
    failed and the thread is abandoned (it will eventually finish on its own
    but we don't wait for it).
    """
    result = {"done": False, "exception": None}

    def _fit():
        try:
            model.fit(X_train, y_train, **fit_kwargs)
            result["done"] = True
        except Exception as exc:
            result["exception"] = exc

    thread = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = thread.submit(_fit)
    try:
        future.result(timeout=timeout_seconds)
    except concurrent.futures.TimeoutError:
        thread.shutdown(wait=False)
        raise FoldTimeoutError(
            f"model.fit() exceeded {timeout_seconds}s timeout "
            f"(model={type(model).__name__}, samples={len(X_train)})"
        )
    finally:
        thread.shutdown(wait=False)

    if result["exception"]:
        raise result["exception"]


def run_fold(
    X_train,
    y_train,
    X_val,
    y_val,
    train_indices,
    val_indices,
    fold_index: int,
    model_id: str,
    task_type: str,
    params: dict,
    trial_id: str,
    pipeline_spec_id: str,
    exec_dir: str,
    save_predictions_flag: bool = True,
    save_model_flag: bool = True,
    fold_timeout_seconds: int = _DEFAULT_FOLD_TIMEOUT,
    fold_pipeline_spec=None,
) -> FoldResultDTO:
    """Execute a single fold: fold preproc (if spec), train, predict, save.

    Receives pre-sliced X_train/y_train/X_val/y_val from trial_runner to
    avoid repeated .iloc operations across folds.

    Returns:
        FoldResultDTO with results and artifact paths.
    """
    started = time.time()
    result = FoldResultDTO(
        fold_index=fold_index,
        train_size=len(X_train),
        validation_size=len(X_val),
        status="running",
    )

    try:
        # Phase A: Fold-level preprocessing (fit on train only)
        if fold_pipeline_spec is not None and fold_pipeline_spec.operations:
            from app.modules.pipeline_execution.fold_preprocessor import (
                FoldPipelineExecutor, FoldPreprocessingError,
            )
            n_ops = len(fold_pipeline_spec.operations)
            logger.debug("fold %d — applying fold preprocessing: %d ops ...", fold_index, n_ops)
            t0_prep = time.time()
            try:
                preprocessor = FoldPipelineExecutor(fold_pipeline_spec)
                X_train = preprocessor.fit_transform(
                    X_train, y_train, trial_id=trial_id, fold_index=fold_index,
                )
                X_val = preprocessor.transform(
                    X_val, trial_id=trial_id, fold_index=fold_index,
                )
                logger.debug("fold %d — fold preprocessing done in %.1fs (train=%d,%d val=%d,%d)",
                      fold_index, time.time() - t0_prep,
                      len(X_train), len(X_train.columns),
                      len(X_val), len(X_val.columns))
            except FoldPreprocessingError:
                raise
            except Exception as e:
                logger.error(
                    "fold %d — fold preprocessing FAILED: %s | X_train.shape=%s params=%s",
                    fold_index, e, X_train.shape,
                    [(op.capability_id, op.parameters) for op in fold_pipeline_spec.operations],
                )
                raise FoldPreprocessingError(
                    f"Fold preprocessing failed at fold {fold_index}: {e}",
                    trial_id=trial_id, fold_index=fold_index,
                ) from e

        logger.info("fold %d — training %s on %d samples (%d features)",
                     fold_index, model_id, len(X_train), len(X_train.columns))

        # Create and train model
        try:
            model = create_model(model_id, task_type, params)
        except Exception as e:
            logger.error("fold %d — model creation FAILED: %s=%s params=%s — %s",
                          fold_index, model_id, model_id, params, e)
            raise

        t0_fit = time.time()
        _fit_kwargs = {}
        if hasattr(model, "fit") and _supports_eval_set(type(model).__name__):
            _fit_kwargs["eval_set"] = [(X_val, y_val)]
            _fit_kwargs["verbose"] = False

        try:
            _fit_with_timeout(model, X_train, y_train, _fit_kwargs, fold_timeout_seconds)
        except FoldTimeoutError:
            logger.error(
                "fold %d — model.fit TIMEOUT (>%ds): model=%s X.shape=%s params=%s",
                fold_index, fold_timeout_seconds, model_id, X_train.shape, params,
            )
            raise
        except Exception as e:
            logger.error(
                "fold %d — model.fit FAILED: model=%s X.shape=%s y.shape=%s params=%s — %s",
                fold_index, model_id, X_train.shape, y_train.shape, params, e,
            )
            raise
        fit_dur = time.time() - t0_fit

        logger.info("fold %d — fit done in %.1fs", fold_index, fit_dur)

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
        result.error_message = f"{e}\n{traceback.format_exc()}"
        logger.debug("fold %d FAILED: %s", fold_index, str(e))

    result.duration_seconds = round(time.time() - started, 3)
    return result


_MODELS_WITH_EVAL_SET = {
    "XGBRegressor", "XGBClassifier", "XGBModel",
    "LGBMRegressor", "LGBMClassifier",
}


def _supports_eval_set(model_class_name: str) -> bool:
    """Check if the model's fit() accepts an eval_set kwarg for early stopping."""
    return model_class_name in _MODELS_WITH_EVAL_SET


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
