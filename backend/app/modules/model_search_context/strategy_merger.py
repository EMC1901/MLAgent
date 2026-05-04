import logging
from typing import Dict, Any
from app.modules.model_search_context.schemas import StrategyAdjustment, LLMStrategyAdvice

logger = logging.getLogger(__name__)


def merge_strategies(
    original_model_strategy: dict,
    original_hpo_strategy: dict,
    original_validation_strategy: dict,
    original_evaluation_strategy: dict,
    validated_llm_advice: dict,
    dataset_analysis: dict,
    feature_group_analysis: dict,
    preprocessing_analysis: dict,
    adjust_model: bool = True,
    adjust_hpo: bool = True,
    adjust_validation: bool = True,
    adjust_evaluation: bool = False,
) -> dict:

    model_strategy = dict(original_model_strategy)
    hpo_strategy = dict(original_hpo_strategy)
    validation_strategy = dict(original_validation_strategy)
    evaluation_strategy = dict(original_evaluation_strategy)

    adjustment_reasons = []
    model_adjusted = False
    hpo_adjusted = False
    validation_adjusted = False
    evaluation_adjusted = False

    llm_advice = validated_llm_advice or {}

    # ---- Model Strategy ----
    if adjust_model:
        updated_model, model_reasons = _adjust_model_strategy(
            model_strategy, llm_advice, dataset_analysis, feature_group_analysis,
        )
        if model_reasons:
            model_strategy = updated_model
            model_adjusted = True
            adjustment_reasons.extend(model_reasons)

    # ---- HPO Strategy ----
    if adjust_hpo:
        updated_hpo, hpo_reasons = _adjust_hpo_strategy(
            hpo_strategy, llm_advice, dataset_analysis,
        )
        if hpo_reasons:
            hpo_strategy = updated_hpo
            hpo_adjusted = True
            adjustment_reasons.extend(hpo_reasons)

    # ---- Validation Strategy ----
    if adjust_validation:
        updated_val, val_reasons = _adjust_validation_strategy(
            validation_strategy, llm_advice, dataset_analysis,
        )
        if val_reasons:
            validation_strategy = updated_val
            validation_adjusted = True
            adjustment_reasons.extend(val_reasons)

    # ---- Evaluation Strategy (rarely adjusted) ----
    if adjust_evaluation:
        updated_eval, eval_reasons = _adjust_evaluation_strategy(
            evaluation_strategy, llm_advice,
        )
        if eval_reasons:
            evaluation_strategy = updated_eval
            evaluation_adjusted = True
            adjustment_reasons.extend(eval_reasons)

    strategy_adjustment = StrategyAdjustment(
        model_strategy_adjusted=model_adjusted,
        hpo_strategy_adjusted=hpo_adjusted,
        validation_strategy_adjusted=validation_adjusted,
        evaluation_strategy_adjusted=evaluation_adjusted,
        adjustment_reasons=adjustment_reasons,
    )

    return {
        "updated_model_strategy": model_strategy,
        "updated_hpo_strategy": hpo_strategy,
        "updated_validation_strategy": validation_strategy,
        "updated_evaluation_strategy": evaluation_strategy,
        "strategy_adjustment": strategy_adjustment,
    }


def _adjust_model_strategy(
    original: dict, llm_advice: dict, dataset_analysis: dict, feature_group_analysis: dict,
):
    reasons = []
    updated = dict(original)

    model_suggestion = llm_advice.get("model_strategy_suggestion") or {}
    llm_candidates = model_suggestion.get("candidate_model_families", [])

    n_final = dataset_analysis.get("n_final_features", 0)
    has_dropped = feature_group_analysis.get("has_dropped_groups", False)
    is_low_feature = dataset_analysis.get("is_low_feature", False)

    if llm_candidates:
        updated["candidate_model_families"] = llm_candidates
        reasons.append("llm_recommended_model_families")

    if llm_candidates and has_dropped and is_low_feature:
        reasons.append("low_effective_feature_count")
        reasons.append("feature_group_dropped")

    if model_suggestion.get("preferred_model_bias"):
        updated["preferred_model_bias"] = model_suggestion["preferred_model_bias"]

    if model_suggestion.get("baseline_models"):
        updated["baseline_models"] = model_suggestion["baseline_models"]

    return updated, reasons


def _adjust_hpo_strategy(
    original: dict, llm_advice: dict, dataset_analysis: dict,
):
    reasons = []
    updated = dict(original)

    hpo_suggestion = llm_advice.get("hpo_strategy_suggestion") or {}

    n_final = dataset_analysis.get("n_final_features", 0)
    n_samples = dataset_analysis.get("n_samples", 0)
    is_small = dataset_analysis.get("is_small_sample", False)
    is_low_feature = dataset_analysis.get("is_low_feature", False)

    if hpo_suggestion.get("search_method"):
        updated["search_method"] = hpo_suggestion["search_method"]
        reasons.append("llm_recommended_hpo_method")

    if hpo_suggestion.get("max_trials"):
        updated["max_trials"] = hpo_suggestion["max_trials"]

    if hpo_suggestion.get("budget_level"):
        updated["budget_level"] = hpo_suggestion["budget_level"]

    # System safety constraints override LLM
    if is_small or is_low_feature:
        updated["budget_level"] = "low"
        updated["max_trials"] = min(updated.get("max_trials", 30), 20)
        reasons.append("reduced_hpo_budget_due_to_data_constraints")

    return updated, reasons


def _adjust_validation_strategy(
    original: dict, llm_advice: dict, dataset_analysis: dict,
):
    reasons = []
    updated = dict(original)

    val_suggestion = llm_advice.get("validation_strategy_suggestion") or {}

    n_samples = dataset_analysis.get("n_samples", 0)
    is_small = dataset_analysis.get("is_small_sample", False)

    if val_suggestion.get("split_strategy"):
        updated["split_strategy"] = val_suggestion["split_strategy"]
        reasons.append("llm_recommended_validation_strategy")

    if val_suggestion.get("n_splits"):
        updated["n_splits"] = val_suggestion["n_splits"]

    if is_small and updated.get("n_splits", 5) > 5:
        updated["n_splits"] = 5
        reasons.append("reduced_cv_splits_for_small_sample")

    return updated, reasons


def _adjust_evaluation_strategy(
    original: dict, llm_advice: dict,
):
    reasons = []
    updated = dict(original)
    return updated, reasons
