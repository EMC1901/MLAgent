def adjust_validation_strategy(
    original: dict, llm_advice: dict, dataset_analysis: dict,
) -> dict:
    updated = dict(original)
    val_suggestion = llm_advice.get("validation_strategy_suggestion") or {}

    is_small = dataset_analysis.get("is_small_sample", False)

    if val_suggestion.get("split_strategy"):
        updated["split_strategy"] = val_suggestion["split_strategy"]

    if val_suggestion.get("n_splits"):
        updated["n_splits"] = val_suggestion["n_splits"]

    if is_small and updated.get("n_splits", 5) > 5:
        updated["n_splits"] = 5

    updated.setdefault("random_state", 42)

    return updated
