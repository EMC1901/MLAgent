import logging
from typing import List, Dict, Any

from app.modules.final_pipeline_selection.schemas import CandidateSelectionItem, FinalSelectedPipeline
from app.modules.final_pipeline_selection.enums import CandidateStatus
from app.modules.final_pipeline_selection.exceptions import FinalRankingException

logger = logging.getLogger(__name__)


def rank_candidates(
    candidates: List[CandidateSelectionItem],
    selection_input_current_best_trial_id: str = "",
) -> List[CandidateSelectionItem]:
    eligible = [c for c in candidates if c.candidate_status == CandidateStatus.ELIGIBLE]
    if not eligible:
        rejected = [c for c in candidates if c.candidate_status == CandidateStatus.REJECTED]
        details = "; ".join(
            f"{c.candidate_id or '?'}({c.model_id or '?'}): {c.rejection_reason or 'no reason'}"
            for c in rejected[:5]
        )
        raise FinalRankingException(
            f"No eligible candidates to rank ({len(candidates)} total, {len(rejected)} rejected). "
            f"Rejections: {details}"
        )

    # Sort by selection_score descending, then tie-breakers
    sorted_candidates = sorted(
        eligible,
        key=lambda c: (
            c.selection_score or 0,
            c.primary_metric_score or 0,
            c.stability_score or 0,
            c.interpretability_score or 0,
            c.cost_score or 0,
            0 if c.pipeline_role != "baseline" else -1,
        ),
        reverse=True,
    )

    for rank, c in enumerate(sorted_candidates, start=1):
        c.selection_rank = rank

    # Mark the first as selected
    if sorted_candidates:
        sorted_candidates[0].candidate_status = CandidateStatus.SELECTED
        sorted_candidates[0].is_final_selected = True

    # Also rank rejected candidates as rank -1
    for c in candidates:
        if c.candidate_status == CandidateStatus.REJECTED:
            c.selection_rank = None

    logger.info("Ranked %d candidates, selected %s", len(sorted_candidates),
                sorted_candidates[0].candidate_id if sorted_candidates else "none")
    return candidates


def select_final_pipeline(candidates: List[CandidateSelectionItem]) -> FinalSelectedPipeline:
    """Extract the final selected candidate as a FinalSelectedPipeline object."""
    selected = None
    for c in candidates:
        if c.is_final_selected and c.candidate_status == CandidateStatus.SELECTED:
            selected = c
            break
    if not selected:
        # Fallback: pick top-ranked eligible candidate
        for c in candidates:
            if c.candidate_status == CandidateStatus.ELIGIBLE:
                selected = c
                c.is_final_selected = True
                c.candidate_status = CandidateStatus.SELECTED
                break
    if not selected:
        raise FinalRankingException("No candidate could be selected as final pipeline.")

    return FinalSelectedPipeline(
        final_pipeline_spec_id=selected.pipeline_spec_id,
        final_model_id=selected.model_id,
        final_model_family=selected.model_family,
        final_trial_id=selected.trial_id,
        final_trial_type=selected.trial_type,
        final_hyperparameters=selected.hyperparameters,
        source_metric_evaluation_id=selected.metric_evaluation_id,
        source_pipeline_execution_id=selected.pipeline_execution_id,
        source_pipeline_generation_id=selected.pipeline_generation_id,
    )
