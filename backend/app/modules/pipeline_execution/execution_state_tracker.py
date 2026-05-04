"""Execution State Tracker — maintains running/completed/failed counts."""

from app.modules.pipeline_execution.enums import PipelineExecutionStatus


def determine_execution_status(
    n_completed: int,
    n_failed: int,
    n_total: int,
    warnings: list,
    pipeline_runs: list,
) -> str:
    """Determine the overall execution status.

    Returns one of: completed, completed_with_warning, partially_failed, failed.
    """
    if n_total == 0:
        return PipelineExecutionStatus.FAILED

    if n_completed == n_total:
        if warnings:
            return PipelineExecutionStatus.COMPLETED_WITH_WARNING
        return PipelineExecutionStatus.COMPLETED

    if n_completed > 0 and n_failed > 0:
        return PipelineExecutionStatus.PARTIALLY_FAILED

    if n_failed == n_total:
        return PipelineExecutionStatus.FAILED

    return PipelineExecutionStatus.FAILED


def compute_execution_counts(
    trial_results: list,
    pipeline_run_results: list,
) -> dict:
    """Compute aggregate counts from trial and pipeline results.

    Accepts both Pydantic model objects and plain dicts.
    """
    n_trials_completed = sum(1 for t in trial_results if _get(t, "status") == "completed")
    n_trials_failed = sum(1 for t in trial_results if _get(t, "status") == "failed")
    n_models_trained = n_trials_completed
    n_pipeline_specs = len(pipeline_run_results)

    return {
        "n_pipeline_specs": n_pipeline_specs,
        "n_trials_planned": len(trial_results),
        "n_trials_completed": n_trials_completed,
        "n_trials_failed": n_trials_failed,
        "n_models_trained": n_models_trained,
    }


def _get(obj, attr: str):
    """Safely get an attribute from either a dict or an object."""
    if isinstance(obj, dict):
        return obj.get(attr)
    return getattr(obj, attr, None)
