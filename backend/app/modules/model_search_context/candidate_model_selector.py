import logging
from typing import List
from app.shared.registry.model_registry import get_model_spec, get_baseline_models
from app.modules.model_search_context.schemas import (
    BaselineModelPlan,
    CandidateModelPlan,
    ExcludedModelPlan,
)
from app.modules.model_search_context.enums import ModelPriority

logger = logging.getLogger(__name__)


def select_candidate_models(
    updated_model_strategy: dict,
    allowed_model_families: List[str],
    task_type: str,
    include_models: List[str],
    exclude_models: List[str],
) -> dict:
    """Derive candidate model plan from the context's updated_model_strategy.

    Uses candidate_model_families, baseline_models, excluded_model_families,
    and selected_model_actions from the updated model strategy — all of which
    were already decided by the Model Search Context Update module's LLM.
    No separate LLM call is made here.
    """
    candidate_families = updated_model_strategy.get("candidate_model_families", [])
    baseline_families = updated_model_strategy.get("baseline_models", [])
    excluded_families = set(updated_model_strategy.get("excluded_model_families", []))
    selected_actions = updated_model_strategy.get("selected_model_actions", [])

    # Build a priority lookup from selected_model_actions
    priority_from_action: dict = {}
    reason_from_action: dict = {}
    for action in selected_actions:
        family = action.get("model_family", "")
        priority_from_action[family] = action.get("priority", "recommended")
        rationale = action.get("decision_rationale", {})
        reason_from_action[family] = rationale.get("reason", "")

    # Map action priority strings to ModelPriority enum values
    _action_priority_map = {
        "required": ModelPriority.HIGH,
        "recommended": ModelPriority.HIGH,
        "optional": ModelPriority.MEDIUM,
        "fallback": ModelPriority.LOW,
    }

    # Apply user include/exclude overrides
    if include_models:
        effective_candidates = [m for m in include_models if m in allowed_model_families]
    else:
        effective_candidates = [m for m in candidate_families if m in allowed_model_families]

    effective_candidates = [m for m in effective_candidates if m not in exclude_models]
    effective_candidates = [m for m in effective_candidates if m not in excluded_families]

    # Build baseline models — system enforces exactly ONE baseline
    baseline_plans: List[BaselineModelPlan] = []
    effective_baselines = [m for m in baseline_families if m in allowed_model_families]
    effective_baselines = [m for m in effective_baselines if m not in exclude_models]

    # Take only the first baseline from the strategy (single baseline rule)
    if effective_baselines:
        effective_baselines = effective_baselines[:1]

    for model_id in effective_baselines:
        spec = get_model_spec(model_id)
        if not spec or task_type not in spec.get("supported_task_types", []):
            continue
        role = "strong_baseline" if spec.get("complexity_level") != "baseline" else "baseline"
        hpo_enabled = role == "strong_baseline"
        baseline_plans.append(BaselineModelPlan(
            model_id=model_id,
            role=role,
            hpo_enabled=hpo_enabled,
        ))

    # Ensure exactly one system baseline if none selected or the selected one is invalid
    if not baseline_plans:
        system_baselines = get_baseline_models(task_type)
        for mid in system_baselines:
            if mid not in exclude_models:
                spec = get_model_spec(mid)
                if spec and task_type in spec.get("supported_task_types", []):
                    baseline_plans.append(BaselineModelPlan(
                        model_id=mid,
                        role="baseline",
                        hpo_enabled=False,
                    ))
                    break

    # Build candidate models (exclude any already used as baseline)
    existing_baselines = {b.model_id for b in baseline_plans}
    candidate_plans: List[CandidateModelPlan] = []
    candidate_ids = [m for m in effective_candidates if m not in existing_baselines]

    for model_id in candidate_ids:
        spec = get_model_spec(model_id)
        if not spec or task_type not in spec.get("supported_task_types", []):
            continue

        action_priority = priority_from_action.get(model_id)
        if action_priority:
            priority = _action_priority_map.get(action_priority, ModelPriority.MEDIUM)
        else:
            priority = _default_priority(spec)

        reason = reason_from_action.get(model_id) or _default_reason(spec, task_type)
        hpo_enabled = spec.get("complexity_level") != "baseline"

        candidate_plans.append(CandidateModelPlan(
            model_id=model_id,
            model_family=spec.get("family", model_id),
            priority=priority,
            hpo_enabled=hpo_enabled,
            reason=reason,
        ))

    # Build excluded models from strategy
    excluded_plans: List[ExcludedModelPlan] = []
    rejected_actions = updated_model_strategy.get("rejected_model_actions", [])
    for action in rejected_actions:
        family = action.get("model_family", "")
        reason = action.get("reason", "")
        if family not in exclude_models:
            excluded_plans.append(ExcludedModelPlan(model_id=family, reason=reason))

    # Also include excluded_model_families that don't appear in rejected_model_actions
    recorded_excluded = {e.model_id for e in excluded_plans}
    for family in excluded_families:
        if family not in recorded_excluded and family not in exclude_models:
            excluded_plans.append(ExcludedModelPlan(
                model_id=family,
                reason="Excluded by model search strategy.",
            ))

    return {
        "baseline_models": baseline_plans,
        "candidate_models": candidate_plans,
        "excluded_models": excluded_plans,
    }


def _default_priority(spec: dict) -> str:
    level = spec.get("complexity_level", "moderate")
    if level == "simple":
        return ModelPriority.HIGH
    elif level == "moderate":
        return ModelPriority.HIGH
    elif level == "high":
        return ModelPriority.MEDIUM
    return ModelPriority.MEDIUM


def _default_reason(spec: dict, task_type: str) -> str:
    display = spec.get("display_name", spec.get("family", ""))
    return f"{display} is compatible with {task_type} tasks."
