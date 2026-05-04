def adjust_model_strategy(
    original: dict, llm_advice: dict, dataset_analysis: dict, feature_group_analysis: dict,
) -> dict:
    updated = dict(original)
    model_suggestion = llm_advice.get("model_strategy_suggestion") or {}

    if model_suggestion.get("candidate_model_families"):
        updated["candidate_model_families"] = model_suggestion["candidate_model_families"]

    if model_suggestion.get("baseline_models"):
        updated["baseline_models"] = model_suggestion["baseline_models"]

    if model_suggestion.get("preferred_model_bias"):
        updated["preferred_model_bias"] = model_suggestion["preferred_model_bias"]

    return updated
