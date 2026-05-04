import logging
from typing import List
from app.shared.registry.model_registry import get_model_spec, get_baseline_models
from app.modules.model_search.schemas import (
    BaselineModelPlan,
    CandidateModelPlan,
    ExcludedModelPlan,
    CandidateModelPlanGroup,
)
from app.modules.model_search.enums import ModelPriority

logger = logging.getLogger(__name__)


def select_candidate_models(
    llm_advice: dict,
    allowed_model_families: List[str],
    task_type: str,
    use_llm_advisor: bool,
    include_models: List[str],
    exclude_models: List[str],
) -> dict:
    """Generate candidate model plan based on LLM advice + registry + user overrides."""
    recommended_ids = llm_advice.get("recommended_model_ids", [])
    baseline_ids = llm_advice.get("baseline_model_ids", [])
    excluded_from_llm = {
        item["model_id"]: item.get("reason", "")
        for item in llm_advice.get("excluded_model_ids", [])
        if isinstance(item, dict) and "model_id" in item
    }
    priority_notes = {
        note["model_id"]: note
        for note in llm_advice.get("model_priority_notes", [])
        if isinstance(note, dict) and "model_id" in note
    }

    # Build baseline models
    baseline_plans: List[BaselineModelPlan] = []
    system_baselines = get_baseline_models(task_type)

    for model_id in baseline_ids if use_llm_advisor else system_baselines:
        if model_id in exclude_models:
            continue
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

    # Ensure at least one baseline from system defaults
    existing_baselines = {b.model_id for b in baseline_plans}
    for mid in system_baselines:
        if mid not in existing_baselines and mid not in exclude_models:
            spec = get_model_spec(mid)
            if spec and task_type in spec.get("supported_task_types", []):
                baseline_plans.append(BaselineModelPlan(
                    model_id=mid,
                    role="baseline",
                    hpo_enabled=False,
                ))
                break

    # Build candidate models
    candidate_plans: List[CandidateModelPlan] = []
    candidate_ids = recommended_ids if use_llm_advisor else [
        m for m in allowed_model_families
        if get_model_spec(m) and get_model_spec(m).get("complexity_level") != "baseline"
    ]

    # Apply user include/exclude
    if include_models:
        candidate_ids = [m for m in include_models if m in allowed_model_families]
    candidate_ids = [m for m in candidate_ids if m not in exclude_models]

    # Remove baseline models from candidates to avoid duplicates
    candidate_ids = [m for m in candidate_ids if m not in existing_baselines]

    for model_id in candidate_ids:
        spec = get_model_spec(model_id)
        if not spec or task_type not in spec.get("supported_task_types", []):
            continue

        priority_note = priority_notes.get(model_id, {})
        priority = priority_note.get("priority", _default_priority(spec))
        reason = priority_note.get("reason") or _default_reason(spec, task_type)
        hpo_enabled = spec.get("complexity_level") != "baseline"

        candidate_plans.append(CandidateModelPlan(
            model_id=model_id,
            model_family=spec.get("family", model_id),
            priority=priority,
            hpo_enabled=hpo_enabled,
            reason=reason,
        ))

    # Build excluded models
    excluded_plans: List[ExcludedModelPlan] = []
    for model_id, reason in excluded_from_llm.items():
        if model_id not in exclude_models:
            excluded_plans.append(ExcludedModelPlan(model_id=model_id, reason=reason))

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
