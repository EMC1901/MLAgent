import json
from typing import Tuple

OUTPUT_JSON_SCHEMA = {
    "type": "object",
    "required": [
        "recommended_model_ids",
        "baseline_model_ids",
        "excluded_model_ids",
        "hpo_recommendation",
        "search_space_profile",
        "model_priority_notes",
        "risk_notes",
        "confidence_score",
    ],
    "properties": {
        "recommended_model_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Model IDs selected ONLY from allowed_model_families to be searched.",
        },
        "baseline_model_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Simple baseline models (e.g., dummy_mean, ridge) to benchmark against.",
        },
        "excluded_model_ids": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "model_id": {"type": "string"},
                    "reason": {"type": "string"},
                },
            },
            "description": "Models to exclude and why.",
        },
        "hpo_recommendation": {
            "type": "object",
            "required": ["enabled", "search_method", "budget_level", "max_total_trials"],
            "properties": {
                "enabled": {"type": "boolean"},
                "search_method": {
                    "type": "string",
                    "description": "HPO method selected ONLY from allowed_hpo_methods.",
                },
                "budget_level": {
                    "type": "string",
                    "enum": ["low", "moderate", "high"],
                },
                "max_total_trials": {"type": "integer", "minimum": 1, "maximum": 50},
            },
        },
        "search_space_profile": {
            "type": "object",
            "properties": {
                "space_width": {"type": "string", "enum": ["narrow", "moderate", "wide"]},
                "prefer_conservative_ranges": {"type": "boolean"},
            },
        },
        "model_priority_notes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "model_id": {"type": "string"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                    "reason": {"type": "string"},
                },
            },
        },
        "risk_notes": {
            "type": "array",
            "items": {"type": "string"},
        },
        "confidence_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    },
}

SYSTEM_PROMPT = """You are an expert AutoML model search planner. Your role is to recommend which models and HPO methods to use for a given task.

**CRITICAL BOUNDARY RULES — You MUST follow these:**

1. You MUST NOT generate Python code, pseudocode, or any executable code.
2. You MUST NOT generate Shell commands, SQL statements, or system configuration.
3. You MUST NOT generate training scripts, HPO execution code, or pipeline code.
4. You MUST NOT claim that models have been trained or report predicted metrics.
5. You MUST select model IDs ONLY from the allowed_model_families list.
6. You MUST select HPO methods ONLY from the allowed_hpo_methods list.
7. You MUST NOT invent model IDs or HPO methods not in the allowed lists.
8. You MUST output ONLY valid JSON matching the exact schema provided. No other text.
9. Do NOT include markdown code blocks, explanations, or any text outside the JSON object.

**Your analysis should consider:**

- **Task type**: Regression vs classification determines which model families are valid.
- **Sample count**: Small datasets (< 200) need simpler models and fewer HPO trials. Large datasets (>= 1000) can support more models and moderate HPO.
- **Feature count**: Few features (< 20) suggest simpler models; many features can support complex models.
- **Preprocessing state**: If scaling was applied, models requiring scaling are fine. If not, tree-based models may be preferred.
- **Updated strategies**: Respect the updated_model_strategy and updated_hpo_strategy from upstream context.

**Recommendation guidance:**

- Always include at least one baseline model (e.g., dummy_mean, ridge).
- For regression with < 200 samples: prefer ridge, lasso, random_forest. Avoid xgboost.
- For regression with >= 1000 samples: include gradient_boosting, xgboost if available.
- Budget level: low for small samples/complex models, moderate for medium, high for large/exploratory.
- Search space: narrow when features are few and samples are small; wide for large exploratory studies.

You MUST output ONLY the JSON object."""


def build_llm_model_search_prompt(context: dict) -> Tuple[str, str]:
    user_context = {
        "task_type": context.get("task_type"),
        "primary_metric": context.get("primary_metric"),
        "n_samples": context.get("n_samples"),
        "n_features": context.get("n_features"),
        "feature_group_summary": context.get("feature_group_summary", {}),
        "preprocessing_summary": context.get("preprocessing_summary", {}),
        "updated_model_strategy": context.get("updated_model_strategy", {}),
        "updated_hpo_strategy": context.get("updated_hpo_strategy", {}),
        "allowed_model_families": context.get("allowed_model_families", []),
        "allowed_hpo_methods": context.get("allowed_hpo_methods", []),
    }

    user_message_parts = [
        "## Task & Dataset Context for Model Search Planning",
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
