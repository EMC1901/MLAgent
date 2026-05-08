import logging
from typing import Optional

from app.modules.final_pipeline_selection.schemas import SelectionPolicy, FinalPipelineSelectionCreateRequest
from app.modules.final_pipeline_selection.enums import (
    SelectionProfile,
    PROFILE_WEIGHTS,
    TIE_BREAKER_ORDER,
    VALID_SELECTION_PROFILES,
)

logger = logging.getLogger(__name__)


def build_selection_policy(
    request: FinalPipelineSelectionCreateRequest,
    upstream_policy: Optional[dict] = None,
) -> SelectionPolicy:
    profile = request.selection_profile
    if profile not in VALID_SELECTION_PROFILES:
        profile = SelectionProfile.BALANCED

    weights = dict(PROFILE_WEIGHTS.get(profile, PROFILE_WEIGHTS[SelectionProfile.BALANCED]))

    # Override weights if explicitly provided in request
    if request.stability_weight is not None:
        weights["stability_weight"] = request.stability_weight
    if request.interpretability_weight is not None:
        weights["interpretability_weight"] = request.interpretability_weight
    if request.cost_weight is not None:
        weights["cost_weight"] = request.cost_weight

    # Merge upstream policy
    if upstream_policy and isinstance(upstream_policy, dict):
        upstream_weights = upstream_policy.get("weights", {})
        if upstream_weights:
            for key in weights:
                if key in upstream_weights:
                    weights[key] = upstream_weights[key]

    policy = SelectionPolicy(
        selection_profile=profile,
        primary_metric_weight=weights.get("primary_metric_weight", 0.5),
        stability_weight=weights.get("stability_weight", 0.2),
        baseline_improvement_weight=weights.get("baseline_improvement_weight", 0.15),
        interpretability_weight=weights.get("interpretability_weight", 0.1),
        cost_weight=weights.get("cost_weight", 0.05),
        constraint_weight=weights.get("constraint_weight", 0.0),
        require_model_artifact=request.require_model_artifact,
        require_prediction_artifact=request.require_prediction_artifact,
        allow_baseline_as_final=request.allow_baseline_as_final,
        tie_breaker_order=TIE_BREAKER_ORDER,
    )

    logger.info("Built selection policy: profile=%s, weights=%s", profile, weights)
    return policy
