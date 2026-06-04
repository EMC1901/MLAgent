"""Trial Runner — executes a single trial across all folds with optional parallelism."""

import logging
import time
import concurrent.futures
from datetime import datetime
from app.modules.pipeline_execution.fold_runner import run_fold
from app.modules.pipeline_execution.schemas import TrialResultDTO, FoldResultDTO

logger = logging.getLogger(__name__)


def run_trial(
    X,
    y,
    trial_plan: dict,
    validation_splits: list,
    task_type: str,
    exec_dir: str,
    save_predictions_flag: bool = True,
    save_model_flag: bool = True,
    parallel_folds: bool = True,
    fold_timeout_seconds: int = 30,
    fold_pipeline_spec=None,
) -> TrialResultDTO:
    """Execute one trial: iterate over folds, train, and collect results.

    Args:
        X: Feature matrix (DataFrame).
        y: Target vector (Series).
        trial_plan: Dict from execution_planner with trial metadata and params.
        validation_splits: List of split dicts from validation_splitter.
        task_type: 'regression' or 'classification'.
        exec_dir: Artifact output directory.
        save_predictions_flag: Whether to persist prediction files.
        save_model_flag: Whether to persist model files.
        parallel_folds: Whether to run folds in parallel via ThreadPoolExecutor.

    Returns:
        TrialResultDTO with fold results and artifact paths.
    """
    started = time.time()
    trial_id = trial_plan["trial_id"]
    pipeline_spec_id = trial_plan["pipeline_spec_id"]
    model_id = trial_plan["model_id"]
    params = trial_plan.get("params", {})

    result = TrialResultDTO(
        trial_id=trial_id,
        pipeline_spec_id=pipeline_spec_id,
        pipeline_run_id=f"prun_{pipeline_spec_id}",
        model_id=model_id,
        trial_index=trial_plan["trial_index"],
        trial_type=trial_plan["trial_type"],
        params=params,
        status="running",
        started_at=datetime.utcnow(),
    )

    # Pre-slice data for all folds to avoid repeated .iloc calls.
    # Each fold gets its own X_train, y_train, X_val, y_val pre-computed.
    fold_inputs = []
    for split in validation_splits:
        train_idx = split["train_indices"]
        val_idx = split["validation_indices"]
        fold_inputs.append({
            "fold_index": split["fold_index"],
            "X_train": X.iloc[train_idx] if hasattr(X, "iloc") else X[train_idx],
            "y_train": y.iloc[train_idx] if hasattr(y, "iloc") else y[train_idx],
            "X_val": X.iloc[val_idx] if hasattr(X, "iloc") else X[val_idx],
            "y_val": y.iloc[val_idx] if hasattr(y, "iloc") else y[val_idx],
            "train_indices": train_idx,
            "val_indices": val_idx,
            "fold_pipeline_spec": fold_pipeline_spec,
        })

    logger.debug("trial %s: pre-sliced %d folds, parallel=%s",
          trial_id, len(fold_inputs), parallel_folds)

    n_folds = len(fold_inputs)
    n_workers = min(n_folds, 4)  # Cap at 4 concurrent folds to avoid memory pressure

    if parallel_folds and n_folds > 1:
        # Execute folds in parallel via ThreadPoolExecutor.
        # sklearn models with n_jobs=-1 release the GIL during C-level
        # operations, so threads provide meaningful parallelism for I/O +
        # model fitting.
        logger.info("trial %s: dispatching %d folds on %d workers ...",
              trial_id, n_folds, n_workers)
        fold_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as pool:
            future_map = {}
            for fi in fold_inputs:
                future = pool.submit(
                    _run_fold_wrapper,
                    X_train=fi["X_train"],
                    y_train=fi["y_train"],
                    X_val=fi["X_val"],
                    y_val=fi["y_val"],
                    train_indices=fi["train_indices"],
                    val_indices=fi["val_indices"],
                    fold_index=fi["fold_index"],
                    model_id=model_id,
                    task_type=task_type,
                    params=params,
                    trial_id=trial_id,
                    pipeline_spec_id=pipeline_spec_id,
                    exec_dir=exec_dir,
                    save_predictions_flag=save_predictions_flag,
                    save_model_flag=save_model_flag,
                    fold_timeout_seconds=fold_timeout_seconds,
                    fold_pipeline_spec=fi["fold_pipeline_spec"],
                )
                future_map[future] = fi["fold_index"]

            for future in concurrent.futures.as_completed(future_map):
                try:
                    fold_results.append(future.result())
                except Exception as e:
                    fi_idx = future_map[future]
                    logger.error("trial %s: fold %d crashed in worker — %s", trial_id, fi_idx, e)
                    import traceback
                    fold_results.append(FoldResultDTO(
                        fold_index=fi_idx,
                        train_size=0,
                        validation_size=0,
                        status="failed",
                        error_message=f"{e}\n{traceback.format_exc()}",
                    ))

        # Restore original fold order
        fold_results.sort(key=lambda f: f.fold_index)
    else:
        # Sequential fallback
        fold_results = []
        for fi in fold_inputs:
            fr = run_fold(
                X_train=fi["X_train"],
                y_train=fi["y_train"],
                X_val=fi["X_val"],
                y_val=fi["y_val"],
                train_indices=fi["train_indices"],
                val_indices=fi["val_indices"],
                fold_index=fi["fold_index"],
                model_id=model_id,
                task_type=task_type,
                params=params,
                trial_id=trial_id,
                pipeline_spec_id=pipeline_spec_id,
                exec_dir=exec_dir,
                save_predictions_flag=save_predictions_flag,
                save_model_flag=save_model_flag,
                fold_timeout_seconds=fold_timeout_seconds,
                fold_pipeline_spec=fi["fold_pipeline_spec"],
            )
            fold_results.append(fr)

    all_failed = all(f.status == "failed" for f in fold_results)
    n_completed = sum(1 for f in fold_results if f.status == "completed")
    n_failed = sum(1 for f in fold_results if f.status == "failed")
    logger.info("trial %s: %d/%d folds done (%d failed) in %.1fs (parallel=%s)",
          trial_id, n_completed, n_folds, n_failed,
          time.time() - started, parallel_folds)

    pred_paths = []
    model_paths = []
    for f in fold_results:
        if f.status == "completed":
            if f.prediction_artifact_path:
                pred_paths.append(f.prediction_artifact_path)
            if f.model_artifact_path:
                model_paths.append(f.model_artifact_path)

    result.fold_results = fold_results
    result.status = "failed" if all_failed else "completed"
    result.prediction_artifact_paths = pred_paths
    result.model_artifact_paths = model_paths

    # Aggregate raw metrics across folds
    agg_metrics = {}
    completed_folds = [f for f in fold_results if f.status == "completed"]
    if completed_folds:
        for key in completed_folds[0].raw_metric_values:
            values = [f.raw_metric_values.get(key) for f in completed_folds
                      if f.raw_metric_values.get(key) is not None]
            if values:
                agg_metrics[f"mean_{key}"] = sum(values) / len(values)

    result.raw_metric_values = agg_metrics
    result.finished_at = datetime.utcnow()
    result.duration_seconds = round(time.time() - started, 3)

    return result


def _run_fold_wrapper(
    X_train, y_train, X_val, y_val,
    train_indices, val_indices,
    fold_index, model_id, task_type, params,
    trial_id, pipeline_spec_id, exec_dir,
    save_predictions_flag, save_model_flag,
    fold_timeout_seconds=30,
    fold_pipeline_spec=None,
) -> FoldResultDTO:
    """Thin wrapper for ThreadPoolExecutor — receives pre-sliced data."""
    return run_fold(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        train_indices=train_indices,
        val_indices=val_indices,
        fold_index=fold_index,
        model_id=model_id,
        task_type=task_type,
        params=params,
        trial_id=trial_id,
        pipeline_spec_id=pipeline_spec_id,
        exec_dir=exec_dir,
        save_predictions_flag=save_predictions_flag,
        save_model_flag=save_model_flag,
        fold_timeout_seconds=fold_timeout_seconds,
        fold_pipeline_spec=fold_pipeline_spec,
    )
