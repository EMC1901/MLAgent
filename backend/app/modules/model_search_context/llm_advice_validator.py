import logging
from typing import Dict, Any, List
from app.shared.config.settings import settings
from app.shared.registry.model_registry import is_valid_model_family, MODEL_FAMILIES
from app.shared.registry.hpo_registry import is_valid_hpo_method

# Build display-name → family-name fallback mapping for LLM naming mistakes
_DISPLAY_NAME_TO_FAMILY: Dict[str, str] = {}
for mf in MODEL_FAMILIES:
    _DISPLAY_NAME_TO_FAMILY[mf["display_name"].lower()] = mf["family"]
    # Also map common variations
    _DISPLAY_NAME_TO_FAMILY[mf["family"].replace("_", " ")] = mf["family"]


def _resolve_model_family(name: str) -> str:
    """Resolve a model family name to its registry key, with fallback mapping."""
    if is_valid_model_family(name):
        return name
    # Try display-name → family-name fallback
    return _DISPLAY_NAME_TO_FAMILY.get(name.lower().strip(), name)
from app.modules.model_search_context.schemas import SystemValidationResult

logger = logging.getLogger(__name__)

_VALID_STRATEGY_AREAS = {"model", "hpo", "validation", "evaluation"}
_VALID_CHANGE_TYPES = {"modified", "added", "removed", "confirmed"}

# Known field paths for each strategy area (from workflow_planning schemas)
_VALID_FIELD_PATHS = {
    "model": {
        "candidate_model_families", "baseline_models", "preferred_model_bias",
        "excluded_model_families", "selected_model_actions", "rejected_model_actions",
        "model_selection_rationale_summary",
    },
    "hpo": {"enabled", "search_method", "budget_level", "max_trials", "search_space_width"},
    "validation": {"split_strategy", "n_splits", "test_size", "random_state", "stratification_required"},
    "evaluation": {"primary_metric", "secondary_metrics", "metric_direction"},
}


_VALID_SPLIT_STRATEGIES = {
    "train_test_split", "k_fold_cross_validation",
    "stratified_k_fold", "repeated_cv",
}


def validate_llm_advice(parsed_advice: dict, task_type: str) -> dict:
    rejected = []
    warnings = []
    fallback_applied = False

    strategy_changes = parsed_advice.get("strategy_changes", [])

    # 1. Validate strategy_changes structure
    if not strategy_changes or not isinstance(strategy_changes, list):
        rejected.append("strategy_changes is missing, empty, or not an array")
        fallback_applied = True
        strategy_changes = []

    valid_changes = []
    for i, change in enumerate(strategy_changes):
        change_errors = []
        change_key = f"strategy_changes[{i}]"

        strategy_area = change.get("strategy_area", "")
        field_path = change.get("field_path", "")
        change_type = change.get("change_type", "")
        rationale = change.get("decision_rationale", {}) or {}

        # Validate strategy_area
        if strategy_area not in _VALID_STRATEGY_AREAS:
            change_errors.append(f"{change_key}: invalid strategy_area '{strategy_area}'")
            fallback_applied = True

        # Validate field_path
        valid_fields = _VALID_FIELD_PATHS.get(strategy_area, set())
        if field_path not in valid_fields:
            if strategy_area in _VALID_STRATEGY_AREAS:
                warnings.append(f"{change_key}: unknown field_path '{field_path}' for area '{strategy_area}'")
            else:
                change_errors.append(f"{change_key}: unknown field_path '{field_path}'")
                fallback_applied = True

        # Validate change_type
        if change_type not in _VALID_CHANGE_TYPES:
            change_errors.append(f"{change_key}: invalid change_type '{change_type}'")
            fallback_applied = True

        # Validate decision_rationale
        if not rationale or not isinstance(rationale, dict):
            change_errors.append(f"{change_key}: missing or invalid decision_rationale")
            fallback_applied = True
        else:
            if not rationale.get("reason", "").strip():
                change_errors.append(f"{change_key}: decision_rationale.reason is empty")
                fallback_applied = True
            if not rationale.get("evidence") or not isinstance(rationale.get("evidence"), list):
                warnings.append(f"{change_key}: decision_rationale.evidence is empty or not an array")

        # Validate model family names in candidate_model_families
        if field_path == "candidate_model_families":
            updated = change.get("updated_value", [])
            if isinstance(updated, list):
                valid_families = []
                for family in updated:
                    resolved = _resolve_model_family(str(family))
                    if is_valid_model_family(resolved):
                        valid_families.append(resolved)
                        if resolved != str(family):
                            warnings.append(f"{change_key}: resolved '{family}' → '{resolved}' via display name mapping")
                    else:
                        rejected.append(f"model_family: '{family}' is not in Model Registry")
                        fallback_applied = True
                change["updated_value"] = list(dict.fromkeys(valid_families))  # dedupe preserving order

        # Validate model family names in baseline_models
        if field_path == "baseline_models":
            updated = change.get("updated_value", [])
            if isinstance(updated, list):
                if len(updated) > 1:
                    rejected.append(f"{change_key}: baseline_models must contain exactly 1 model, got {len(updated)}. Using only the first one.")
                    updated = updated[:1]
                    fallback_applied = True
                valid_baselines = []
                for m in updated:
                    resolved = _resolve_model_family(str(m))
                    if is_valid_model_family(resolved):
                        valid_baselines.append(resolved)
                        if resolved != str(m):
                            warnings.append(f"{change_key}: resolved baseline '{m}' → '{resolved}' via display name mapping")
                    else:
                        rejected.append(f"baseline_model: '{m}' is not in Model Registry")
                change["updated_value"] = list(dict.fromkeys(valid_baselines))  # dedupe preserving order

        # Validate HPO search_method
        if field_path == "search_method":
            updated = change.get("updated_value", "")
            if updated and not is_valid_hpo_method(str(updated)):
                rejected.append(f"hpo_method: '{updated}' is not in HPO Registry")
                change["updated_value"] = "random_search"
                fallback_applied = True

        # Clamp max_trials
        if field_path == "max_trials":
            updated = change.get("updated_value", 30)
            max_allowed = getattr(settings, "MODEL_CONTEXT_MAX_HPO_TRIALS", 50)
            if isinstance(updated, (int, float)) and updated > max_allowed:
                rejected.append(f"max_trials: {updated} exceeds system limit of {max_allowed}")
                change["updated_value"] = max_allowed
                fallback_applied = True

        # Validate split_strategy
        if field_path == "split_strategy":
            updated = change.get("updated_value", "")
            if updated and updated not in _VALID_SPLIT_STRATEGIES:
                rejected.append(f"split_strategy: '{updated}' is not valid")
                change["updated_value"] = "k_fold_cross_validation"
                fallback_applied = True

        # Validate search_space_width
        if field_path == "search_space_width":
            updated = change.get("updated_value", "moderate")
            if updated not in ("narrow", "moderate", "wide"):
                rejected.append(f"search_space_width: '{updated}' is not valid (must be narrow, moderate, or wide)")
                change["updated_value"] = "moderate"
                fallback_applied = True

        if change_errors:
            rejected.extend(change_errors)
        else:
            valid_changes.append(change)

    parsed_advice["strategy_changes"] = valid_changes

    # 1b. Validate trial_allocation (top-level field)
    trial_allocation = parsed_advice.get("trial_allocation", [])
    if trial_allocation and isinstance(trial_allocation, list):
        valid_allocations = []
        for i, alloc in enumerate(trial_allocation):
            alloc_key = f"trial_allocation[{i}]"
            family = str(alloc.get("model_family", "")) if alloc.get("model_family") else ""
            resolved = _resolve_model_family(family)
            if not is_valid_model_family(resolved):
                rejected.append(f"{alloc_key}: model_family '{family}' is not in Model Registry")
                fallback_applied = True
                continue
            trials = alloc.get("max_trials", 0)
            max_allowed_trials = getattr(settings, "MODEL_CONTEXT_MAX_HPO_TRIALS", 50)
            if not isinstance(trials, (int, float)) or trials < 0 or trials > max_allowed_trials:
                rejected.append(f"{alloc_key}: max_trials {trials} is out of range [0, {max_allowed_trials}]")
                fallback_applied = True
                continue
            rationale = alloc.get("allocation_rationale", "")
            if not rationale or not isinstance(rationale, str) or not rationale.strip():
                warnings.append(f"{alloc_key}: missing or empty allocation_rationale")
            valid_allocations.append({
                "model_family": resolved,
                "max_trials": int(trials),
                "allocation_rationale": rationale.strip() if rationale else "",
            })
        parsed_advice["trial_allocation"] = valid_allocations
    else:
        parsed_advice["trial_allocation"] = []

    # 1c. Validate search_space_overrides (top-level field)
    search_space_overrides = parsed_advice.get("search_space_overrides", [])
    if search_space_overrides and isinstance(search_space_overrides, list):
        valid_overrides = []
        for i, override in enumerate(search_space_overrides):
            ovr_key = f"search_space_overrides[{i}]"
            family = str(override.get("model_family", "")) if override.get("model_family") else ""
            resolved = _resolve_model_family(family)
            if not is_valid_model_family(resolved):
                rejected.append(f"{ovr_key}: model_family '{family}' is not in Model Registry")
                fallback_applied = True
                continue
            param_name = str(override.get("parameter_name", "")).strip()
            if not param_name:
                rejected.append(f"{ovr_key}: missing parameter_name")
                fallback_applied = True
                continue
            rationale = override.get("override_rationale", "")
            if not rationale or not isinstance(rationale, str) or not rationale.strip():
                warnings.append(f"{ovr_key}: missing or empty override_rationale")
            valid_overrides.append({
                "model_family": resolved,
                "parameter_name": param_name,
                "low": override.get("low"),
                "high": override.get("high"),
                "choices": override.get("choices"),
                "override_rationale": rationale.strip() if rationale else "",
            })
        parsed_advice["search_space_overrides"] = valid_overrides
    else:
        parsed_advice["search_space_overrides"] = []

    # 2. Validate confidence score
    confidence = parsed_advice.get("confidence_score", 0.0)
    if isinstance(confidence, (int, float)) and (confidence < 0.0 or confidence > 1.0):
        warnings.append("confidence_score out of [0,1] range; clamped.")
        parsed_advice["confidence_score"] = max(0.0, min(1.0, confidence))

    is_valid = len(rejected) == 0

    if rejected:
        logger.warning("LLM advice validation rejected items: %s", rejected)

    validation_result = SystemValidationResult(
        is_valid=is_valid,
        rejected_suggestions=rejected,
        fallback_applied=fallback_applied,
    )

    return {
        "is_valid": is_valid,
        "rejected_suggestions": rejected,
        "warnings": warnings,
        "fallback_applied": fallback_applied,
        "validated_advice": parsed_advice,
        "validation_result": validation_result,
    }
