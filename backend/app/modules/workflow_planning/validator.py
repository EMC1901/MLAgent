import re
from typing import Dict, Any, List
from app.shared.registry.featurizer_registry import resolve, get_default_fallback
from app.shared.registry.fe_capability_registry import get_fe_capability_by_id


REQUIRED_TOP_LEVEL_FIELDS = [
    "task_summary", "data_strategy", "feature_strategy", "preprocessing_intent",
    "model_strategy", "validation_strategy", "evaluation_strategy", "hpo_strategy",
    "interpretability_strategy", "pipeline_generation_input", "workflow_rationale",
    "planning_warnings", "planning_assumptions",
    "llm_reasoning_summary", "confidence_score",
]

TASK_SUMMARY_FIELDS = ["task_type", "input_modality", "prediction_target", "material_domain", "primary_goal"]
DATA_STRATEGY_FIELDS = ["input_columns", "target_column", "required_cleaning_steps", "target_handling", "duplicate_handling", "missing_value_strategy"]
FEATURE_STRATEGY_FIELDS = ["feature_type", "executable_featurizers", "selected_feature_actions", "rejected_feature_actions"]
MODEL_STRATEGY_FIELDS = ["candidate_model_families", "baseline_models", "preferred_model_bias", "excluded_model_families", "selected_model_actions", "rejected_model_actions"]
VALIDATION_STRATEGY_FIELDS = ["split_strategy", "n_splits", "test_size", "random_state", "stratification_required"]
EVALUATION_STRATEGY_FIELDS = ["primary_metric", "secondary_metrics", "metric_direction"]
HPO_STRATEGY_FIELDS = ["enabled", "search_method", "budget_level", "max_trials"]
INTERPRETABILITY_STRATEGY_FIELDS = ["enabled", "methods", "priority"]
PIPELINE_INPUT_FIELDS = ["pipeline_steps", "required_components"]
PREPROCESSING_INTENT_FIELDS = ["high_level_goals"]
WORKFLOW_RATIONALE_FIELDS = ["overall_reasoning_summary", "key_assumptions", "known_risks"]

VALID_TASK_TYPES = {"regression", "classification", "ranking"}
VALID_INPUT_MODALITIES = {"composition", "structure", "descriptor", "text", "mixed"}
VALID_SPLIT_STRATEGIES = {"train_test_split", "k_fold_cross_validation", "stratified_k_fold", "repeated_cv"}
VALID_SEARCH_METHODS = {"grid_search", "random_search", "bayesian_optimization", "optuna_tpe", "successive_halving"}
VALID_BUDGET_LEVELS = {"low", "medium", "high"}
VALID_METRIC_DIRECTIONS = {"minimize", "maximize"}
VALID_PRIORITIES = {"required", "recommended", "optional", "fallback"}

RATIONALE_REQUIRED_FIELDS = ["reason", "evidence", "material_science_basis", "expected_benefit", "risk", "fallback"]
MODEL_RATIONALE_REQUIRED_FIELDS = ["reason", "evidence", "expected_performance", "risk", "fallback"]

FORBIDDEN_CODE_PATTERNS = [
    "import pandas", "import numpy", "import sklearn", "from sklearn",
    "def train", "def predict", "def fit", "class Model", "exec(",
    "model.fit", "model.predict",
]

# Regex patterns for fabricated metrics: metric name followed by a numeric value
# e.g. "MAE of 0.05" or "R�?of 0.92" �?this indicates the LLM invented results.
# Mere mention of the metric name (e.g. "use MAE as primary_metric") is allowed.
FORBIDDEN_METRIC_REGEX = re.compile(
    r"(?:MAE|RMSE|R虏|R2)\s+of\s+[\d.\-]"
    r"|accuracy\s+of\s+[\d.\-]"
    r"|F1\s+score\s+of\s+[\d.\-]"
    r"|(?:training|validation|test)\s+loss\s*[=:]\s*[\d.\-]",
    re.IGNORECASE,
)


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
    _check_sub_object("preprocessing_intent", plan.get("preprocessing_intent", {}), PREPROCESSING_INTENT_FIELDS, errors)
    _check_sub_object("model_strategy", plan.get("model_strategy", {}), MODEL_STRATEGY_FIELDS, errors)
    _check_sub_object("validation_strategy", plan.get("validation_strategy", {}), VALIDATION_STRATEGY_FIELDS, errors)
    _check_sub_object("evaluation_strategy", plan.get("evaluation_strategy", {}), EVALUATION_STRATEGY_FIELDS, errors)
    _check_sub_object("hpo_strategy", plan.get("hpo_strategy", {}), HPO_STRATEGY_FIELDS, errors)
    _check_sub_object("interpretability_strategy", plan.get("interpretability_strategy", {}), INTERPRETABILITY_STRATEGY_FIELDS, errors)
    _check_sub_object("pipeline_generation_input", plan.get("pipeline_generation_input", {}), PIPELINE_INPUT_FIELDS, errors)
    _check_sub_object("workflow_rationale", plan.get("workflow_rationale", {}), WORKFLOW_RATIONALE_FIELDS, errors)

    _check_enum_values(plan, errors)
    _check_confidence_score(plan, errors)
    _check_arrays(plan, errors)
    _check_forbidden_content(plan, errors)
    _check_featurizer_registry(plan, errors)
    _check_feature_strategy_actions(plan, errors)
    _check_model_strategy_actions(plan, errors)
    _check_preprocessing_intent(plan, errors)

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
        errors.append(f"Invalid split_strategy '{split_strategy}'.")

    hpo_strategy = plan.get("hpo_strategy", {})
    search_method = hpo_strategy.get("search_method")
    if search_method and search_method not in VALID_SEARCH_METHODS:
        errors.append(f"Invalid search_method '{search_method}'.")
    budget_level = hpo_strategy.get("budget_level")
    if budget_level and budget_level not in VALID_BUDGET_LEVELS:
        errors.append(f"Invalid budget_level '{budget_level}'.")

    evaluation_strategy = plan.get("evaluation_strategy", {})
    metric_direction = evaluation_strategy.get("metric_direction")
    if metric_direction and metric_direction not in VALID_METRIC_DIRECTIONS:
        errors.append(f"Invalid metric_direction '{metric_direction}'.")

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
    else:
        baseline_count = len(plan["model_strategy"]["baseline_models"])
        if baseline_count == 0:
            errors.append("'model_strategy.baseline_models' must contain exactly 1 model family, got 0.")
        elif baseline_count > 1:
            errors.append(f"'model_strategy.baseline_models' must contain exactly 1 model family, got {baseline_count}: {plan['model_strategy']['baseline_models']}. Choose the single most appropriate baseline.")
    if not isinstance(plan.get("preprocessing_intent", {}).get("high_level_goals"), list):
        errors.append("'preprocessing_intent.high_level_goals' must be an array.")
    if not isinstance(plan.get("workflow_rationale", {}).get("key_assumptions"), list):
        errors.append("'workflow_rationale.key_assumptions' must be an array.")
    if not isinstance(plan.get("workflow_rationale", {}).get("known_risks"), list):
        errors.append("'workflow_rationale.known_risks' must be an array.")


def _check_forbidden_content(plan: Dict[str, Any], errors: List[str]):
    plan_str = str(plan).lower()

    # Code injection patterns �?simple substring match
    for forbidden in FORBIDDEN_CODE_PATTERNS:
        if forbidden.lower() in plan_str:
            errors.append(
                f"Forbidden content detected: '{forbidden}'. "
                "Workflow Plan must not contain executable code, training results, or fabricated metrics."
            )

    # Fabricated metric patterns �?only flag when a metric name is
    # followed by a numeric value (e.g. "MAE of 0.05"), not when the
    # metric is merely mentioned as a planning choice.
    metric_match = FORBIDDEN_METRIC_REGEX.search(plan_str)
    if metric_match:
        errors.append(
            f"Forbidden content detected: '{metric_match.group()}'. "
            "Workflow Plan must not contain executable code, training results, or fabricated metrics."
        )


def _check_featurizer_registry(plan: Dict[str, Any], errors: List[str]):
    feature_strategy = plan.get("feature_strategy") or {}
    task_summary = plan.get("task_summary") or {}
    input_modality = task_summary.get("input_modality", "")
    task_type = task_summary.get("task_type")

    executable = feature_strategy.get("executable_featurizers")
    recommended = feature_strategy.get("recommended_featurizers")

    if executable is not None:
        if not isinstance(executable, list):
            errors.append("'feature_strategy.executable_featurizers' must be an array.")
            return
        for name in executable:
            result = resolve(name)
            if result.resolved_id is None:
                errors.append(
                    f"Executable featurizer '{name}' is not registered in the Featurizer Registry."
                )
                continue
            if result.status == "planned":
                errors.append(
                    f"Featurizer '{name}' has status 'planned' and cannot be used as executable."
                )
            elif result.status not in ("available",):
                errors.append(
                    f"Featurizer '{name}' has status '{result.status}', not 'available'."
                )
        if len(executable) == 0 and input_modality:
            fallback = get_default_fallback(input_modality, task_type)
            if fallback.fallback_featurizer_id:
                errors.append(
                    f"'executable_featurizers' is empty. Fallback '{fallback.fallback_featurizer_id}' available."
                )
            else:
                errors.append(f"'executable_featurizers' is empty and no fallback available.")
        return

    if recommended is not None and isinstance(recommended, list) and len(recommended) > 0:
        resolvable_count = 0
        for name in recommended:
            result = resolve(name)
            if result.resolved_id is not None and result.status == "available":
                resolvable_count += 1
        if resolvable_count == 0 and input_modality:
            fallback = get_default_fallback(input_modality, task_type)
            if fallback.fallback_featurizer_id:
                errors.append(
                    f"No recommended_featurizers resolve to available. "
                    f"Fallback '{fallback.fallback_featurizer_id}' available."
                )
            else:
                errors.append(f"No recommended_featurizers resolve to available featurizers.")
        return

    if input_modality:
        fallback = get_default_fallback(input_modality, task_type)
        if fallback.fallback_featurizer_id:
            errors.append(
                f"No featurizers specified. Fallback '{fallback.fallback_featurizer_id}' available."
            )
        else:
            errors.append(f"No featurizers specified and no fallback available.")


def _check_feature_strategy_actions(plan: Dict[str, Any], errors: List[str]):
    """Validate capability-aware selected_feature_actions and rejected_feature_actions."""
    feature_strategy = plan.get("feature_strategy") or {}

    selected_actions = feature_strategy.get("selected_feature_actions", [])
    rejected_actions = feature_strategy.get("rejected_feature_actions", [])

    if not isinstance(selected_actions, list):
        errors.append("'feature_strategy.selected_feature_actions' must be an array.")
        return
    if not isinstance(rejected_actions, list):
        errors.append("'feature_strategy.rejected_feature_actions' must be an array.")

    seen_action_ids = set()
    for i, action in enumerate(selected_actions):
        prefix = f"selected_feature_actions[{i}]"

        capability_id = action.get("capability_id", "")
        if not capability_id:
            errors.append(f"{prefix}: missing 'capability_id'.")
            continue

        # Check registry
        cap = get_fe_capability_by_id(capability_id)
        if cap is None:
            errors.append(
                f"{prefix}: capability_id '{capability_id}' is not in the FE Capability Registry."
            )
            continue

        if cap.status == "planned":
            priority = action.get("priority", "")
            if priority in ("required", "recommended"):
                errors.append(
                    f"{prefix}: capability_id '{capability_id}' has status 'planned' "
                    f"but is used as '{priority}' action. Planned capabilities cannot be required or recommended."
                )
        elif cap.status not in ("available", "experimental"):
            errors.append(
                f"{prefix}: capability_id '{capability_id}' has status '{cap.status}' and cannot be used."
            )

        # Cross-registry check: capability must have at least one executable featurizer
        featurizer_ids = cap.featurizer_ids
        if not featurizer_ids:
            priority = action.get("priority", "")
            if priority in ("required", "recommended"):
                errors.append(
                    f"{prefix}: capability_id '{capability_id}' has no executable "
                    f"featurizer_ids mapped. It cannot be used as a '{priority}' action. "
                    f"Use as 'optional' at most."
                )
        else:
            from app.shared.registry.featurizer_registry import (
                get_featurizer_by_id,
                get_featurizer_effective_status,
            )
            any_available = False
            for fid in featurizer_ids:
                spec = get_featurizer_by_id(fid)
                if spec and get_featurizer_effective_status(spec) == "available":
                    any_available = True
                    break
            if not any_available:
                errors.append(
                    f"{prefix}: capability_id '{capability_id}' maps to featurizers "
                    f"{featurizer_ids} but none are currently available (check dependencies)."
                )

        # Note: required_input_columns validation is deferred to Feature Engineering
        # execution time, where the actual dataset columns are available. The
        # planner's job is to select capabilities appropriate for the task's
        # input_modality and task_type �?not to verify dataset column names.

        # Check priority
        priority = action.get("priority", "")
        if priority and priority not in VALID_PRIORITIES:
            errors.append(f"{prefix}: invalid priority '{priority}'.")

        # Check rationale
        rationale = action.get("decision_rationale", {})
        if not rationale:
            errors.append(f"{prefix}: missing 'decision_rationale'.")
        else:
            for rfield in RATIONALE_REQUIRED_FIELDS:
                if rfield not in rationale or not rationale[rfield]:
                    errors.append(f"{prefix}: decision_rationale missing '{rfield}'.")

        # Check action_id uniqueness
        action_id = action.get("action_id", "")
        if action_id:
            if action_id in seen_action_ids:
                errors.append(f"{prefix}: duplicate action_id '{action_id}'.")
            seen_action_ids.add(action_id)

    # Validate rejected actions
    for i, action in enumerate(rejected_actions):
        prefix = f"rejected_feature_actions[{i}]"
        capability_id = action.get("capability_id", "")
        if not capability_id:
            errors.append(f"{prefix}: missing 'capability_id'.")
        if not action.get("reason"):
            errors.append(f"{prefix}: missing 'reason' for rejecting '{capability_id}'.")


def _check_model_strategy_actions(plan: Dict[str, Any], errors: List[str]):
    """Validate model_strategy selected_model_actions and rejected_model_actions."""
    model_strategy = plan.get("model_strategy") or {}

    selected_actions = model_strategy.get("selected_model_actions", [])
    rejected_actions = model_strategy.get("rejected_model_actions", [])

    if not isinstance(selected_actions, list):
        errors.append("'model_strategy.selected_model_actions' must be an array.")
        return
    if not isinstance(rejected_actions, list):
        errors.append("'model_strategy.rejected_model_actions' must be an array.")

    seen_action_ids = set()
    for i, action in enumerate(selected_actions):
        prefix = f"selected_model_actions[{i}]"

        model_family = action.get("model_family", "")
        if not model_family:
            errors.append(f"{prefix}: missing 'model_family'.")
            continue

        priority = action.get("priority", "")
        if priority and priority not in VALID_PRIORITIES:
            errors.append(f"{prefix}: invalid priority '{priority}'.")

        rationale = action.get("decision_rationale", {})
        if not rationale:
            errors.append(f"{prefix}: missing 'decision_rationale'.")
        else:
            for rfield in MODEL_RATIONALE_REQUIRED_FIELDS:
                if rfield not in rationale or not rationale[rfield]:
                    errors.append(f"{prefix}: decision_rationale missing '{rfield}'.")

        action_id = action.get("action_id", "")
        if action_id:
            if action_id in seen_action_ids:
                errors.append(f"{prefix}: duplicate action_id '{action_id}'.")
            seen_action_ids.add(action_id)

    for i, action in enumerate(rejected_actions):
        prefix = f"rejected_model_actions[{i}]"
        model_family = action.get("model_family", "")
        if not model_family:
            errors.append(f"{prefix}: missing 'model_family'.")
        if not action.get("reason"):
            errors.append(f"{prefix}: missing 'reason' for rejecting '{model_family}'.")


def _check_preprocessing_intent(plan: Dict[str, Any], errors: List[str]):
    """Validate that preprocessing_intent only contains high-level goals."""
    intent = plan.get("preprocessing_intent") or {}
    non_final = intent.get("non_final_notes", "")

    if "executable preprocessing" not in non_final.lower() and "final" not in non_final.lower():
        errors.append(
            "preprocessing_intent.non_final_notes must indicate that final preprocessing "
            "decisions will be made after Feature Engineering output is available."
        )

    # Check that no column-level operations are specified
    forbidden_intent_keys = {"column_operations", "operation_sequence", "feature_group_policies", "preprocessing_plan"}
    for key in forbidden_intent_keys:
        if key in intent:
            errors.append(
                f"preprocessing_intent must not contain '{key}'. "
                "Only high-level goals are allowed. Column-level operations belong to PreprocessingPlan."
            )
