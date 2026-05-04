"""Trial Runner — executes a single trial across all folds."""

import time
from datetime import datetime
from app.modules.pipeline_execution.fold_runner import run_fold
from app.modules.pipeline_execution.schemas import TrialResultDTO, FoldResultDTO


def run_trial(
    X,
    y,
    trial_plan: dict,
    validation_splits: list,
    task_type: str,
    exec_dir: str,
    save_predictions_flag: bool = True,
    save_model_flag: bool = True,
) -> TrialResultDTO:
    """Execute one trial: iterate over folds, train, and collect results.

    Args:
        X: Feature matrix.
        y: Target vector.
        trial_plan: Dict from execution_planner with trial metadata and params.
        validation_splits: List of split dicts from validation_splitter.
        task_type: 'regression' or 'classification'.
        exec_dir: Artifact output directory.
        save_predictions_flag: Whether to persist prediction files.
        save_model_flag: Whether to persist model files.

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

    fold_results = []
    all_failed = True
    pred_paths = []
    model_paths = []

    for split in validation_splits:
        fold_result = run_fold(
            X=X,
            y=y,
            train_indices=split["train_indices"],
            val_indices=split["validation_indices"],
            fold_index=split["fold_index"],
            model_id=model_id,
            task_type=task_type,
            params=params,
            trial_id=trial_id,
            pipeline_spec_id=pipeline_spec_id,
            exec_dir=exec_dir,
            save_predictions_flag=save_predictions_flag,
            save_model_flag=save_model_flag,
        )
        fold_results.append(fold_result)
        if fold_result.status == "completed":
            all_failed = False
            if fold_result.prediction_artifact_path:
                pred_paths.append(fold_result.prediction_artifact_path)
            if fold_result.model_artifact_path:
                model_paths.append(fold_result.model_artifact_path)

    result.fold_results = fold_results
    result.status = "failed" if all_failed else "completed"
    result.prediction_artifact_path = pred_paths[0] if pred_paths else None
    result.model_artifact_path = model_paths[0] if model_paths else None

    # Aggregate raw metrics across folds
    agg_metrics = {}
    completed_folds = [f for f in fold_results if f.status == "completed"]
    if completed_folds:
        for key in completed_folds[0].raw_metric_values:
            values = [f.raw_metric_values.get(key) for f in completed_folds if f.raw_metric_values.get(key) is not None]
            if values:
                agg_metrics[f"mean_{key}"] = sum(values) / len(values)

    result.raw_metric_values = agg_metrics
    result.finished_at = datetime.utcnow()
    result.duration_seconds = round(time.time() - started, 3)

    return result
