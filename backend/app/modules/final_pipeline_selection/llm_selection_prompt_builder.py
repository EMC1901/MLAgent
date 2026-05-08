import json
import logging
from typing import List, Dict, Any, Optional

from app.modules.final_pipeline_selection.schemas import (
    CandidateSelectionItem,
    FinalSelectedPipeline,
    SelectionPolicy,
    SystemSelectionReason,
    ConstraintCheckResult,
    FinalArtifactManifest,
)
from app.modules.final_pipeline_selection.enums import CandidateStatus

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an explanation assistant for final pipeline selection in an AutoML system for materials science.

The final pipeline has already been selected by the system. Your role is strictly limited to explaining WHY the system selected this pipeline.

You must not change the selected pipeline.
You must not change candidate ranking.
You must not modify metric values.
You must not recommend another pipeline as the final selected one.
You must only explain why the system selected this pipeline, summarize candidate differences, and highlight human-review risks.
You must not output executable code.

Return your response as a valid JSON object with exactly these fields:
- "why_selected": string (brief explanation of why this pipeline was selected)
- "candidate_difference_summary": array of objects with "candidate" (string) and "summary" (string)
- "selection_rationale_natural_language": string (detailed natural language explanation)
- "human_review_notes": array of strings (items for human reviewers to check)
- "risk_notes": array of strings (potential risks of this selection)
- "confidence_level": one of "low", "medium", "high"
"""


def build_llm_selection_explanation_context(
    final_pipeline: FinalSelectedPipeline,
    candidates: List[CandidateSelectionItem],
    policy: SelectionPolicy,
    system_reason: SystemSelectionReason,
    constraint_result: ConstraintCheckResult,
    artifact_manifest: Optional[FinalArtifactManifest] = None,
    task_type: str = "",
    target_column: str = "",
    primary_metric: str = "",
    metric_direction: str = "minimize",
) -> Dict[str, Any]:
    selected = _find_selected(candidates)
    top_n = 5
    ranked = sorted(
        [c for c in candidates if c.candidate_status != CandidateStatus.REJECTED],
        key=lambda c: c.selection_score or 0,
        reverse=True,
    )[:top_n]

    context = {
        "task_summary": {
            "task_type": task_type,
            "target_column": target_column,
            "primary_metric": primary_metric,
            "metric_direction": metric_direction,
        },
        "selected_pipeline": {
            "model_id": final_pipeline.final_model_id,
            "model_family": final_pipeline.final_model_family,
            "trial_id": final_pipeline.final_trial_id,
            "trial_type": final_pipeline.final_trial_type,
            "hyperparameters": final_pipeline.final_hyperparameters,
            "primary_metric_value": selected.primary_metric_value if selected else None,
            "selection_score": selected.selection_score if selected else None,
        },
        "candidate_ranking_top_n": [
            {
                "rank": c.selection_rank,
                "model": c.model_id,
                "model_family": c.model_family,
                "pipeline_role": c.pipeline_role,
                "primary_metric_value": c.primary_metric_value,
                "selection_score": c.selection_score,
                "stability_score": c.stability_score,
                "interpretability_score": c.interpretability_score,
            }
            for c in ranked
        ],
        "selection_policy": {
            "profile": policy.selection_profile,
            "weights": {
                "primary_metric": policy.primary_metric_weight,
                "stability": policy.stability_weight,
                "baseline_improvement": policy.baseline_improvement_weight,
                "interpretability": policy.interpretability_weight,
                "cost": policy.cost_weight,
            },
        },
        "system_selection_reason": system_reason.model_dump(),
        "constraint_check": {
            "passed": constraint_result.passed,
            "issues": constraint_result.issues,
            "warnings": constraint_result.warnings,
        },
        "artifact_completeness": artifact_manifest.artifact_integrity_status if artifact_manifest else "unknown",
        "rejected_candidates": [
            {
                "candidate_id": c.candidate_id,
                "model": c.model_id,
                "reason": c.rejection_reason,
            }
            for c in candidates
            if c.candidate_status == CandidateStatus.REJECTED
        ],
    }

    user_message = json.dumps(context, indent=2, default=str)
    return {"system_prompt": SYSTEM_PROMPT, "user_message": user_message, "selection_context": context}


def _find_selected(candidates: List[CandidateSelectionItem]) -> CandidateSelectionItem:
    for c in candidates:
        if c.is_final_selected:
            return c
    return CandidateSelectionItem()
