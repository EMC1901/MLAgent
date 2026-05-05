from typing import List, Dict, Any, Optional
from app.modules.result_diagnosis.schemas import (
    ClosedLoopRefinementInput,
    LLMDiagnosisResult,
    SystemDiagnosticChecks,
    RefinementRecommendation,
    SuggestedNextIterationProfile,
)
from app.modules.result_diagnosis.exceptions import ClosedLoopInputBuildException


def build_closed_loop_refinement_input(
    result_diagnosis_id: str,
    metric_evaluation_id: str,
    task_id: str,
    llm_diagnosis: Optional[LLMDiagnosisResult],
    system_checks: SystemDiagnosticChecks,
    llm_available: bool = True,
) -> ClosedLoopRefinementInput:
    try:
        oa = llm_diagnosis.overall_assessment if llm_diagnosis else None
        should_refine = oa.should_refine if oa else False
        recommendations = llm_diagnosis.refinement_recommendations if llm_diagnosis else []

        # Determine refinement focus
        focus_set = set()
        for rec in recommendations:
            if rec.priority in ("high", "medium"):
                focus_set.add(rec.target_stage)
        refinement_focus = list(focus_set) if focus_set else ["model_search"]

        # Priority recommendations (high first, then medium)
        priority_recs = sorted(recommendations, key=lambda r: {"high": 0, "medium": 1, "low": 2}.get(r.priority, 3))
        priority_recs = priority_recs[:5]

        # Diagnostic findings summary
        findings_summary = []
        for f in (llm_diagnosis.diagnostic_findings if llm_diagnosis else []):
            findings_summary.append({
                "diagnosis_type": f.diagnosis_type,
                "severity": f.severity,
                "description": f.description,
            })

        # Constraints to preserve
        constraints = [
            "task_type",
            "target_column",
            "primary_metric",
        ]

        # Avoid actions based on diagnosis
        avoid_actions = []
        if system_checks.high_fold_variance:
            avoid_actions.append("do_not_reduce_validation_folds")
        if system_checks.candidate_underperforms_baseline:
            avoid_actions.append("do_not_remove_best_baseline")
        if system_checks.many_features_dropped:
            avoid_actions.append("do_not_further_drop_features_without_review")

        # Next iteration profile
        next_profile = SuggestedNextIterationProfile(
            model_search_budget="moderate",
            hpo_trials="increase_if_runtime_allows" if system_checks.hpo_budget_limited else "keep_current",
            feature_strategy="expand_or_refine" if system_checks.feature_count_low else "keep_current",
        )

        # Determine ready for closed loop
        has_actionable_recs = any(
            r.priority in ("high", "medium") for r in recommendations
        )
        ready = (
            should_refine
            and has_actionable_recs
            and llm_available
        )

        return ClosedLoopRefinementInput(
            result_diagnosis_id=result_diagnosis_id,
            metric_evaluation_id=metric_evaluation_id,
            task_id=task_id,
            should_refine=should_refine,
            refinement_focus=refinement_focus,
            priority_recommendations=priority_recs[:3],
            diagnostic_findings_summary=findings_summary,
            constraints_to_preserve=constraints,
            avoid_actions=avoid_actions,
            suggested_next_iteration_profile=next_profile,
            ready_for_closed_loop_refinement=ready,
        )

    except Exception as e:
        raise ClosedLoopInputBuildException(f"Failed to build closed-loop refinement input: {str(e)}")
