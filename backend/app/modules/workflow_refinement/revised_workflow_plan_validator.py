import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

REQUIRED_TOP_LEVEL_FIELDS = [
    "task_summary",
    "data_strategy",
    "feature_strategy",
    "model_strategy",
    "validation_strategy",
    "evaluation_strategy",
    "hpo_strategy",
    "interpretability_strategy",
    "pipeline_generation_input",
]

TASK_SUMMARY_REQUIRED = [
    "task_type", "input_modality", "prediction_target",
    "material_domain", "primary_goal",
]

DATA_STRATEGY_REQUIRED = [
    "input_columns", "target_column", "required_cleaning_steps",
]

FEATURE_STRATEGY_REQUIRED = [
    "feature_type", "executable_featurizers", "semantic_featurizers",
]

MODEL_STRATEGY_REQUIRED = [
    "candidate_model_families", "baseline_models",
]

VALIDATION_STRATEGY_REQUIRED = [
    "split_strategy", "n_splits",
]

EVALUATION_STRATEGY_REQUIRED = [
    "primary_metric",
]

HPO_STRATEGY_REQUIRED = [
    "enabled", "search_method", "budget_level", "max_trials",
]

VALID_TASK_TYPES = {"regression", "classification", "ranking"}
VALID_INPUT_MODALITIES = {"composition", "structure", "descriptor", "text", "mixed"}
VALID_SPLIT_STRATEGIES = {
    "train_test_split", "k_fold_cross_validation",
    "stratified_k_fold", "repeated_cv",
}
VALID_SEARCH_METHODS = {"grid_search", "random_search", "bayesian_optimization"}
VALID_BUDGET_LEVELS = {"low", "medium", "high"}
VALID_METRIC_DIRECTIONS = {"minimize", "maximize"}


def validate_revised_workflow_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that a revised workflow plan is compatible with WorkflowPlanResponse schema."""
    errors: List[str] = []

    if not isinstance(plan, dict):
        return {"is_valid": False, "errors": ["Revised workflow plan must be a dict"]}

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in plan or plan[field] is None:
            errors.append(f"Missing required field: {field}")

    ts = plan.get("task_summary") or {}
    if isinstance(ts, dict):
        for field in TASK_SUMMARY_REQUIRED:
            if field not in ts:
                errors.append(f"task_summary missing field: {field}")
        if ts.get("task_type") not in VALID_TASK_TYPES:
            errors.append(f"Invalid task_type: {ts.get('task_type')}")
        if ts.get("input_modality") not in VALID_INPUT_MODALITIES:
            errors.append(f"Invalid input_modality: {ts.get('input_modality')}")

    ds = plan.get("data_strategy") or {}
    if isinstance(ds, dict):
        for field in DATA_STRATEGY_REQUIRED:
            if field not in ds:
                errors.append(f"data_strategy missing field: {field}")

    fs = plan.get("feature_strategy") or {}
    if isinstance(fs, dict):
        for field in FEATURE_STRATEGY_REQUIRED:
            if field not in fs:
                errors.append(f"feature_strategy missing field: {field}")

    ms = plan.get("model_strategy") or {}
    if isinstance(ms, dict):
        for field in MODEL_STRATEGY_REQUIRED:
            if field not in ms:
                errors.append(f"model_strategy missing field: {field}")

    vs = plan.get("validation_strategy") or {}
    if isinstance(vs, dict):
        for field in VALIDATION_STRATEGY_REQUIRED:
            if field not in vs:
                errors.append(f"validation_strategy missing field: {field}")
        split = vs.get("split_strategy", "")
        if split and split not in VALID_SPLIT_STRATEGIES:
            errors.append(f"Invalid split_strategy: {split}")
        n_splits = vs.get("n_splits")
        if n_splits is not None and (not isinstance(n_splits, int) or n_splits < 2 or n_splits > 10):
            errors.append(f"n_splits must be int between 2 and 10, got: {n_splits}")

    es = plan.get("evaluation_strategy") or {}
    if isinstance(es, dict):
        for field in EVALUATION_STRATEGY_REQUIRED:
            if field not in es:
                errors.append(f"evaluation_strategy missing field: {field}")

    hs = plan.get("hpo_strategy") or {}
    if isinstance(hs, dict):
        for field in HPO_STRATEGY_REQUIRED:
            if field not in hs:
                errors.append(f"hpo_strategy missing field: {field}")
        if hs.get("search_method") not in VALID_SEARCH_METHODS:
            errors.append(f"Invalid search_method: {hs.get('search_method')}")
        if hs.get("budget_level") not in VALID_BUDGET_LEVELS:
            errors.append(f"Invalid budget_level: {hs.get('budget_level')}")

    confidence = plan.get("confidence_score")
    if confidence is not None:
        if not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
            errors.append(f"confidence_score must be float between 0.0 and 1.0, got: {confidence}")

    return {"is_valid": len(errors) == 0, "errors": errors}
