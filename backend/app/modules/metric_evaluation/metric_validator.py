import numpy as np
from typing import List
from app.modules.metric_evaluation.schemas import (
    TrialMetricResult,
    ModelRankingItem,
    BaselineComparison,
    MetricValidationResult,
)
from app.modules.metric_evaluation.enums import MetricDirection


def validate_metric_results(
    trial_results: List[TrialMetricResult],
    model_ranking: List[ModelRankingItem],
    baseline_comparison: BaselineComparison,
    metric_direction: str,
    best_trial_id: str,
    result_diagnosis_input: dict,
) -> MetricValidationResult:
    issues: List[str] = []

    all_metrics_finite = True
    for t in trial_results:
        if t.status != "evaluated":
            continue
        if t.primary_metric_mean is not None and not np.isfinite(t.primary_metric_mean):
            all_metrics_finite = False
            issues.append(f"Trial '{t.trial_id}' has non-finite primary metric value.")
        for fold in t.fold_metrics:
            if fold.primary_metric_value is not None and not np.isfinite(fold.primary_metric_value):
                all_metrics_finite = False
                issues.append(
                    f"Fold '{fold.fold_metric_id}' in trial '{t.trial_id}' "
                    "has non-finite primary metric value."
                )

    primary_metric_present = len(model_ranking) > 0

    is_minimize = metric_direction == MetricDirection.MINIMIZE
    ranking_consistent = True
    if len(model_ranking) >= 2:
        for i in range(len(model_ranking) - 1):
            a = model_ranking[i]
            b = model_ranking[i + 1]
            if a.primary_metric_value is not None and b.primary_metric_value is not None:
                if is_minimize and a.primary_metric_value > b.primary_metric_value:
                    ranking_consistent = False
                    issues.append(
                        f"Ranking inconsistency: rank {a.rank} value {a.primary_metric_value} "
                        f"> rank {b.rank} value {b.primary_metric_value}."
                    )
                elif not is_minimize and a.primary_metric_value < b.primary_metric_value:
                    ranking_consistent = False
                    issues.append(
                        f"Ranking inconsistency: rank {a.rank} value {a.primary_metric_value} "
                        f"< rank {b.rank} value {b.primary_metric_value}."
                    )

    best_trial_in_results = any(t.trial_id == best_trial_id for t in trial_results)

    baseline_references_valid = True
    if baseline_comparison.baseline_available:
        bl_model = baseline_comparison.best_baseline_model_id
        if bl_model and not any(t.model_id == bl_model for t in trial_results):
            baseline_references_valid = False
            issues.append(f"Baseline model '{bl_model}' not found in trial results.")

    diagnosis_input_complete = bool(
        result_diagnosis_input
        and result_diagnosis_input.get("best_trial")
        and result_diagnosis_input.get("model_ranking")
    )

    is_valid = (
        all_metrics_finite
        and primary_metric_present
        and ranking_consistent
        and best_trial_in_results
        and baseline_references_valid
        and diagnosis_input_complete
    )

    return MetricValidationResult(
        is_valid=is_valid,
        all_metrics_finite=all_metrics_finite,
        primary_metric_present=primary_metric_present,
        ranking_consistent=ranking_consistent,
        best_trial_in_results=best_trial_in_results,
        baseline_references_valid=baseline_references_valid,
        diagnosis_input_complete=diagnosis_input_complete,
        issues=issues,
    )
