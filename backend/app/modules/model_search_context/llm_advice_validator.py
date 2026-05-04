import logging
from typing import Dict, Any, List
from app.shared.config.settings import settings
from app.shared.registry.model_registry import is_valid_model_family
from app.shared.registry.hpo_registry import is_valid_hpo_method
from app.modules.model_search_context.schemas import SystemValidationResult

logger = logging.getLogger(__name__)

_VALID_SPLIT_STRATEGIES = [
    "train_test_split", "k_fold_cross_validation",
    "stratified_k_fold", "repeated_cv",
]


def validate_llm_advice(parsed_advice: dict, task_type: str) -> dict:
    rejected = []
    warnings = []
    fallback_applied = False

    # 1. Validate model_strategy_suggestion
    model_suggestion = parsed_advice.get("model_strategy_suggestion") or {}
    candidate_families = model_suggestion.get("candidate_model_families", [])
    if candidate_families:
        valid_families = []
        for family in candidate_families:
            if is_valid_model_family(str(family)):
                valid_families.append(str(family))
            else:
                rejected.append(f"model_family: '{family}' is not in Model Registry")
                fallback_applied = True
        model_suggestion["candidate_model_families"] = valid_families

        baseline_models = model_suggestion.get("baseline_models", [])
        valid_baselines = [
            m for m in baseline_models if is_valid_model_family(str(m))
        ]
        invalid_baselines = set(baseline_models) - set(valid_baselines)
        for m in invalid_baselines:
            rejected.append(f"baseline_model: '{m}' is not in Model Registry")
        model_suggestion["baseline_models"] = valid_baselines

    # 2. Validate HPO strategy suggestion
    hpo_suggestion = parsed_advice.get("hpo_strategy_suggestion") or {}
    search_method = hpo_suggestion.get("search_method")
    if search_method and not is_valid_hpo_method(str(search_method)):
        rejected.append(f"hpo_method: '{search_method}' is not in HPO Registry")
        hpo_suggestion["search_method"] = "random_search"
        fallback_applied = True

    max_trials = hpo_suggestion.get("max_trials", 30)
    max_allowed = getattr(settings, "MODEL_CONTEXT_MAX_HPO_TRIALS", 50)
    if isinstance(max_trials, (int, float)) and max_trials > max_allowed:
        rejected.append(
            f"max_trials: {max_trials} exceeds system limit of {max_allowed}"
        )
        hpo_suggestion["max_trials"] = max_allowed
        fallback_applied = True

    # 3. Validate validation strategy
    val_suggestion = parsed_advice.get("validation_strategy_suggestion") or {}
    split_strategy = val_suggestion.get("split_strategy")
    if split_strategy and split_strategy not in _VALID_SPLIT_STRATEGIES:
        rejected.append(f"split_strategy: '{split_strategy}' is not valid")
        val_suggestion["split_strategy"] = "k_fold_cross_validation"
        fallback_applied = True

    n_splits = val_suggestion.get("n_splits", 5)
    if isinstance(n_splits, (int, float)) and (n_splits < 2 or n_splits > 10):
        rejected.append(f"n_splits: {n_splits} must be between 2 and 10")
        val_suggestion["n_splits"] = 5
        fallback_applied = True

    # 4. Validate confidence score
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
