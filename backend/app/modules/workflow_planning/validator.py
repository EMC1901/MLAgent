from typing import Dict, Any, List


REQUIRED_TOP_LEVEL_FIELDS = [
    "task_summary", "data_strategy", "feature_strategy", "model_strategy",
    "validation_strategy", "evaluation_strategy", "hpo_strategy",
    "interpretability_strategy", "pipeline_generation_input",
    "planning_warnings", "planning_assumptions",
    "llm_reasoning_summary", "confidence_score",
]

TASK_SUMMARY_FIELDS = ["task_type", "input_modality", "prediction_target", "material_domain", "primary_goal"]
DATA_STRATEGY_FIELDS = ["input_columns", "target_column", "required_cleaning_steps", "target_handling", "duplicate_handling", "missing_value_strategy"]
FEATURE_STRATEGY_FIELDS = ["feature_type", "recommended_featurizers", "requires_structure_features", "feature_selection_required", "feature_scaling_required"]
MODEL_STRATEGY_FIELDS = ["candidate_model_families", "baseline_models", "preferred_model_bias", "excluded_model_families"]
VALIDATION_STRATEGY_FIELDS = ["split_strategy", "n_splits", "random_state", "stratification_required"]
EVALUATION_STRATEGY_FIELDS = ["primary_metric", "secondary_metrics", "metric_direction"]
HPO_STRATEGY_FIELDS = ["enabled", "search_method", "budget_level", "max_trials"]
INTERPRETABILITY_STRATEGY_FIELDS = ["enabled", "methods", "priority"]
PIPELINE_INPUT_FIELDS = ["pipeline_steps", "required_components"]

VALID_TASK_TYPES = {"regression", "classification", "ranking"}
VALID_INPUT_MODALITIES = {"composition", "structure", "descriptor", "text", "mixed"}
VALID_SPLIT_STRATEGIES = {"train_test_split", "k_fold_cross_validation", "stratified_k_fold", "repeated_cv"}
VALID_SEARCH_METHODS = {"grid_search", "random_search", "bayesian_optimization"}
VALID_BUDGET_LEVELS = {"low", "medium", "high"}
VALID_METRIC_DIRECTIONS = {"minimize", "maximize"}

FORBIDDEN_CONTENT = [
    "import pandas",
    "import numpy",
    "import sklearn",
    "from sklearn",
    "def train",
    "def predict",
    "def fit",
    "class Model",
    "exec(",
    "MAE of",
    "RMSE of",
    "R² of",
    "R2 of",
    "accuracy of",
    "F1 score of",
    "training loss",
    "validation loss",
    "test loss",
    "model.fit",
    "model.predict",
]


def validate_workflow_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in plan:
            errors.append(f"Missing required top-level field: '{field}'")

    if errors:
        return {"is_valid": False, "errors": errors}

    _check_sub_object("task_summary", plan.get("task_summary", {}), TASK_SUMMARY_FIELDS, errors)
    _check_sub_object("data_strategy", plan.get("data_strategy", {}), DATA_STRATEGY_FIELDS, errors)
    _check_sub_object("feature_strategy", plan.get("feature_strategy", {}), FEATURE_STRATEGY_FIELDS, errors)
    _check_sub_object("model_strategy", plan.get("model_strategy", {}), MODEL_STRATEGY_FIELDS, errors)
    _check_sub_object("validation_strategy", plan.get("validation_strategy", {}), VALIDATION_STRATEGY_FIELDS, errors)
    _check_sub_object("evaluation_strategy", plan.get("evaluation_strategy", {}), EVALUATION_STRATEGY_FIELDS, errors)
    _check_sub_object("hpo_strategy", plan.get("hpo_strategy", {}), HPO_STRATEGY_FIELDS, errors)
    _check_sub_object("interpretability_strategy", plan.get("interpretability_strategy", {}), INTERPRETABILITY_STRATEGY_FIELDS, errors)
    _check_sub_object("pipeline_generation_input", plan.get("pipeline_generation_input", {}), PIPELINE_INPUT_FIELDS, errors)

    _check_enum_values(plan, errors)
    _check_confidence_score(plan, errors)
    _check_arrays(plan, errors)
    _check_forbidden_content(plan, errors)

    return {"is_valid": len(errors) == 0, "errors": errors}


def _check_sub_object(name: str, obj: Dict[str, Any], required_fields: List[str], errors: List[str]):
    for field in required_fields:
        if field not in obj:
            errors.append(f"Missing required field in {name}: '{field}'")


def _check_enum_values(plan: Dict[str, Any], errors: List[str]):
    task_summary = plan.get("task_summary", {})
    task_type = task_summary.get("task_type")
    if task_type and task_type not in VALID_TASK_TYPES:
        errors.append(f"Invalid task_type '{task_type}'. Must be one of: {VALID_TASK_TYPES}")

    input_modality = task_summary.get("input_modality")
    if input_modality and input_modality not in VALID_INPUT_MODALITIES:
        errors.append(f"Invalid input_modality '{input_modality}'. Must be one of: {VALID_INPUT_MODALITIES}")

    validation_strategy = plan.get("validation_strategy", {})
    split_strategy = validation_strategy.get("split_strategy")
    if split_strategy and split_strategy not in VALID_SPLIT_STRATEGIES:
        errors.append(f"Invalid split_strategy '{split_strategy}'. Must be one of: {VALID_SPLIT_STRATEGIES}")

    hpo_strategy = plan.get("hpo_strategy", {})
    search_method = hpo_strategy.get("search_method")
    if search_method and search_method not in VALID_SEARCH_METHODS:
        errors.append(f"Invalid search_method '{search_method}'. Must be one of: {VALID_SEARCH_METHODS}")

    budget_level = hpo_strategy.get("budget_level")
    if budget_level and budget_level not in VALID_BUDGET_LEVELS:
        errors.append(f"Invalid budget_level '{budget_level}'. Must be one of: {VALID_BUDGET_LEVELS}")

    evaluation_strategy = plan.get("evaluation_strategy", {})
    metric_direction = evaluation_strategy.get("metric_direction")
    if metric_direction and metric_direction not in VALID_METRIC_DIRECTIONS:
        errors.append(f"Invalid metric_direction '{metric_direction}'. Must be one of: {VALID_METRIC_DIRECTIONS}")

    n_splits = validation_strategy.get("n_splits")
    if n_splits is not None and (not isinstance(n_splits, int) or n_splits < 2 or n_splits > 10):
        errors.append(f"Invalid n_splits {n_splits}. Must be an integer between 2 and 10.")


def _check_confidence_score(plan: Dict[str, Any], errors: List[str]):
    score = plan.get("confidence_score")
    if score is not None:
        if not isinstance(score, (int, float)) or score < 0.0 or score > 1.0:
            errors.append(f"Invalid confidence_score {score}. Must be between 0.0 and 1.0.")


def _check_arrays(plan: Dict[str, Any], errors: List[str]):
    if not isinstance(plan.get("planning_warnings"), list):
        errors.append("'planning_warnings' must be an array.")
    if not isinstance(plan.get("planning_assumptions"), list):
        errors.append("'planning_assumptions' must be an array.")
    if not isinstance(plan.get("pipeline_generation_input", {}).get("pipeline_steps"), list):
        errors.append("'pipeline_generation_input.pipeline_steps' must be an array.")
    if not isinstance(plan.get("model_strategy", {}).get("candidate_model_families"), list):
        errors.append("'model_strategy.candidate_model_families' must be an array.")
    if not isinstance(plan.get("model_strategy", {}).get("baseline_models"), list):
        errors.append("'model_strategy.baseline_models' must be an array.")


def _check_forbidden_content(plan: Dict[str, Any], errors: List[str]):
    plan_str = str(plan).lower()
    for forbidden in FORBIDDEN_CONTENT:
        if forbidden.lower() in plan_str:
            errors.append(
                f"Forbidden content detected: '{forbidden}'. "
                "Workflow Plan must not contain executable code, training results, or fabricated metrics."
            )
