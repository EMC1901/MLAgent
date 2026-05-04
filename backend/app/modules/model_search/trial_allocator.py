import logging
from typing import List
from app.modules.model_search.schemas import TrialAllocationItem

logger = logging.getLogger(__name__)


def allocate_trials(
    candidate_models: List[dict],
    baseline_models: List[dict],
    hpo_budget_level: str,
    max_total_trials: int,
    n_samples: int,
    n_features: int,
) -> List[TrialAllocationItem]:
    """Allocate trial budget across models with priority weighting and dataset-aware adjustments."""
    allocations: List[TrialAllocationItem] = []

    hpo_baselines = [b for b in baseline_models if b.get("hpo_enabled", False)]
    non_hpo_baselines = [b for b in baseline_models if not b.get("hpo_enabled", False)]

    # Non-HPO models get 0 trials
    for b in non_hpo_baselines:
        allocations.append(TrialAllocationItem(model_id=b["model_id"], max_trials=0))

    all_hpo_models = hpo_baselines + candidate_models
    if not all_hpo_models:
        return allocations

    # Weight by priority and dataset size
    priority_weight = {"high": 3, "medium": 2, "low": 1}

    # Small datasets: give more weight to simpler models
    if n_samples < 200:
        for m in all_hpo_models:
            if m.get("priority") == "high":
                priority_weight["high"] = 4

    weights = []
    for m in all_hpo_models:
        priority = m.get("priority", "medium")
        weights.append(priority_weight.get(priority, 2))

    total_weight = sum(weights)
    if total_weight == 0:
        return allocations

    remaining = max_total_trials
    for i, m in enumerate(all_hpo_models):
        model_id = m.get("model_id", "")
        if i == len(all_hpo_models) - 1:
            trials = max(1, remaining)
        else:
            trials = max(1, int(max_total_trials * weights[i] / total_weight))
        trials = min(trials, remaining)
        remaining -= trials
        allocations.append(TrialAllocationItem(model_id=model_id, max_trials=trials))

    return allocations
