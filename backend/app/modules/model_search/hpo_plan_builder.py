import logging
from typing import List
from app.shared.config.settings import settings
from app.shared.registry.hpo_registry import get_hpo_method_spec
from app.modules.model_search.schemas import HPOPlan, TrialAllocationItem
from app.modules.model_search.enums import HPOBudgetLevel

logger = logging.getLogger(__name__)


def build_hpo_plan(
    llm_advice: dict,
    updated_hpo_strategy: dict,
    n_samples: int,
    n_features: int,
    candidate_models: List[dict],
    baseline_models: List[dict],
    preferred_search_method: str = None,
    max_total_trials_override: int = None,
) -> HPOPlan:
    """Build HPO plan based on LLM advice, registry, and dataset characteristics."""
    hpo_rec = llm_advice.get("hpo_recommendation", {}) if llm_advice else {}

    # Determine if HPO is enabled
    enabled = hpo_rec.get("enabled", True) if hpo_rec else True

    # Select search method
    search_method = preferred_search_method or hpo_rec.get("search_method") or "random_search"
    method_spec = get_hpo_method_spec(search_method)
    if not method_spec:
        search_method = "random_search"
        method_spec = get_hpo_method_spec(search_method)

    # Determine budget level
    budget_level = hpo_rec.get("budget_level", _infer_budget_level(n_samples, n_features))

    # Determine max trials
    if max_total_trials_override:
        max_total_trials = max_total_trials_override
    elif hpo_rec.get("max_total_trials"):
        max_total_trials = int(hpo_rec["max_total_trials"])
    else:
        max_total_trials = _default_trials_for_budget(budget_level, method_spec)

    max_allowed = getattr(settings, "MODEL_SEARCH_MAX_TOTAL_TRIALS", 50)
    max_total_trials = min(max_total_trials, max_allowed)

    # Determine max parallel
    max_parallel = getattr(settings, "MODEL_SEARCH_DEFAULT_MAX_PARALLEL_TRIALS", 1)

    # Build trial allocation
    trial_allocation = _allocate_trials(
        candidate_models, baseline_models, max_total_trials,
    )

    # Determine fallback method
    fallback = "random_search" if search_method != "random_search" else None

    return HPOPlan(
        enabled=enabled,
        search_method=search_method,
        budget_level=budget_level,
        max_total_trials=max_total_trials,
        max_parallel_trials=max_parallel,
        trial_allocation=trial_allocation,
        early_stopping=budget_level == HPOBudgetLevel.LOW,
        fallback_method=fallback,
    )


def _infer_budget_level(n_samples: int, n_features: int) -> str:
    if n_samples < 200 or n_features < 10:
        return HPOBudgetLevel.LOW
    elif n_samples < 1000:
        return HPOBudgetLevel.MODERATE
    return HPOBudgetLevel.HIGH


def _default_trials_for_budget(budget_level: str, method_spec: dict) -> int:
    if not method_spec:
        return 30
    if budget_level == HPOBudgetLevel.LOW:
        return method_spec.get("default_max_trials_small", 10)
    elif budget_level == HPOBudgetLevel.HIGH:
        return method_spec.get("default_max_trials_large", 50)
    return method_spec.get("default_max_trials_medium", 30)


def _allocate_trials(
    candidate_models: List[dict],
    baseline_models: List[dict],
    max_total_trials: int,
) -> List[TrialAllocationItem]:
    """Allocate trial budget across models, weighted by priority."""
    allocations = []

    # Baseline models get minimal trials
    hpo_baselines = [b for b in baseline_models if b.get("hpo_enabled")]
    non_hpo_baselines = [b for b in baseline_models if not b.get("hpo_enabled")]

    # Non-HPO baselines get 0 trials (they don't need HPO)
    for b in non_hpo_baselines:
        allocations.append(TrialAllocationItem(model_id=b["model_id"], max_trials=0))

    all_hpo_models = hpo_baselines + candidate_models
    if not all_hpo_models:
        return allocations

    # Weight by priority
    priority_weight = {"high": 3, "medium": 2, "low": 1}
    weights = []
    for m in all_hpo_models:
        priority = m.get("priority", "medium")
        weights.append(priority_weight.get(priority, 2))

    total_weight = sum(weights)
    remaining = max_total_trials

    for i, m in enumerate(all_hpo_models):
        if i == len(all_hpo_models) - 1:
            trials = remaining
        else:
            trials = max(1, int(max_total_trials * weights[i] / total_weight))
        trials = max(1, min(trials, remaining))
        remaining -= trials
        allocations.append(TrialAllocationItem(model_id=m["model_id"], max_trials=trials))

    return allocations
