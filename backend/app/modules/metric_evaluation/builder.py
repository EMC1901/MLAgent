from typing import List, Optional
from datetime import datetime
from app.modules.metric_evaluation.schemas import (
    MetricEvaluationResponse,
    MetricEvaluationSummaryResponse,
    MetricSummary,
    FoldMetricResult,
    TrialMetricResult,
    PipelineMetricResult,
    ModelRankingItem,
    BaselineComparison,
    MetricValidationResult,
    EvaluationArtifactManifest,
    ResultDiagnosisInput,
    FinalHoldoutEvaluation,
)
from app.modules.metric_evaluation.enums import MetricDirection


def build_metric_summary(
    trial_results: List[TrialMetricResult],
    primary_metric: str,
    metric_direction: str,
) -> MetricSummary:
    evaluated_trials = [t for t in trial_results if t.status == "evaluated"]
    values = [
        t.primary_metric_mean for t in evaluated_trials
        if t.primary_metric_mean is not None
    ]

    if not values:
        return MetricSummary(
            primary_metric=primary_metric,
            metric_direction=metric_direction,
        )

    is_minimize = metric_direction == MetricDirection.MINIMIZE

    return MetricSummary(
        primary_metric=primary_metric,
        metric_direction=metric_direction,
        best_metric_value=min(values) if is_minimize else max(values),
        worst_metric_value=max(values) if is_minimize else min(values),
        mean_metric_value=sum(values) / len(values),
        std_metric_value=(
            (sum((v - sum(values) / len(values)) ** 2 for v in values) / (len(values) - 1)) ** 0.5
            if len(values) > 1 else 0.0
        ),
        n_trials_contributing=len(evaluated_trials),
        n_models_contributing=len(set(t.model_id for t in evaluated_trials)),
    )


def build_response(
    metric_evaluation_id: str,
    task_id: str,
    pipeline_execution_id: str,
    pipeline_generation_id: str,
    status: str,
    task_type: str,
    primary_metric: str,
    metric_direction: str,
    n_trials_evaluated: int,
    n_trials_failed: int,
    n_models_evaluated: int,
    best_trial_id: Optional[str],
    best_model_id: Optional[str],
    best_pipeline_spec_id: Optional[str],
    metric_summary: MetricSummary,
    final_holdout_evaluation: Optional[FinalHoldoutEvaluation],
    trial_metric_results: List[TrialMetricResult],
    pipeline_metric_results: List[PipelineMetricResult],
    fold_metric_results: List[FoldMetricResult],
    model_ranking: List[ModelRankingItem],
    baseline_comparison: BaselineComparison,
    metric_validation_result: MetricValidationResult,
    evaluation_artifact_manifest: EvaluationArtifactManifest,
    result_diagnosis_input: ResultDiagnosisInput,
    warnings: List[str],
    error_message: Optional[str],
    created_at: datetime,
    updated_at: datetime,
) -> MetricEvaluationResponse:
    return MetricEvaluationResponse(
        metric_evaluation_id=metric_evaluation_id,
        task_id=task_id,
        pipeline_execution_id=pipeline_execution_id,
        pipeline_generation_id=pipeline_generation_id,
        status=status,
        task_type=task_type,
        primary_metric=primary_metric,
        metric_direction=metric_direction,
        n_trials_evaluated=n_trials_evaluated,
        n_trials_failed=n_trials_failed,
        n_models_evaluated=n_models_evaluated,
        best_trial_id=best_trial_id,
        best_model_id=best_model_id,
        best_pipeline_spec_id=best_pipeline_spec_id,
        metric_summary=metric_summary,
        final_holdout_evaluation=final_holdout_evaluation,
        trial_metric_results=trial_metric_results,
        pipeline_metric_results=pipeline_metric_results,
        fold_metric_results=fold_metric_results,
        model_ranking=model_ranking,
        baseline_comparison=baseline_comparison,
        metric_validation_result=metric_validation_result,
        evaluation_artifact_manifest=evaluation_artifact_manifest,
        result_diagnosis_input=result_diagnosis_input,
        ready_for_result_diagnosis=result_diagnosis_input.ready_for_result_diagnosis,
        warnings=warnings,
        error_message=error_message,
        created_at=created_at,
        updated_at=updated_at,
    )


def build_summary_response(record) -> MetricEvaluationSummaryResponse:
    bl_improvement = None
    if record.metric_summary_json:
        bl_comp = (record.evaluation_json or {}).get("baseline_comparison", {})
        if isinstance(bl_comp, dict):
            bl_improvement = bl_comp.get("absolute_improvement")

    return MetricEvaluationSummaryResponse(
        metric_evaluation_id=record.id,
        task_id=record.task_id,
        status=record.status or "unknown",
        primary_metric=record.primary_metric,
        best_model_id=record.best_model_id,
        best_trial_id=record.best_trial_id,
        best_metric_value=record.best_primary_metric_value,
        baseline_improvement=bl_improvement,
        ready_for_result_diagnosis=record.ready_for_result_diagnosis or False,
        created_at=record.created_at,
    )
