import json
from typing import Tuple
from app.shared.registry.model_registry import get_model_families_for_task_type, get_baseline_models, get_all_model_families
from app.shared.registry.hpo_registry import get_all_hpo_methods


OUTPUT_JSON_SCHEMA = {
    "type": "object",
    "required": [
        "model_strategy_suggestion",
        "hpo_strategy_suggestion",
        "validation_strategy_suggestion",
        "adjustment_reasons",
        "risk_notes",
        "confidence_score",
    ],
    "properties": {
        "model_strategy_suggestion": {
            "type": "object",
            "required": ["candidate_model_families", "baseline_models", "preferred_model_bias"],
            "properties": {
                "candidate_model_families": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Model families selected ONLY from allowed_model_families.",
                },
                "baseline_models": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Simple baseline models to compare against.",
                },
                "preferred_model_bias": {
                    "type": "string",
                    "enum": [
                        "balanced_accuracy_and_stability",
                        "favor_accuracy",
                        "favor_stability",
                        "favor_interpretability",
                    ],
                },
            },
        },
        "hpo_strategy_suggestion": {
            "type": "object",
            "required": ["budget_level", "max_trials", "search_method"],
            "properties": {
                "budget_level": {
                    "type": "string",
                    "enum": ["low", "moderate", "high"],
                },
                "max_trials": {"type": "integer", "minimum": 1, "maximum": 50},
                "search_method": {
                    "type": "string",
                    "description": "HPO method selected ONLY from allowed_hpo_methods.",
                },
            },
        },
        "validation_strategy_suggestion": {
            "type": "object",
            "required": ["split_strategy", "n_splits"],
            "properties": {
                "split_strategy": {
                    "type": "string",
                    "enum": ["train_test_split", "k_fold_cross_validation", "stratified_k_fold", "repeated_cv"],
                },
                "n_splits": {"type": "integer", "minimum": 2, "maximum": 10},
            },
        },
        "adjustment_reasons": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Reasons why the original strategy should be adjusted.",
        },
        "risk_notes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Risks or concerns about the current strategy.",
        },
        "confidence_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    },
}

SYSTEM_PROMPT = """You are an expert AutoML strategy advisor for materials science. Your task is to analyze the model-ready dataset and suggest updates to the model search strategy.

**YOUR ROLE:** You analyze and advise — you do NOT execute. The system will validate and merge your advice.

**CRITICAL BOUNDARY RULES — You MUST follow these:**

1. You MUST NOT generate Python code, pseudocode, or any executable code.
2. You MUST NOT generate Shell commands, SQL statements, or system configuration.
3. You MUST NOT generate training scripts, pipeline scripts, or HPO execution code.
4. You MUST NOT fabricate or predict model performance metrics.
5. You MUST NOT claim that models have been trained or evaluated.
6. You MUST select model families ONLY from the allowed_model_families list.
7. You MUST select HPO methods ONLY from the allowed_hpo_methods list.
8. You MUST NOT invent model families or HPO methods not in the allowed lists.
9. You MUST output ONLY valid JSON matching the exact schema provided. No other text.
10. If the original strategy is still reasonable, set adjustment_reasons to explain why it remains valid.

**Your analysis should consider:**

- **Feature count**: If final features are very few, prefer simpler models, lower HPO budget, and fewer CV folds.
- **Feature reduction**: If many feature groups were dropped, reassess whether the original model choices still make sense.
- **Sample size**: Small samples need simpler models and fewer HPO trials. Large samples can support more complex models.
- **Preprocessing execution**: If scaling was already applied, tree-based models that don't require scaling may be less critical. If the original plan assumed scaling and scaling was executed, models that need scaling are fine.
- **Task type**: Regression vs classification affects model family selection.

**Strategy guidance:**

- Low feature count (< 20): prefer linear models, ridge/lasso, random_forest. Avoid xgboost with shallow trees.
- High feature reduction (> 80%): be conservative — fewer model families, more baselines.
- Small samples (< 200): prefer ridge, lasso over gradient_boosting. Use k-fold CV with fewer splits.
- Large samples (>= 1000): allow full candidate list and moderate HPO.

You MUST output ONLY the JSON object."""


def build_llm_context(
    task_type: str,
    target_column: str,
    primary_metric: str,
    dataset_profile_result: dict,
    feature_group_result: dict,
    preprocessing_result: dict,
    original_model_strategy: dict,
    original_hpo_strategy: dict,
    original_validation_strategy: dict,
) -> Tuple[str, str]:
    allowed_model_families = get_model_families_for_task_type(task_type)
    if not allowed_model_families:
        allowed_model_families = get_all_model_families()

    allowed_hpo_methods = get_all_hpo_methods()

    user_context = {
        "task_type": task_type,
        "target_column": target_column,
        "primary_metric": primary_metric,
        "dataset_effective_profile": {
            "n_samples": dataset_profile_result.get("n_samples", 0),
            "n_final_features": dataset_profile_result.get("n_final_features", 0),
            "feature_reduction_ratio": dataset_profile_result.get("feature_reduction_ratio", 0.0),
            "is_low_feature": dataset_profile_result.get("is_low_feature", False),
            "is_high_reduction": dataset_profile_result.get("is_high_reduction", False),
            "is_small_sample": dataset_profile_result.get("is_small_sample", False),
        },
        "feature_group_summary": {
            "retained_groups": feature_group_result["summary"].retained_groups,
            "dropped_groups": feature_group_result["summary"].dropped_groups,
            "has_dropped_groups": feature_group_result.get("has_dropped_groups", False),
        },
        "preprocessing_summary": {
            "imputation_executed": preprocessing_result["summary"].imputation_executed,
            "scaling_executed": preprocessing_result["summary"].scaling_executed,
            "feature_selection_executed": preprocessing_result["summary"].feature_selection_executed,
        },
        "original_model_strategy": original_model_strategy,
        "original_hpo_strategy": original_hpo_strategy,
        "original_validation_strategy": original_validation_strategy,
        "allowed_model_families": allowed_model_families,
        "allowed_hpo_methods": allowed_hpo_methods,
        "baseline_model_suggestions": get_baseline_models(task_type),
    }

    user_message_parts = [
        "## Model-Ready Dataset & Strategy Context",
        json.dumps(user_context, indent=2, ensure_ascii=False),
        "",
        "## Output JSON Schema",
        "You MUST output a single JSON object that strictly follows this schema:",
        json.dumps(OUTPUT_JSON_SCHEMA, indent=2),
        "",
        "Remember: output ONLY the JSON object. No markdown, no code blocks, no explanatory text.",
    ]

    user_message = "\n".join(user_message_parts)
    return SYSTEM_PROMPT, user_message
