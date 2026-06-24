"""Final external test runner.

Refits the selected trial on the train pool and predicts the external test set
exactly once. This artifact is the source for external-test performance charts.
"""

import logging
import os
import time
from typing import Optional

from app.modules.pipeline_execution.model_factory import create_model
from app.modules.pipeline_execution.prediction_writer import save_predictions

logger = logging.getLogger(__name__)


def run_final_external_test(
    X_train_pool,
    y_train_pool,
    X_test,
    y_test,
    test_indices,
    best_trial,
    task_type: str,
    exec_dir: str,
    fold_pipeline_spec=None,
) -> dict:
    """Refit the selected trial on train pool and predict external test data."""
    started = time.time()
    trial_id = _trial_attr(best_trial, "trial_id")
    pipeline_spec_id = _trial_attr(best_trial, "pipeline_spec_id")
    model_id = _trial_attr(best_trial, "model_id")
    params = _trial_attr(best_trial, "params") or {}

    if not trial_id or not model_id:
        raise ValueError("best_trial must include trial_id and model_id.")

    X_fit = X_train_pool
    X_eval = X_test

    if fold_pipeline_spec is not None and getattr(fold_pipeline_spec, "operations", None):
        from app.modules.pipeline_execution.fold_preprocessor import FoldPipelineExecutor

        preprocessor = FoldPipelineExecutor(fold_pipeline_spec)
        X_fit = preprocessor.fit_transform(
            X_train_pool,
            y_train_pool,
            trial_id=trial_id,
            fold_index=-1,
        )
        X_eval = preprocessor.transform(
            X_test,
            trial_id=trial_id,
            fold_index=-1,
        )

    logger.info(
        "final external test: refitting %s on %d train-pool samples, testing %d samples",
        model_id,
        len(X_fit),
        len(X_eval),
    )
    model = create_model(model_id, task_type, params)
    model.fit(X_fit, y_train_pool)
    y_pred = model.predict(X_eval)

    y_pred_proba = None
    class_labels = None
    if task_type == "classification" and hasattr(model, "predict_proba"):
        try:
            y_pred_proba = model.predict_proba(X_eval)
            if hasattr(model, "classes_"):
                class_labels = model.classes_.tolist()
        except Exception:
            pass

    pred_dir = os.path.join(exec_dir, "predictions")
    pred_path = save_predictions(
        y_true=y_test,
        y_pred=y_pred,
        sample_indices=(
            test_indices.tolist() if hasattr(test_indices, "tolist") else list(test_indices)
        ),
        trial_id=trial_id,
        pipeline_spec_id=pipeline_spec_id,
        fold_index=-1,
        model_id=model_id,
        output_dir=pred_dir,
        task_type=task_type,
        y_pred_proba=y_pred_proba,
        class_labels=class_labels,
        split="test",
        filename="final_external_test_predictions.parquet",
        extra_columns={
            "is_final_external_test": True,
            "prediction_source": "final_external_test",
        },
    )

    return {
        "enabled": True,
        "status": "completed",
        "prediction_artifact_path": pred_path,
        "trial_id": trial_id,
        "pipeline_spec_id": pipeline_spec_id,
        "model_id": model_id,
        "train_pool_size": len(X_train_pool),
        "external_test_size": len(X_test),
        "duration_seconds": round(time.time() - started, 3),
    }


def select_best_trial_for_external_test(
    trial_results: list,
    primary_metric: Optional[str],
    metric_direction: str = "minimize",
):
    """Select a completed trial using the PipelineExecution raw CV metrics."""
    completed = [t for t in trial_results if _trial_attr(t, "status") == "completed"]
    if not completed:
        return None

    key = _raw_metric_key(primary_metric)
    scored = []
    for trial in completed:
        metrics = _trial_attr(trial, "raw_metric_values") or {}
        value = metrics.get(key) if key else None
        if value is not None:
            scored.append((float(value), trial))

    if scored:
        reverse = metric_direction == "maximize"
        scored.sort(key=lambda item: item[0], reverse=reverse)
        return scored[0][1]

    return completed[0]


def _raw_metric_key(primary_metric: Optional[str]) -> Optional[str]:
    if not primary_metric:
        return None
    key = str(primary_metric).strip().lower()
    key = key.replace("-", "_").replace(" ", "_")
    aliases = {
        "mean_absolute_error": "mae",
        "root_mean_squared_error": "rmse",
        "r_squared": "r2",
        "r2_score": "r2",
        "accuracy_score": "accuracy",
    }
    key = aliases.get(key, key)
    return f"mean_{key}"


def _trial_attr(trial, name: str):
    if isinstance(trial, dict):
        return trial.get(name)
    return getattr(trial, name, None)