from typing import List, Optional
from app.modules.metric_evaluation.schemas import (
    TrialMetricResult,
    ModelRankingItem,
    BaselineComparison,
)
from app.modules.metric_evaluation.enums import MetricDirection


def compare_against_baselines(
    trial_results: List[TrialMetricResult],
    ranking_items: List[ModelRankingItem],
    metric_direction: str,
) -> BaselineComparison:
    baseline_trials = [
        t for t in trial_results
        if t.pipeline_role == "baseline"
        and t.status == "evaluated"
        and t.primary_metric_mean is not None
    ]

    candidate_trials = [
        t for t in trial_results
        if t.pipeline_role != "baseline"
        and t.status == "evaluated"
        and t.primary_metric_mean is not None
    ]

    if len(baseline_trials) == 0:
        return BaselineComparison(
            baseline_available=False,
            candidate_beats_baseline=len(candidate_trials) > 0,
            comparison_notes=["No baseline trials available for comparison."],
        )

    is_minimize = metric_direction == MetricDirection.MINIMIZE

    if is_minimize:
        best_baseline = min(baseline_trials, key=lambda t: t.primary_metric_mean)
    else:
        best_baseline = max(baseline_trials, key=lambda t: t.primary_metric_mean)

    best_candidate = None
    if len(candidate_trials) > 0:
        if is_minimize:
            best_candidate = min(candidate_trials, key=lambda t: t.primary_metric_mean)
        else:
            best_candidate = max(candidate_trials, key=lambda t: t.primary_metric_mean)

    if best_candidate is None:
        return BaselineComparison(
            baseline_available=True,
            best_baseline_model_id=best_baseline.model_id,
            best_baseline_trial_id=best_baseline.trial_id,
            best_baseline_metric_value=best_baseline.primary_metric_mean,
            comparison_notes=["No candidate trials available for comparison."],
        )

    baseline_val = best_baseline.primary_metric_mean or 0
    candidate_val = best_candidate.primary_metric_mean or 0

    if is_minimize:
        abs_improvement = baseline_val - candidate_val
        candidate_beats = candidate_val < baseline_val
    else:
        abs_improvement = candidate_val - baseline_val
        candidate_beats = candidate_val > baseline_val

    rel_improvement = (
        (abs_improvement / abs(baseline_val) * 100)
        if baseline_val != 0
        else None
    )

    notes = []
    if candidate_beats:
        notes.append(
            f"Best candidate '{best_candidate.model_id}' ({candidate_val:.6f}) "
            f"outperforms best baseline '{best_baseline.model_id}' ({baseline_val:.6f})."
        )
        if rel_improvement is not None:
            notes.append(f"Relative improvement: {rel_improvement:.2f}%.")
    else:
        notes.append(
            f"Best candidate '{best_candidate.model_id}' ({candidate_val:.6f}) "
            f"does not beat best baseline '{best_baseline.model_id}' ({baseline_val:.6f})."
        )

    return BaselineComparison(
        baseline_available=True,
        best_baseline_model_id=best_baseline.model_id,
        best_baseline_trial_id=best_baseline.trial_id,
        best_baseline_metric_value=baseline_val,
        best_candidate_model_id=best_candidate.model_id,
        best_candidate_trial_id=best_candidate.trial_id,
        best_candidate_metric_value=candidate_val,
        absolute_improvement=abs_improvement,
        relative_improvement_percentage=rel_improvement,
        candidate_beats_baseline=candidate_beats,
        comparison_notes=notes,
    )
