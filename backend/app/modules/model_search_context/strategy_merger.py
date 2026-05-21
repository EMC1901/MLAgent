import logging
from typing import Dict, Any, List, Optional
from app.modules.model_search_context.schemas import StrategyAdjustment, StrategyChange

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
    """Merge LLM strategy changes with original strategies, tracking all diffs with rationale."""

    model_strategy = dict(original_model_strategy)
    hpo_strategy = dict(original_hpo_strategy)
    validation_strategy = dict(original_validation_strategy)
    evaluation_strategy = dict(original_evaluation_strategy)

    strategy_mapping = {
        "model": model_strategy,
        "hpo": hpo_strategy,
        "validation": validation_strategy,
        "evaluation": evaluation_strategy,
    }

    adjust_flags = {
        "model": adjust_model,
        "hpo": adjust_hpo,
        "validation": adjust_validation,
        "evaluation": adjust_evaluation,
    }

    llm_advice = validated_llm_advice or {}
    llm_changes = llm_advice.get("strategy_changes", []) or []

    applied_changes = []
    model_adjusted = False
    hpo_adjusted = False
    validation_adjusted = False
    evaluation_adjusted = False

    for change_data in llm_changes:
        strategy_area = change_data.get("strategy_area", "")
        field_path = change_data.get("field_path", "")
        change_type = change_data.get("change_type", "modified")

        if strategy_area not in strategy_mapping:
            continue

        target_strategy = strategy_mapping[strategy_area]
        original_value = change_data.get("original_value")
        updated_value = change_data.get("updated_value")
        rationale = change_data.get("decision_rationale")

        # Verify original_value matches actual current value (sanity check)
        actual_current = target_strategy.get(field_path)
        if change_type in ("modified", "confirmed", "removed") and original_value is not None:
            if not _values_equal(original_value, actual_current):
                logger.warning(
                    "LLM original_value for %s.%s doesn't match actual — using actual value",
                    strategy_area, field_path,
                )

        # Build the StrategyChange record
        strategy_change = StrategyChange(
            strategy_area=strategy_area,
            field_path=field_path,
            original_value=actual_current if actual_current is not None else original_value,
            updated_value=updated_value,
            change_type=change_type,
            decision_rationale=rationale,
        )

        # Apply the change if adjustment is enabled and type is not 'confirmed'
        if adjust_flags.get(strategy_area, True) and change_type != "confirmed":
            if change_type == "modified" and field_path in target_strategy:
                target_strategy[field_path] = updated_value
            elif change_type == "added":
                target_strategy[field_path] = updated_value
            elif change_type == "removed" and field_path in target_strategy:
                del target_strategy[field_path]

            # Track which areas were adjusted
            if strategy_area == "model":
                model_adjusted = True
            elif strategy_area == "hpo":
                hpo_adjusted = True
            elif strategy_area == "validation":
                validation_adjusted = True
            elif strategy_area == "evaluation":
                evaluation_adjusted = True

        applied_changes.append(strategy_change)

    # Apply system safety constraints and record them as system-generated changes
    system_changes = _apply_system_constraints(
        model_strategy, hpo_strategy, validation_strategy,
        dataset_analysis, feature_group_analysis, adjust_flags,
    )
    for sc in system_changes:
        applied_changes.append(sc)
        if sc.strategy_area == "hpo":
            hpo_adjusted = True
        elif sc.strategy_area == "validation":
            validation_adjusted = True

    # Build adjustment reasons from applied changes
    adjustment_reasons = []
    for change in applied_changes:
        area = change.strategy_area
        field = change.field_path
        ctype = change.change_type
        if ctype == "modified":
            adjustment_reasons.append(f"{area}.{field}: modified")
        elif ctype == "added":
            adjustment_reasons.append(f"{area}.{field}: added")
        elif ctype == "removed":
            adjustment_reasons.append(f"{area}.{field}: removed")

    strategy_adjustment = StrategyAdjustment(
        model_strategy_adjusted=model_adjusted,
        hpo_strategy_adjusted=hpo_adjusted,
        validation_strategy_adjusted=validation_adjusted,
        evaluation_strategy_adjusted=evaluation_adjusted,
        adjustment_reasons=adjustment_reasons,
    )

    # Pass through LLM's trial_allocation and search_space_overrides if provided
    llm_trial_allocation = llm_advice.get("trial_allocation", []) if isinstance(llm_advice, dict) else []
    llm_search_space_overrides = llm_advice.get("search_space_overrides", []) if isinstance(llm_advice, dict) else []

    return {
        "updated_model_strategy": model_strategy,
        "updated_hpo_strategy": hpo_strategy,
        "updated_validation_strategy": validation_strategy,
        "updated_evaluation_strategy": evaluation_strategy,
        "strategy_adjustment": strategy_adjustment,
        "strategy_changes": applied_changes,
        "strategy_change_summary": llm_advice.get("strategy_change_summary", ""),
        "llm_trial_allocation": llm_trial_allocation,
        "llm_search_space_overrides": llm_search_space_overrides,
    }


def _apply_system_constraints(
    model_strategy: dict,
    hpo_strategy: dict,
    validation_strategy: dict,
    dataset_analysis: dict,
    feature_group_analysis: dict,
    adjust_flags: dict,
) -> List[StrategyChange]:
    """Apply system safety constraints and return them as system-generated StrategyChanges."""
    changes = []

    n_final = dataset_analysis.get("n_final_features", 0)
    n_samples = dataset_analysis.get("n_samples", 0)
    is_small = dataset_analysis.get("is_small_sample", False)
    is_low_feature = dataset_analysis.get("is_low_feature", False)

    # HPO budget constraint for small/low-feature datasets
    if (is_small or is_low_feature) and adjust_flags.get("hpo", True):
        orig_budget = hpo_strategy.get("budget_level", "moderate")
        if orig_budget not in ("low",):
            hpo_strategy["budget_level"] = "low"
            changes.append(StrategyChange(
                strategy_area="hpo",
                field_path="budget_level",
                original_value=orig_budget,
                updated_value="low",
                change_type="modified",
                decision_rationale={
                    "reason": f"System override: reduced HPO budget due to {'small sample size' if is_small else ''}{' and ' if is_small and is_low_feature else ''}{'low feature count' if is_low_feature else ''}.",
                    "evidence": [f"n_samples={n_samples}", f"n_final_features={n_final}"],
                    "expected_benefit": "Prevents overfitting from excessive hyperparameter exploration on limited data.",
                    "risk": "May miss optimal hyperparameters if search space is too coarse.",
                    "fallback": "If initial results are poor, manually increase budget and re-run.",
                },
            ))

        orig_trials = hpo_strategy.get("max_trials", 30)
        if orig_trials > 20:
            hpo_strategy["max_trials"] = 20
            changes.append(StrategyChange(
                strategy_area="hpo",
                field_path="max_trials",
                original_value=orig_trials,
                updated_value=20,
                change_type="modified",
                decision_rationale={
                    "reason": "System override: capped max_trials to 20 due to small sample / low feature constraints.",
                    "evidence": [f"Original max_trials={orig_trials}", f"n_samples={n_samples}", f"n_final_features={n_final}"],
                    "expected_benefit": "Faster convergence and reduced risk of overfitting on limited data.",
                    "risk": "Fewer trials may not find the global optimum.",
                    "fallback": "Re-run HPO with higher max_trials if cross-validation scores are poor.",
                },
            ))

    # CV splits constraint for small samples
    if is_small and adjust_flags.get("validation", True):
        orig_n_splits = validation_strategy.get("n_splits", 5)
        if orig_n_splits > 5:
            validation_strategy["n_splits"] = 5
            changes.append(StrategyChange(
                strategy_area="validation",
                field_path="n_splits",
                original_value=orig_n_splits,
                updated_value=5,
                change_type="modified",
                decision_rationale={
                    "reason": f"System override: reduced CV splits from {orig_n_splits} to 5 due to small sample size ({n_samples}).",
                    "evidence": [f"n_samples={n_samples}"],
                    "expected_benefit": "Each fold has enough samples for meaningful evaluation.",
                    "risk": "Fewer folds means higher variance in CV estimates.",
                    "fallback": "If CV scores are unstable, switch to repeated_cv with fewer splits.",
                },
            ))

    return changes


def _values_equal(a: Any, b: Any) -> bool:
    """Compare two values loosely, handling list/set ordering."""
    if isinstance(a, list) and isinstance(b, list):
        return sorted(str(x) for x in a) == sorted(str(x) for x in b)
    if isinstance(a, (list, dict)) or isinstance(b, (list, dict)):
        return str(a) == str(b)
    return a == b
