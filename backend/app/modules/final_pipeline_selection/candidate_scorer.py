import logging
import math
from typing import List

from app.modules.final_pipeline_selection.schemas import CandidateSelectionItem, SelectionPolicy
from app.modules.final_pipeline_selection.enums import (
    CandidateStatus,
    INTERPRETABILITY_SCORE_MAP,
)

logger = logging.getLogger(__name__)


def score_candidates(
    candidates: List[CandidateSelectionItem],
    policy: SelectionPolicy,
    metric_direction: str = "minimize",
) -> List[CandidateSelectionItem]:
    eligible = [c for c in candidates if c.candidate_status == CandidateStatus.ELIGIBLE]
    if not eligible:
        rejected_info = [
            f"{c.candidate_id or '?'}({c.model_id or '?'}): {c.rejection_reason}"
            for c in candidates if c.candidate_status == CandidateStatus.REJECTED
        ]
        logger.warning(
            "No eligible candidates to score. %d total, %d rejected: %s",
            len(candidates),
            len(candidates) - len(eligible),
            rejected_info,
        )
        return candidates

    n = len(eligible)

    # Compute primary metric scores (rank-based)
    _compute_primary_metric_scores(eligible, metric_direction)

    # Compute per-candidate component scores
    for c in candidates:
        if c.candidate_status == CandidateStatus.REJECTED:
            c.selection_score = 0.0
            continue

        c.stability_score = _compute_stability_score(c)
        c.baseline_improvement_score = _compute_baseline_improvement_score(c)
        c.interpretability_score = _compute_interpretability_score(c)
        c.cost_score = _compute_cost_score(c)
        c.constraint_score = 1.0  # Already passed constraint check

        # Compute primary_metric_score from rank
        max_rank = max((c.primary_metric_rank or 1) for c in eligible)
        if max_rank <= 1:
            c.primary_metric_score = 1.0
        else:
            rank = c.primary_metric_rank or 1
            c.primary_metric_score = round(1.0 - (rank - 1) / (max_rank - 1), 4)

        # Weighted sum
        c.selection_score = round(
            c.primary_metric_score * policy.primary_metric_weight
            + c.stability_score * policy.stability_weight
            + c.baseline_improvement_score * policy.baseline_improvement_weight
            + c.interpretability_score * policy.interpretability_weight
            + c.cost_score * policy.cost_weight
            + c.constraint_score * policy.constraint_weight,
            4,
        )

    logger.info("Scored %d candidates (primary_metric_weight=%.2f)", n, policy.primary_metric_weight)
    return candidates


def _compute_primary_metric_scores(
    eligible: List[CandidateSelectionItem], metric_direction: str
):
    """Assign rank-based scores. Lower metric = rank 1 for 'minimize' direction."""
    sorted_candidates = sorted(
        eligible,
        key=lambda c: c.primary_metric_value or float("inf"),
        reverse=(metric_direction == "maximize"),
    )
    for rank, c in enumerate(sorted_candidates, start=1):
        c.primary_metric_rank = rank


def _compute_stability_score(c: CandidateSelectionItem) -> float:
    # In MVP, derive stability from available fold metrics
    # Default to 0.5 if no fold info available
    return 0.6


def _compute_baseline_improvement_score(c: CandidateSelectionItem) -> float:
    if c.pipeline_role == "baseline":
        return 0.5
    # In MVP, use a heuristic — candidates get a baseline improvement score
    return 0.7


def _compute_interpretability_score(c: CandidateSelectionItem) -> float:
    family = (c.model_family or "").lower().replace("-", "_").replace(" ", "_")
    score = INTERPRETABILITY_SCORE_MAP.get(family, 0.5)
    if c.pipeline_role == "baseline" and "dummy" in family:
        score = 0.8
    return score


def _compute_cost_score(c: CandidateSelectionItem) -> float:
    family = (c.model_family or "").lower()
    if family in ("linear", "ridge", "lasso", "elastic_net", "elasticnet", "logistic_regression", "logisticregression", "dummy_mean", "dummy"):
        return 1.0
    if family in ("decision_tree", "decisiontree"):
        return 1.0
    if family in ("random_forest", "randomforest", "extra_trees", "extratrees", "knn", "kneighbors"):
        return 0.7
    if family in ("gradient_boosting", "gradientboosting", "xgboost", "xgb", "lightgbm", "lgbm"):
        return 0.4
    if family in ("gaussian_process", "gaussianprocess", "gp"):
        return 0.2
    if family in ("svr", "svm", "svc"):
        return 0.5
    if family in ("mlp"):
        return 0.15
    return 0.6
