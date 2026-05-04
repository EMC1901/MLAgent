import logging
import re
from typing import Dict, Any, List
from app.shared.config.settings import settings
from app.shared.registry.model_registry import is_valid_model_family
from app.shared.registry.hpo_registry import is_valid_hpo_method
from app.modules.model_search.schemas import SystemValidationResult

logger = logging.getLogger(__name__)

_CODE_PATTERNS = [
    r"\bimport\s+\w+",
    r"\bdef\s+\w+\s*\(",
    r"\.fit\s*\(",
    r"\.predict\s*\(",
    r"\.train\s*\(",
    r"optuna\.create_study",
    r"GridSearchCV|RandomizedSearchCV",
    r"sklearn\.",
    r"Pipeline\s*\(",
    r"make_pipeline",
    r"exec\s*\(",
    r"eval\s*\(",
    r"os\.system",
    r"subprocess\.",
    r"__import__",
]


def validate_llm_advice(parsed_advice: dict, allowed_model_families: List[str], allowed_hpo_methods: List[str]) -> dict:
    rejected_models: List[str] = []
    rejected_hpo_methods: List[str] = []
    warnings_list: List[str] = []
    fallback_applied = False

    # 1. Security check: scan for executable code patterns
    advice_str = str(parsed_advice)
    for pattern in _CODE_PATTERNS:
        if re.search(pattern, advice_str, re.IGNORECASE):
            rejected_models.append(f"executable code pattern detected: '{pattern}'")
            fallback_applied = True

    # 2. Validate recommended_model_ids
    recommended = parsed_advice.get("recommended_model_ids", [])
    valid_recommended = []
    for model_id in recommended:
        if is_valid_model_family(str(model_id)):
            valid_recommended.append(str(model_id))
        else:
            rejected_models.append(f"model_id: '{model_id}' not in Model Registry")
            fallback_applied = True
    parsed_advice["recommended_model_ids"] = valid_recommended

    # 3. Validate baseline_model_ids
    baselines = parsed_advice.get("baseline_model_ids", [])
    valid_baselines = [m for m in baselines if is_valid_model_family(str(m))]
    for m in set(baselines) - set(valid_baselines):
        rejected_models.append(f"baseline_model_id: '{m}' not in Model Registry")
        fallback_applied = True
    parsed_advice["baseline_model_ids"] = valid_baselines

    # 4. Validate excluded_model_ids
    excluded = parsed_advice.get("excluded_model_ids", [])
    for item in excluded:
        if isinstance(item, dict):
            mid = item.get("model_id", "")
            if mid and is_valid_model_family(str(mid)):
                # Valid model being excluded - that's fine, just note it
                pass

    # 5. Validate HPO recommendation
    hpo_rec = parsed_advice.get("hpo_recommendation", {})
    if isinstance(hpo_rec, dict):
        search_method = hpo_rec.get("search_method")
        if search_method and not is_valid_hpo_method(str(search_method)):
            rejected_hpo_methods.append(f"hpo_method: '{search_method}' not in HPO Registry")
            hpo_rec["search_method"] = "random_search"
            fallback_applied = True

        max_trials = hpo_rec.get("max_total_trials", 30)
        max_allowed = getattr(settings, "MODEL_SEARCH_MAX_TOTAL_TRIALS", 50)
        if isinstance(max_trials, (int, float)) and max_trials > max_allowed:
            rejected_hpo_methods.append(
                f"max_total_trials: {max_trials} exceeds system limit {max_allowed}"
            )
            hpo_rec["max_total_trials"] = max_allowed
            fallback_applied = True

    # 6. Validate model_priority_notes
    priority_notes = parsed_advice.get("model_priority_notes", [])
    valid_priorities = {"high", "medium", "low"}
    for note in priority_notes:
        if isinstance(note, dict):
            if note.get("priority") not in valid_priorities:
                note["priority"] = "medium"
            mid = note.get("model_id", "")
            if mid and not is_valid_model_family(str(mid)):
                note["valid_model"] = False

    # 7. Validate confidence_score
    confidence = parsed_advice.get("confidence_score", 0.0)
    if isinstance(confidence, (int, float)) and (confidence < 0.0 or confidence > 1.0):
        warnings_list.append("confidence_score out of [0,1] range; clamped.")
        parsed_advice["confidence_score"] = max(0.0, min(1.0, confidence))

    is_valid = len(rejected_models) == 0 and len(rejected_hpo_methods) == 0

    if rejected_models or rejected_hpo_methods:
        logger.warning(
            "LLM model search advice validation - rejected models: %s, rejected HPO: %s",
            rejected_models, rejected_hpo_methods,
        )

    validation_result = SystemValidationResult(
        is_valid=is_valid,
        rejected_models=rejected_models,
        rejected_hpo_methods=rejected_hpo_methods,
        fallback_applied=fallback_applied,
        warnings=warnings_list,
    )

    return {
        "is_valid": is_valid,
        "rejected_models": rejected_models,
        "rejected_hpo_methods": rejected_hpo_methods,
        "fallback_applied": fallback_applied,
        "warnings": warnings_list,
        "validated_advice": parsed_advice,
        "validation_result": validation_result,
    }
