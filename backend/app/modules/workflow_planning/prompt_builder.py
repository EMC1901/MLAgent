import json
from typing import Tuple


OUTPUT_JSON_SCHEMA = {
    "type": "object",
    "required": [
        "task_summary",
        "data_strategy",
        "feature_strategy",
        "model_strategy",
        "validation_strategy",
        "evaluation_strategy",
        "hpo_strategy",
        "interpretability_strategy",
        "pipeline_generation_input",
        "planning_warnings",
        "planning_assumptions",
        "llm_reasoning_summary",
        "confidence_score",
    ],
    "properties": {
        "task_summary": {
            "type": "object",
            "required": ["task_type", "input_modality", "prediction_target", "material_domain", "primary_goal"],
            "properties": {
                "task_type": {"type": "string", "enum": ["regression", "classification", "ranking"]},
                "input_modality": {"type": "string", "enum": ["composition", "structure", "descriptor", "text", "mixed"]},
                "prediction_target": {"type": "string"},
                "material_domain": {"type": "string"},
                "primary_goal": {"type": "string"},
            },
        },
        "data_strategy": {
            "type": "object",
            "required": ["input_columns", "target_column", "required_cleaning_steps", "target_handling", "duplicate_handling", "missing_value_strategy"],
            "properties": {
                "input_columns": {"type": "array", "items": {"type": "string"}},
                "target_column": {"type": "string"},
                "required_cleaning_steps": {"type": "array", "items": {"type": "string"}},
                "target_handling": {
                    "type": "object",
                    "properties": {
                        "requires_transformation_check": {"type": "boolean"},
                        "recommended_transformation": {"type": "string"},
                    },
                },
                "duplicate_handling": {"type": "string"},
                "missing_value_strategy": {"type": "string"},
            },
        },
        "feature_strategy": {
            "type": "object",
            "required": ["feature_type", "recommended_featurizers", "requires_structure_features", "feature_selection_required", "feature_scaling_required"],
            "properties": {
                "feature_type": {"type": "string"},
                "recommended_featurizers": {"type": "array", "items": {"type": "string"}},
                "requires_structure_features": {"type": "boolean"},
                "feature_selection_required": {"type": "boolean"},
                "feature_scaling_required": {"type": "boolean"},
            },
        },
        "model_strategy": {
            "type": "object",
            "required": ["candidate_model_families", "baseline_models", "preferred_model_bias", "excluded_model_families"],
            "properties": {
                "candidate_model_families": {"type": "array", "items": {"type": "string"}},
                "baseline_models": {"type": "array", "items": {"type": "string"}},
                "preferred_model_bias": {"type": "string"},
                "excluded_model_families": {"type": "array", "items": {"type": "string"}},
            },
        },
        "validation_strategy": {
            "type": "object",
            "required": ["split_strategy", "n_splits", "random_state", "stratification_required"],
            "properties": {
                "split_strategy": {"type": "string", "enum": ["train_test_split", "k_fold_cross_validation", "stratified_k_fold", "repeated_cv"]},
                "n_splits": {"type": "integer", "minimum": 2, "maximum": 10},
                "test_size": {"type": ["number", "null"]},
                "random_state": {"type": "integer"},
                "stratification_required": {"type": "boolean"},
            },
        },
        "evaluation_strategy": {
            "type": "object",
            "required": ["primary_metric", "secondary_metrics", "metric_direction"],
            "properties": {
                "primary_metric": {"type": "string"},
                "secondary_metrics": {"type": "array", "items": {"type": "string"}},
                "metric_direction": {"type": "string", "enum": ["minimize", "maximize"]},
            },
        },
        "hpo_strategy": {
            "type": "object",
            "required": ["enabled", "search_method", "budget_level", "max_trials"],
            "properties": {
                "enabled": {"type": "boolean"},
                "search_method": {"type": "string", "enum": ["grid_search", "random_search", "bayesian_optimization"]},
                "budget_level": {"type": "string", "enum": ["low", "medium", "high"]},
                "max_trials": {"type": "integer", "minimum": 1},
            },
        },
        "interpretability_strategy": {
            "type": "object",
            "required": ["enabled", "methods", "priority"],
            "properties": {
                "enabled": {"type": "boolean"},
                "methods": {"type": "array", "items": {"type": "string"}},
                "priority": {"type": "string"},
            },
        },
        "pipeline_generation_input": {
            "type": "object",
            "required": ["pipeline_steps", "required_components"],
            "properties": {
                "pipeline_steps": {"type": "array", "items": {"type": "string"}},
                "required_components": {
                    "type": "object",
                    "properties": {
                        "data_cleaner": {"type": "boolean"},
                        "featurizer": {"type": "boolean"},
                        "model_trainer": {"type": "boolean"},
                        "evaluator": {"type": "boolean"},
                    },
                },
            },
        },
        "planning_warnings": {"type": "array", "items": {"type": "string"}},
        "planning_assumptions": {"type": "array", "items": {"type": "string"}},
        "llm_reasoning_summary": {"type": "string"},
        "confidence_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    },
}


SYSTEM_PROMPT = """You are an expert AutoML workflow planner for materials science. Your task is to generate a structured machine learning workflow plan based on task specifications, task interpretation, and dataset profiling results.

**CRITICAL BOUNDARY RULES — You MUST follow these:**

1. You ONLY plan the machine learning workflow. You do NOT execute anything.
2. You MUST NOT generate Python code, pseudocode, or any executable code.
3. You MUST NOT fabricate or predict model training results, metrics values, or evaluation scores.
4. You MUST NOT claim that models have been trained.
5. You MUST NOT load, clean, or transform any actual data.
6. You MUST NOT modify upstream task specification, interpretation, or dataset profile.
7. You MUST base all decisions on the data facts provided in the dataset profile.
8. If something is uncertain, put it in "planning_assumptions", not in the main plan.
9. If there are risks or limitations, put them in "planning_warnings".
10. You MUST output ONLY valid JSON matching the exact schema provided. No other text.

Your planning should cover:

- **Task Summary**: Summarize what this ML task is about.
- **Data Strategy**: Plan data cleaning, missing value handling, duplicate handling, target transformation checks.
- **Feature Strategy**: Based on input modality, recommend featurizers and whether scaling/selection is needed.
- **Model Strategy**: Recommend candidate model families, baseline models, and any excluded models.
- **Validation Strategy**: Recommend split strategy, number of folds, random state.
- **Evaluation Strategy**: Define primary and secondary metrics, and metric direction (minimize or maximize).
- **HPO Strategy**: Decide whether hyperparameter optimization is needed, and if so which method and budget.
- **Interpretability Strategy**: Decide which interpretability methods to use (feature importance, SHAP, etc.).
- **Pipeline Generation Input**: List the pipeline steps in order and which components are required.
- **Planning Warnings**: List any concerns based on data quality, sample size, task complexity, etc.
- **Planning Assumptions**: List any assumptions made during planning.
- **LLM Reasoning Summary**: A brief paragraph explaining the key planning decisions.
- **Confidence Score**: A number between 0 and 1 indicating your confidence in this plan.

For materials science tasks:

- **composition** input modality -> recommend composition-based featurizers (elemental property statistics, stoichiometric features, Magpie descriptors)
- **structure** input modality -> recommend structure-based featurizers (density, symmetry, local environment, graph-based)
- **descriptor** input modality -> use existing numeric descriptors with scaling and feature selection
- **regression** tasks -> recommend MAE/RMSE/R2 metrics, tree-based + linear models
- **classification** tasks -> recommend Accuracy/F1/ROC-AUC metrics, tree-based + linear models
- Small samples (n < 100) -> prefer simple models, fewer CV folds, limited HPO
- Medium samples (100 <= n < 1000) -> allow moderate complexity
- Large samples (n >= 1000) -> allow complex models, more HPO budget"""


def build_prompt(context: dict) -> Tuple[str, str]:
    user_message_parts = [
        "## Task Context",
        json.dumps(context.get("task_context", {}), indent=2, ensure_ascii=False),
        "",
        "## Interpretation Context",
        json.dumps(context.get("interpretation_context", {}), indent=2, ensure_ascii=False),
        "",
        "## Data Context",
        json.dumps(context.get("data_context", {}), indent=2, ensure_ascii=False),
        "",
        "## Output JSON Schema",
        "You MUST output a single JSON object that strictly follows this schema:",
        json.dumps(OUTPUT_JSON_SCHEMA, indent=2),
        "",
        "Remember: output ONLY the JSON object. No markdown, no code blocks, no explanatory text.",
    ]

    user_message = "\n".join(user_message_parts)
    return SYSTEM_PROMPT, user_message
