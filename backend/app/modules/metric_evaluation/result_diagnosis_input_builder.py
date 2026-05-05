from typing import List, Any, Optional
from app.modules.metric_evaluation.schemas import (
    ModelRankingItem,
    BaselineComparison,
    MetricSummary,
    ResultDiagnosisInput,
    TrialMetricResult,
)
from app.modules.metric_evaluation.exceptions import ResultDiagnosisInputBuildException


def build_result_diagnosis_input(
    metric_evaluation_id: str,
    pipeline_execution_id: str,
    task_id: str,
    task_type: str,
    primary_metric: str,
    metric_direction: str,
    best_trial: Optional[Any],
    best_model_id: Optional[str],
    model_ranking: List[ModelRankingItem],
    baseline_comparison: BaselineComparison,
    metric_summary: MetricSummary,
    trial_results: List[TrialMetricResult],
    warnings: List[str],
) -> ResultDiagnosisInput:
    if len(trial_results) == 0:
        return ResultDiagnosisInput(
            metric_evaluation_id=metric_evaluation_id,
            pipeline_execution_id=pipeline_execution_id,
            task_id=task_id,
            task_type=task_type,
            primary_metric=primary_metric,
            metric_direction=metric_direction,
            ready_for_result_diagnosis=False,
            evaluation_warnings=["No trial results available."] + warnings,
        )

    evaluated_trials = [t for t in trial_results if t.status == "evaluated"]
    failed_trials = [t for t in trial_results if t.status == "failed"]

    ready = (
        len(evaluated_trials) > 0
        and best_trial is not None
        and len(model_ranking) > 0
        and metric_summary is not None
    )

    best_trial_dict = None
    if best_trial is not None:
        best_trial_dict = {
            "trial_id": best_trial.trial_id,
            "model_id": best_trial.model_id,
            "pipeline_spec_id": best_trial.pipeline_spec_id,
            "primary_metric_mean": best_trial.primary_metric_mean,
            "primary_metric_std": best_trial.primary_metric_std,
            "pipeline_role": best_trial.pipeline_role,
            "trial_type": best_trial.trial_type,
        }

    best_model_dict = None
    if best_model_id:
        for p in model_ranking:
            if p.model_id == best_model_id:
                best_model_dict = {
                    "model_id": p.model_id,
                    "model_family": p.model_family,
                    "rank": p.rank,
                    "primary_metric_value": p.primary_metric_value,
                }
                break

    failed_summary = {
        "n_failed_trials": len(failed_trials),
        "n_successful_trials": len(evaluated_trials),
        "failed_trial_ids": [t.trial_id for t in failed_trials][:10],
    }

    stability_summary = {}
    if len(evaluated_trials) > 0:
        std_values = [
            t.primary_metric_std for t in evaluated_trials
            if t.primary_metric_std is not None
        ]
        if std_values:
            stability_summary["mean_cv_std"] = sum(std_values) / len(std_values)
            stability_summary["max_cv_std"] = max(std_values)
            stability_summary["min_cv_std"] = min(std_values)

    return ResultDiagnosisInput(
        metric_evaluation_id=metric_evaluation_id,
        pipeline_execution_id=pipeline_execution_id,
        task_id=task_id,
        task_type=task_type,
        primary_metric=primary_metric,
        metric_direction=metric_direction,
        best_trial=best_trial_dict,
        best_model=best_model_dict,
        model_ranking=model_ranking,
        baseline_comparison=baseline_comparison,
        metric_summary=metric_summary,
        failed_trials_summary=failed_summary,
        stability_summary=stability_summary,
        evaluation_warnings=warnings,
        ready_for_result_diagnosis=ready,
    )
