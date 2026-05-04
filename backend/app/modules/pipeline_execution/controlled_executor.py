"""Controlled Executor — the ONLY entry point for training execution.

No LLM code, no eval, no dynamic imports. Models come from Model Registry only.
"""

import time
from datetime import datetime
from typing import List
from app.modules.pipeline_execution.trial_runner import run_trial
from app.modules.pipeline_execution.schemas import (
    TrialResultDTO,
    PipelineRunResultDTO,
)
from app.modules.pipeline_execution.exceptions import TrialExecutionException


def execute_training(
    X,
    y,
    trial_plans: List[dict],
    validation_splits: list,
    task_type: str,
    exec_dir: str,
    execution_mode: str = "sequential",
    fail_fast: bool = False,
    save_predictions: bool = True,
    save_models: bool = True,
    max_runtime_seconds: int = None,
) -> dict:
    """Execute all trials from the expanded execution plan.

    Args:
        X: Feature matrix.
        y: Target vector.
        trial_plans: List of trial plan dicts from execution_planner.
        validation_splits: List of split dicts.
        task_type: 'regression' or 'classification'.
        exec_dir: Artifact output directory.
        execution_mode: 'sequential' (MVP) or 'limited_parallel'.
        fail_fast: Stop after first trial failure.
        save_predictions: Whether to persist predictions.
        save_models: Whether to persist model files.
        max_runtime_seconds: Maximum total execution time.

    Returns:
        Dict with:
            - trial_results: List[TrialResultDTO]
            - pipeline_run_results: List[PipelineRunResultDTO]
            - n_completed: int
            - n_failed: int
            - warnings: List[str]
    """
    started = time.time()
    trial_results: List[TrialResultDTO] = []
    pipeline_runs: dict = {}  # pipeline_spec_id -> PipelineRunResultDTO
    warnings = []

    for tp in trial_plans:
        # Check timeout
        if max_runtime_seconds and (time.time() - started) > max_runtime_seconds:
            warnings.append(
                f"Execution timeout reached ({max_runtime_seconds}s). "
                f"Remaining trials skipped."
            )
            break

        spec_id = tp["pipeline_spec_id"]

        # Initialize pipeline run tracker
        if spec_id not in pipeline_runs:
            pipeline_runs[spec_id] = PipelineRunResultDTO(
                pipeline_run_id=f"prun_{spec_id}",
                pipeline_spec_id=spec_id,
                pipeline_role=tp["pipeline_role"],
                model_id=tp["model_id"],
                model_family=tp.get("model_family"),
                hpo_enabled=tp.get("hpo_enabled", False),
                status="running",
            )

        pr = pipeline_runs[spec_id]
        pr.n_trials_planned += 1

        # Execute trial
        try:
            trial_result = run_trial(
                X=X,
                y=y,
                trial_plan=tp,
                validation_splits=validation_splits,
                task_type=task_type,
                exec_dir=exec_dir,
                save_predictions_flag=save_predictions,
                save_model_flag=save_models,
            )
            trial_results.append(trial_result)

            if trial_result.status == "completed":
                pr.n_trials_completed += 1
                if trial_result.prediction_artifact_path:
                    pr.prediction_artifact_paths.append(trial_result.prediction_artifact_path)
                if trial_result.model_artifact_path:
                    pr.model_artifact_paths.append(trial_result.model_artifact_path)
            else:
                pr.n_trials_failed += 1
                if fail_fast:
                    warnings.append(f"fail_fast triggered after trial {tp['trial_id']} failed.")
                    break

        except Exception as e:
            pr.n_trials_failed += 1
            failed_result = TrialResultDTO(
                trial_id=tp["trial_id"],
                pipeline_spec_id=spec_id,
                pipeline_run_id=f"prun_{spec_id}",
                model_id=tp["model_id"],
                trial_index=tp["trial_index"],
                trial_type=tp["trial_type"],
                params=tp.get("params", {}),
                status="failed",
                error_message=str(e),
            )
            trial_results.append(failed_result)
            warnings.append(f"Trial {tp['trial_id']} error: {e}")
            if fail_fast:
                break

    # Finalize pipeline run statuses
    for spec_id, pr in pipeline_runs.items():
        if pr.n_trials_completed > 0 and pr.n_trials_failed == 0:
            pr.status = "completed"
        elif pr.n_trials_completed > 0 and pr.n_trials_failed > 0:
            pr.status = "partially_failed"
        elif pr.n_trials_failed > 0 and pr.n_trials_completed == 0:
            pr.status = "failed"
        else:
            pr.status = "skipped"

    n_completed = sum(1 for t in trial_results if t.status == "completed")
    n_failed = sum(1 for t in trial_results if t.status == "failed")

    return {
        "trial_results": trial_results,
        "pipeline_run_results": list(pipeline_runs.values()),
        "n_completed": n_completed,
        "n_failed": n_failed,
        "warnings": warnings,
    }
