"""Builder — assembles the final PipelineExecutionResponse."""

from app.modules.pipeline_execution.schemas import (
    PipelineExecutionResponse,
    ExecutionSummaryDTO,
    TrainingArtifactManifestDTO,
    MetricEvaluationInputDTO,
    RuntimeEnvironmentDTO,
)
from app.modules.pipeline_execution.runtime_monitor import capture_runtime_environment
from app.modules.pipeline_execution.execution_state_tracker import (
    determine_execution_status,
    compute_execution_counts,
)


def build_response(
    pipeline_execution_id: str,
    task_id: str,
    pipeline_generation_id: str,
    execution_mode: str,
    trial_results: list,
    pipeline_run_results: list,
    execution_result: dict,
    metric_evaluation_input: MetricEvaluationInputDTO,
    artifact_manifest: dict,
    started_at,
    finished_at,
    warnings: list,
    error_message: str = None,
    created_at=None,
    updated_at=None,
) -> PipelineExecutionResponse:
    """Assemble the full PipelineExecutionResponse."""
    counts = compute_execution_counts(trial_results, pipeline_run_results)
    status = determine_execution_status(
        n_completed=counts["n_trials_completed"],
        n_failed=counts["n_trials_failed"],
        n_total=counts["n_trials_planned"],
        warnings=warnings,
        pipeline_runs=pipeline_run_results,
    )
    duration = (
        (finished_at - started_at).total_seconds()
        if started_at and finished_at
        else 0.0
    )

    runtime_env = capture_runtime_environment()

    summary = ExecutionSummaryDTO(
        pipeline_execution_id=pipeline_execution_id,
        task_id=task_id,
        pipeline_generation_id=pipeline_generation_id,
        status=status,
        execution_mode=execution_mode,
        n_pipeline_specs=counts["n_pipeline_specs"],
        n_trials_planned=counts["n_trials_planned"],
        n_trials_completed=counts["n_trials_completed"],
        n_trials_failed=counts["n_trials_failed"],
        n_models_trained=counts["n_models_trained"],
        duration_seconds=duration,
        ready_for_metric_evaluation=metric_evaluation_input.ready_for_metric_evaluation,
    )

    manifest = TrainingArtifactManifestDTO(
        pipeline_execution_id=pipeline_execution_id,
        training_artifact_dir=artifact_manifest.get("exec_dir", ""),
        manifest_path=artifact_manifest.get("manifest_path"),
        execution_result_path=artifact_manifest.get("execution_result_path"),
        trial_results_path=artifact_manifest.get("trial_results_path"),
        prediction_paths=artifact_manifest.get("prediction_paths", []),
        model_paths=artifact_manifest.get("model_paths", []),
        log_path=artifact_manifest.get("log_path"),
        split_metadata_path=artifact_manifest.get("split_metadata_path"),
        metric_evaluation_input_path=artifact_manifest.get("metric_evaluation_input_path"),
    )

    return PipelineExecutionResponse(
        pipeline_execution_id=pipeline_execution_id,
        task_id=task_id,
        pipeline_generation_id=pipeline_generation_id,
        status=status,
        execution_mode=execution_mode,
        n_pipeline_specs=counts["n_pipeline_specs"],
        n_trials_planned=counts["n_trials_planned"],
        n_trials_completed=counts["n_trials_completed"],
        n_trials_failed=counts["n_trials_failed"],
        n_models_trained=counts["n_models_trained"],
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration,
        execution_summary=summary,
        pipeline_run_results=pipeline_run_results,
        trial_results=trial_results,
        training_artifact_manifest=manifest,
        runtime_environment=runtime_env,
        metric_evaluation_input=metric_evaluation_input,
        ready_for_metric_evaluation=metric_evaluation_input.ready_for_metric_evaluation,
        warnings=warnings,
        error_message=error_message,
        created_at=created_at,
        updated_at=updated_at,
    )
