from app.modules.model_search_context.enums import HPOBudgetLevel


def adjust_hpo_strategy(
    original: dict, llm_advice: dict, dataset_analysis: dict,
) -> dict:
    updated = dict(original)
    hpo_suggestion = llm_advice.get("hpo_strategy_suggestion") or {}

    is_small = dataset_analysis.get("is_small_sample", False)
    is_low_feature = dataset_analysis.get("is_low_feature", False)

    if hpo_suggestion.get("search_method"):
        updated["search_method"] = hpo_suggestion["search_method"]

    if hpo_suggestion.get("max_trials"):
        updated["max_trials"] = hpo_suggestion["max_trials"]

    if hpo_suggestion.get("budget_level"):
        updated["budget_level"] = hpo_suggestion["budget_level"]

    # System safety constraint: small samples / low features force reduced HPO
    if is_small or is_low_feature:
        updated["budget_level"] = HPOBudgetLevel.LOW
        updated["max_trials"] = min(updated.get("max_trials", 30), 20)

    updated["enabled"] = True

    return updated
