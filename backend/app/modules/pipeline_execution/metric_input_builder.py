"""Metric Input Builder — constructs the downstream MetricEvaluationInput."""

from app.modules.pipeline_execution.schemas import MetricEvaluationInputDTO
from app.modules.pipeline_execution.exceptions import MetricEvaluationInputBuildException


def build_metric_evaluation_input(
    pipeline_execution_id: str,
    pipeline_generation_id: str,
    task_id: str,
    task_type: str,
    target_column: str,
    evaluation_plan: dict,
    validation_plan: dict,
    trial_results: list,
    prediction_artifacts: list,
    model_artifacts: list,
    primary_metric: str = None,
    metric_direction: str = "minimize",
) -> MetricEvaluationInputDTO:
    """Build the structured input for the downstream Metric Evaluation module.

    ready_for_metric_evaluation is true only when:
    - At least one trial completed successfully
    - At least one prediction artifact exists
    - target_column is valid
    - evaluation_plan is present
    """
    ready = (
        len(trial_results) > 0
        and any(
            (hasattr(t, "status") and t.status == "completed") or
            (isinstance(t, dict) and t.get("status") == "completed")
            for t in trial_results
        )
        and len(prediction_artifacts) > 0
        and bool(target_column)
        and bool(evaluation_plan)
    )

    trial_summaries = []
    for t in trial_results:
        if isinstance(t, dict):
            trial_summaries.append({
                "trial_id": t.get("trial_id"),
                "model_id": t.get("model_id"),
                "status": t.get("status"),
                "prediction_artifact_paths": t.get("prediction_artifact_paths", []),
                "model_artifact_paths": t.get("model_artifact_paths", []),
                "duration_seconds": t.get("duration_seconds"),
            })
        else:
            trial_summaries.append({
                "trial_id": t.trial_id,
                "model_id": t.model_id,
                "status": t.status,
                "prediction_artifact_paths": t.prediction_artifact_paths,
                "model_artifact_paths": t.model_artifact_paths,
                "duration_seconds": t.duration_seconds,
            })

    return MetricEvaluationInputDTO(
        pipeline_execution_id=pipeline_execution_id,
        pipeline_generation_id=pipeline_generation_id,
        task_id=task_id,
        task_type=task_type,
        target_column=target_column,
        primary_metric=primary_metric,
        metric_direction=metric_direction,
        evaluation_plan=evaluation_plan,
        validation_plan=validation_plan,
        trial_results=trial_summaries,
        prediction_artifacts=prediction_artifacts,
        model_artifacts=model_artifacts,
        ready_for_metric_evaluation=ready,
    )
