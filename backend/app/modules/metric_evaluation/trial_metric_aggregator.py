import numpy as np
from typing import Dict, List, Any, Optional
from app.modules.metric_evaluation.schemas import FoldMetricResult, TrialMetricResult


def aggregate_trial_metrics(
    fold_results: List[FoldMetricResult],
    trial_info_map: Dict[str, Dict[str, Any]],
    primary_metric: str,
) -> List[TrialMetricResult]:
    trial_folds: Dict[str, List[FoldMetricResult]] = {}
    for fr in fold_results:
        trial_folds.setdefault(fr.trial_id, []).append(fr)

    results: List[TrialMetricResult] = []
    for trial_id, folds in trial_folds.items():
        info = trial_info_map.get(trial_id, {})
        evaluated_folds = [f for f in folds if f.status == "evaluated"]

        if len(evaluated_folds) == 0:
            results.append(TrialMetricResult(
                trial_id=trial_id,
                pipeline_spec_id=info.get("pipeline_spec_id", folds[0].pipeline_spec_id if folds else ""),
                pipeline_run_id=info.get("pipeline_run_id", ""),
                model_id=info.get("model_id", folds[0].model_id if folds else ""),
                model_family=info.get("model_family"),
                pipeline_role=info.get("pipeline_role"),
                trial_type=info.get("trial_type"),
                params=info.get("params", {}),
                n_folds=len(folds),
                fold_metrics=folds,
                status="failed",
            ))
            continue

        primary_values = [
            f.primary_metric_value for f in evaluated_folds
            if f.primary_metric_value is not None and np.isfinite(f.primary_metric_value)
        ]

        if len(primary_values) == 0:
            results.append(TrialMetricResult(
                trial_id=trial_id,
                pipeline_spec_id=evaluated_folds[0].pipeline_spec_id,
                pipeline_run_id=info.get("pipeline_run_id", ""),
                model_id=evaluated_folds[0].model_id,
                model_family=info.get("model_family"),
                pipeline_role=info.get("pipeline_role"),
                trial_type=info.get("trial_type"),
                params=info.get("params", {}),
                n_folds=len(folds),
                fold_metrics=folds,
                status="failed",
            ))
            continue

        aggregated: Dict[str, float] = {}
        all_metric_names = set()
        for f in evaluated_folds:
            all_metric_names.update(f.metrics.keys())

        for key in all_metric_names:
            vals = [f.metrics[key] for f in evaluated_folds if key in f.metrics and np.isfinite(f.metrics[key])]
            if vals:
                aggregated[f"{key}_mean"] = float(np.mean(vals))
                aggregated[f"{key}_std"] = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0

        results.append(TrialMetricResult(
            trial_id=trial_id,
            pipeline_spec_id=evaluated_folds[0].pipeline_spec_id,
            pipeline_run_id=info.get("pipeline_run_id", ""),
            model_id=evaluated_folds[0].model_id,
            model_family=info.get("model_family"),
            pipeline_role=info.get("pipeline_role"),
            trial_type=info.get("trial_type"),
            params=info.get("params", {}),
            n_folds=len(folds),
            fold_metrics=folds,
            aggregated_metrics=aggregated,
            primary_metric_mean=float(np.mean(primary_values)),
            primary_metric_std=float(np.std(primary_values, ddof=1)) if len(primary_values) > 1 else 0.0,
            primary_metric_min=float(np.min(primary_values)),
            primary_metric_max=float(np.max(primary_values)),
            status="evaluated",
        ))

    return results
