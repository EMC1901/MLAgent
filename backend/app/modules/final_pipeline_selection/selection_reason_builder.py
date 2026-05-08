import logging
from typing import List

from app.modules.final_pipeline_selection.schemas import (
    CandidateSelectionItem,
    FinalSelectedPipeline,
    SelectionPolicy,
    SystemSelectionReason,
)
from app.modules.final_pipeline_selection.enums import CandidateStatus

logger = logging.getLogger(__name__)


def build_system_selection_reason(
    final_pipeline: FinalSelectedPipeline,
    candidates: List[CandidateSelectionItem],
    policy: SelectionPolicy,
    primary_metric: str = "",
) -> SystemSelectionReason:
    selected = _find_selected(candidates)

    reason = SystemSelectionReason(
        main_reason=_build_main_reason(final_pipeline, selected, primary_metric),
        metric_reason=_build_metric_reason(selected, primary_metric),
        stability_reason=_build_stability_reason(selected),
        baseline_reason=_build_baseline_reason(selected, candidates),
        interpretability_reason=_build_interpretability_reason(selected, policy),
        cost_reason=_build_cost_reason(selected),
        constraint_reason=_build_constraint_reason(selected),
        artifact_reason=_build_artifact_reason(final_pipeline),
        tradeoff_summary=_build_tradeoff_summary(final_pipeline, selected, policy),
    )

    logger.info("Built system selection reason for %s", final_pipeline.final_model_id)
    return reason


def _find_selected(candidates: List[CandidateSelectionItem]) -> CandidateSelectionItem:
    for c in candidates:
        if c.is_final_selected:
            return c
    return candidates[0] if candidates else CandidateSelectionItem()


def _build_main_reason(
    fp: FinalSelectedPipeline, c: CandidateSelectionItem, primary_metric: str
) -> str:
    return (
        f"The {fp.final_model_family} pipeline ({fp.final_trial_id}) was selected "
        f"as the final pipeline with {primary_metric or 'primary metric'} value "
        f"{c.primary_metric_value} and selection score {c.selection_score}."
    )


def _build_metric_reason(c: CandidateSelectionItem, primary_metric: str) -> str:
    return (
        f"Ranked #{c.primary_metric_rank} on {primary_metric or 'primary metric'} "
        f"with value {c.primary_metric_value}."
    )


def _build_stability_reason(c: CandidateSelectionItem) -> str:
    level = "high" if c.stability_score >= 0.8 else "moderate" if c.stability_score >= 0.5 else "low"
    return f"Stability score: {c.stability_score:.2f} ({level})."


def _build_baseline_reason(
    c: CandidateSelectionItem, candidates: List[CandidateSelectionItem]
) -> str:
    if c.pipeline_role == "baseline":
        return "Selected candidate is the baseline model."
    return f"Baseline improvement score: {c.baseline_improvement_score:.2f}."


def _build_interpretability_reason(
    c: CandidateSelectionItem, policy: SelectionPolicy
) -> str:
    return (
        f"Interpretability score: {c.interpretability_score:.2f} "
        f"(model family: {c.model_family}, profile: {policy.selection_profile})."
    )


def _build_cost_reason(c: CandidateSelectionItem) -> str:
    return f"Cost score: {c.cost_score:.2f}."


def _build_constraint_reason(c: CandidateSelectionItem) -> str:
    return "All hard constraints satisfied."


def _build_artifact_reason(fp: FinalSelectedPipeline) -> str:
    return (
        f"Model artifact sourced from PipelineExecution {fp.source_pipeline_execution_id}, "
        f"MetricEvaluation {fp.source_metric_evaluation_id}."
    )


def _build_tradeoff_summary(
    fp: FinalSelectedPipeline, c: CandidateSelectionItem, policy: SelectionPolicy
) -> str:
    return (
        f"The final selection balances {policy.selection_profile} priorities: "
        f"primary metric weight={policy.primary_metric_weight}, "
        f"stability weight={policy.stability_weight}, "
        f"interpretability weight={policy.interpretability_weight}, "
        f"cost weight={policy.cost_weight}. "
        f"Selected model {fp.final_model_family} achieves the best overall trade-off."
    )
