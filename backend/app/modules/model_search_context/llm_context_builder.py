import json
from typing import Tuple, Dict, Any
from app.shared.registry.model_registry import get_model_families_for_task_type, get_baseline_models, get_all_model_families, MODEL_FAMILIES
from app.shared.registry.hpo_registry import get_all_hpo_methods


OUTPUT_JSON_SCHEMA = {
    "type": "object",
    "required": [
        "strategy_changes",
        "strategy_change_summary",
        "risk_notes",
        "confidence_score",
    ],
    "properties": {
        "strategy_changes": {
            "type": "array",
            "description": "Every field-level change you recommend, plus fields you examined but kept.",
            "items": {
                "type": "object",
                "required": [
                    "strategy_area", "field_path", "original_value",
                    "updated_value", "change_type", "decision_rationale",
                ],
                "properties": {
                    "strategy_area": {
                        "type": "string",
                        "enum": ["model", "hpo", "validation", "evaluation"],
                        "description": "Which strategy area this change belongs to.",
                    },
                    "field_path": {
                        "type": "string",
                        "description": "The specific field being changed, e.g. 'candidate_model_families', 'search_method', 'split_strategy'.",
                    },
                    "original_value": {
                        "description": "The original value from the workflow plan. Use null if the field was empty/absent.",
                    },
                    "updated_value": {
                        "description": "Your recommended value. Use null if recommending removal.",
                    },
                    "change_type": {
                        "type": "string",
                        "enum": ["modified", "added", "removed", "confirmed"],
                        "description": "modified=value changed, added=new field, removed=field removed, confirmed=examined but kept unchanged.",
                    },
                    "decision_rationale": {
                        "type": "object",
                        "required": ["reason", "evidence", "expected_benefit", "risk", "fallback"],
                        "properties": {
                            "reason": {
                                "type": "string",
                                "description": "WHY this specific change is recommended. Reference concrete data (feature count, sample size, preprocessing results). Must be 1-3 sentences.",
                            },
                            "evidence": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific facts from the dataset profile, feature groups, or preprocessing summary that support this change.",
                            },
                            "expected_benefit": {
                                "type": "string",
                                "description": "What improvement this change should produce (e.g. better generalization, reduced overfitting, faster search).",
                            },
                            "risk": {
                                "type": "string",
                                "description": "What could go wrong if this change is applied (e.g. underfitting, missing non-linear patterns).",
                            },
                            "fallback": {
                                "type": "string",
                                "description": "What to do if this change causes problems (e.g. revert to original, try a different model family).",
                            },
                        },
                    },
                },
            },
        },
        "trial_allocation": {
            "type": "array",
            "description": "Per-model-family trial budget allocation with detailed rationale. Allocate the total max_trials across the candidate and baseline model families you recommended. Each entry explains WHY that specific model family deserves its allocated trial count.",
            "items": {
                "type": "object",
                "required": ["model_family", "max_trials", "allocation_rationale"],
                "properties": {
                    "model_family": {
                        "type": "string",
                        "description": "The exact model family name (snake_case, e.g. 'random_forest', 'xgboost'). Must match a family from allowed_model_families.",
                    },
                    "max_trials": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Number of HPO trials to allocate to this model family. 0 means no HPO for this model.",
                    },
                    "allocation_rationale": {
                        "type": "string",
                        "description": "WHY this specific number of trials for this model family. Reference: model complexity, expected sensitivity to hyperparameters, risk of overfitting given dataset size, and how critical this model is to the search strategy.",
                    },
                },
            },
        },
        "search_space_overrides": {
            "type": "array",
            "description": "Optional per-parameter search space overrides. Use this to adjust specific parameter ranges based on dataset characteristics (n_samples, n_features). Only include overrides where the template defaults are clearly wrong for this dataset.",
            "items": {
                "type": "object",
                "required": ["model_family", "parameter_name", "override_rationale"],
                "properties": {
                    "model_family": {
                        "type": "string",
                        "description": "The exact model family name (snake_case, e.g. 'random_forest', 'xgboost').",
                    },
                    "parameter_name": {
                        "type": "string",
                        "description": "The exact parameter name to override, e.g. 'n_estimators', 'learning_rate', 'max_depth'.",
                    },
                    "low": {
                        "type": "number",
                        "description": "Override the lower bound. Only include if you want to change it.",
                    },
                    "high": {
                        "type": "number",
                        "description": "Override the upper bound. Only include if you want to change it.",
                    },
                    "choices": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Override the categorical choices. Only include if you want to change them.",
                    },
                    "override_rationale": {
                        "type": "string",
                        "description": "WHY this parameter range should be different from the default. Reference: dataset size, feature count, expected model sensitivity, and risk of overfitting/underfitting.",
                    },
                },
            },
        },
        "strategy_change_summary": {
            "type": "string",
            "description": "A 2-4 sentence narrative summary of the overall strategy changes and their rationale. Written for a materials scientist to understand the big picture.",
        },
        "risk_notes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Risks or concerns about the overall updated strategy.",
        },
        "confidence_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    },
}

SYSTEM_PROMPT = """You are an expert AutoML strategy advisor for materials science. Your task is to analyze the model-ready dataset and produce a detailed, field-by-field strategy update with complete rationale for every change.

**YOUR ROLE:** You analyze and advise — you do NOT execute. The system will validate and merge your advice.

**CRITICAL BOUNDARY RULES — You MUST follow these:**

1. You MUST NOT generate Python code, pseudocode, or any executable code.
2. You MUST NOT generate Shell commands, SQL statements, or system configuration.
3. You MUST NOT generate training scripts, pipeline scripts, or HPO execution code.
4. You MUST NOT fabricate or predict model performance metrics.
5. You MUST NOT claim that models have been trained or evaluated.
6. You MUST select model families ONLY from the allowed_model_families list.
7. You MUST use the EXACT "family" field value (e.g., "random_forest", "ridge") — do NOT use the "display_name" (e.g., "Random Forest", "Ridge Regression"). Copy the family strings verbatim.
8. You MUST select HPO methods ONLY from the allowed_hpo_methods list.
9. You MUST NOT invent model families or HPO methods not in the allowed lists.
10. You MUST output ONLY valid JSON matching the exact schema provided. No other text.

**YOUR OUTPUT — strategy_changes array:**

For EVERY field in the original strategies, you MUST include an entry in `strategy_changes`:
- If you recommend changing it: change_type = "modified" (or "added"/"removed")
- If you examined it and decided NOT to change it: change_type = "confirmed" with a rationale explaining WHY it's still correct

**DECISION_RATIONALE REQUIREMENTS:**

Each change MUST have a complete decision_rationale with:
- **reason**: WHY this specific change. Must reference concrete numbers (n_samples, n_final_features, feature_reduction_ratio, dropped groups, preprocessing results).
- **evidence**: Specific facts from the provided context that support your decision.
- **expected_benefit**: What improvement this produces.
- **risk**: What could go wrong.
- **fallback**: What to revert to if this fails.

**TRIAL ALLOCATION REQUIREMENTS:**

You MUST also output a `trial_allocation` array that allocates the HPO trial budget across ALL model families you recommended (candidate + baseline). This is a critical decision because it determines how much computational resource each model receives.

Guidelines for trial allocation:
- Complex models (xgboost, lightgbm, mlp, gradient_boosting): allocate MORE trials — they have larger search spaces and are more sensitive to hyperparameters.
- Simpler models (ridge, lasso, linear_regression): allocate FEWER trials — they have small or no search spaces.
- Tree-based ensemble models (random_forest, extra_trees): allocate MODERATE trials.
- Baseline models: allocate 0 trials (they use default parameters, no HPO).
- The sum of all max_trials in the allocation should approximately match your recommended max_trials.
- Moderate HPO should usually stay near 50 total trials; high-budget or wide-search cases with enough samples/features may recommend up to 100 total trials. The system enforces a hard safety cap.
- If xgboost or lightgbm is selected outside small-sample/low-feature settings, avoid allocations below 20 trials per model unless the total HPO budget is intentionally low.
- Each allocation_rationale MUST explain WHY that specific model gets that specific number of trials — reference the model's complexity, search space size, expected sensitivity to HPO, and the dataset characteristics (n_samples, n_final_features).

**Strategy guidance:**

- Low feature count (< 20): prefer linear models, ridge/lasso, random_forest. Avoid xgboost with shallow trees.
- High feature reduction (> 80%): be conservative — fewer model families.
- Small samples (< 200): prefer ridge, lasso over gradient_boosting. Use k-fold CV with fewer splits.
- **Baseline model rule:** You MUST keep exactly ONE baseline model. The baseline is the minimum-performance reference (e.g. dummy_mean, linear_regression, ridge). If you change the baseline, replace the old one — never have more than one.
- Large samples (>= 1000): allow full candidate list and moderate HPO.
- If scaling was executed: tree-based models that don't need scaling are less critical; models that benefit from scaling are well-prepared.
- If feature selection removed many features: reassess whether the original model families still make sense.

**SEARCH SPACE WIDTH GUIDANCE:**

You should set `search_space_width` based on dataset characteristics:
- **narrow**: Small samples (< 200) OR low features (< 10) — tighter parameter ranges to prevent overfitting from excessive search.
- **moderate**: Medium samples (200–1000) with moderate features (10–50) — standard ranges, good default.
- **wide**: Large samples (>= 1000) with many features (>= 50) — expanded ranges to explore more possibilities with sufficient data.
- Also consider: if the dataset has high feature reduction (> 80%), prefer narrow to avoid overfitting on the reduced feature set.

**SEARCH SPACE OVERRIDES GUIDANCE:**

You may optionally provide `search_space_overrides` to fine-tune specific parameter ranges for individual model families. This is for cases where the default ranges are clearly wrong for this dataset.

When to provide overrides:
- Small samples (< 200): reduce n_estimators high bound (e.g., 500 → 200) for tree models to avoid overfitting.
- Many features (>= 50): increase max_depth high bound for tree models to allow deeper splits.
- Low features (< 10): reduce max_depth high bound (shallow trees are sufficient).
- High feature reduction (> 80%): tighten learning_rate range for gradient-based models (less exploration needed).

Each override MUST have an `override_rationale` explaining WHY with concrete numbers. Only include overrides you are confident about — the system will ignore invalid ones.

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
    iteration_guidance: Dict[str, Any] = None,
) -> Tuple[str, str]:
    allowed_model_families = get_model_families_for_task_type(task_type)
    if not allowed_model_families:
        allowed_model_families = get_all_model_families()

    allowed_hpo_methods = get_all_hpo_methods()

    # Build model family info with both family keys and display names for the LLM
    allowed_model_families_info = []
    for mf in MODEL_FAMILIES:
        if mf["family"] in allowed_model_families:
            allowed_model_families_info.append({
                "family": mf["family"],
                "display_name": mf["display_name"],
            })

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
        "original_strategies": {
            "model_strategy": original_model_strategy,
            "hpo_strategy": original_hpo_strategy,
            "validation_strategy": original_validation_strategy,
        },
        "allowed_model_families": allowed_model_families_info,
        "allowed_hpo_methods": allowed_hpo_methods,
        "baseline_model_suggestions": get_baseline_models(task_type),
        "iteration_guidance": iteration_guidance,
    }

    user_message_parts = [
        "## Model-Ready Dataset & Strategy Context",
        json.dumps(user_context, indent=2, ensure_ascii=False),
        "",
        "## Output JSON Schema",
        "You MUST output a single JSON object that strictly follows this schema:",
        json.dumps(OUTPUT_JSON_SCHEMA, indent=2),
        "",
        "## IMPORTANT REMINDER",
        "1. Include a strategy_changes entry for EVERY field you examine — use 'confirmed' for fields you keep.",
        "2. Every entry MUST have a complete decision_rationale with all 5 required fields filled.",
        "3. Reference concrete numbers from the dataset profile in your reasons.",
        "4. For model family names, use the EXACT 'family' value (snake_case like 'random_forest') — NEVER use display_name (like 'Random Forest').",
        "5. For HPO method names, copy the allowed_hpo_methods strings verbatim.",
        "6. Output ONLY the JSON object. No markdown, no code blocks, no explanatory text.",
    ]

    user_message = "\n".join(user_message_parts)
    return SYSTEM_PROMPT, user_message
