import numpy as np
from typing import Dict, List, Any
from app.modules.metric_evaluation.schemas import TrialMetricResult, PipelineMetricResult
from app.modules.metric_evaluation.enums import MetricDirection


def aggregate_pipeline_metrics(
    trial_results: List[TrialMetricResult],
    metric_direction: str = "minimize",
) -> List[PipelineMetricResult]:
    pipeline_groups: Dict[str, List[TrialMetricResult]] = {}
    for tr in trial_results:
        key = tr.pipeline_spec_id or tr.model_id
        pipeline_groups.setdefault(key, []).append(tr)

    results: List[PipelineMetricResult] = []
    for key, trials in pipeline_groups.items():
        evaluated_trials = [t for t in trials if t.status == "evaluated"]

        if len(evaluated_trials) == 0:
            results.append(PipelineMetricResult(
                pipeline_spec_id=trials[0].pipeline_spec_id,
                pipeline_run_id=trials[0].pipeline_run_id,
                model_id=trials[0].model_id,
                model_family=trials[0].model_family,
                pipeline_role=trials[0].pipeline_role,
                n_trials_evaluated=0,
            ))
            continue

        is_minimize = metric_direction == MetricDirection.MINIMIZE
        if is_minimize:
            best_trial = min(
                evaluated_trials,
                key=lambda t: t.primary_metric_mean if t.primary_metric_mean is not None else float("inf"),
            )
        else:
            best_trial = max(
                evaluated_trials,
                key=lambda t: t.primary_metric_mean if t.primary_metric_mean is not None else float("-inf"),
            )

        primary_values = [
            t.primary_metric_mean for t in evaluated_trials
            if t.primary_metric_mean is not None and np.isfinite(t.primary_metric_mean)
        ]

        results.append(PipelineMetricResult(
            pipeline_spec_id=evaluated_trials[0].pipeline_spec_id,
            pipeline_run_id=evaluated_trials[0].pipeline_run_id,
            model_id=evaluated_trials[0].model_id,
            model_family=evaluated_trials[0].model_family,
            pipeline_role=evaluated_trials[0].pipeline_role,
            n_trials_evaluated=len(evaluated_trials),
            best_trial_id=best_trial.trial_id,
            best_primary_metric_value=best_trial.primary_metric_mean,
            mean_primary_metric_value=float(np.mean(primary_values)) if primary_values else None,
            std_primary_metric_value=float(np.std(primary_values, ddof=1)) if len(primary_values) > 1 else 0.0,
            best_trial_params=best_trial.params,
        ))

    return results
