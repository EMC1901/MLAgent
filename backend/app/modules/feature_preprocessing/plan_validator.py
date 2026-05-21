"""
PreprocessingPlan Validator.

Validates LLM-generated PreprocessingPlan against:
1. Capability Registry constraints
2. Data leakage prevention rules
3. Operational sequence ordering
4. Rationale completeness
5. Schema compliance

Includes auto-repair for common LLM field-value confusions (e.g. using
column_policies action values in feature_group_policies policy fields).
"""
from typing import Dict, Any, List
from app.shared.registry.fp_capability_registry import get_fp_capability_by_id, CAPABILITY_GROUPS

VALID_EXECUTION_SCOPES = {"dataset_profile_only", "train_only", "fold_only"}
VALID_ACTIONS = {"keep", "drop", "transform", "flag_for_review"}
VALID_POLICIES = {"preserve", "filter", "transform", "reduce_dimension", "drop", "flag_for_review"}
VALID_VARIANT_MODES = {"single", "model_family_specific", "multiple_variants"}
RATIONALE_REQUIRED = {"reason", "evidence", "expected_benefit", "risk", "fallback"}

# Maps from column-level action values → group-level policy values (LLM confusion repair)
ACTION_TO_POLICY_REPAIR: Dict[str, str] = {
    "keep": "preserve",
}

# Maps from group-level policy values → column-level action values (LLM confusion repair)
POLICY_TO_ACTION_REPAIR: Dict[str, str] = {
    "preserve": "keep",
    "filter": "drop",
    "reduce_dimension": "drop",
}

# Ordered operation types for sequence validation
OPERATION_ORDER = [
    "leakage_detection",
    "analysis",  # missingness analysis
    "filtering",  # low information filtering
    "imputation",
    "transformation",
    "scaling",
    "redundancy_filter",
    "feature_selection",
    "group_policy",
    "dimensionality_reduction",
    "lineage",
    "artifact_tracking",
]


def validate_preprocessing_plan(plan: Dict[str, Any], decision_input: Dict[str, Any] = None) -> Dict[str, Any]:
    """Validate a PreprocessingPlan. Returns {"is_valid": bool, "errors": [str], "warnings": [str]}."""
    errors: List[str] = []
    warnings: List[str] = []

    if not plan:
        errors.append("PreprocessingPlan is empty.")
        return {"is_valid": False, "errors": errors, "warnings": warnings}

    # 0. Auto-repair common LLM field-value confusions before strict validation
    repair_warnings = _repair_common_llm_mistakes(plan)
    warnings.extend(repair_warnings)

    # 1. Top-level required fields
    required_top = ["plan_version", "global_policy", "capability_groups_used", "operation_sequence", "rejected_operations", "warnings_for_downstream"]
    for field in required_top:
        if field not in plan:
            errors.append(f"Missing required field: '{field}'")

    if errors:
        return {"is_valid": False, "errors": errors, "warnings": warnings}

    # 2. Validate global_policy
    global_policy = plan.get("global_policy", {})
    _validate_global_policy(global_policy, errors, warnings)

    # 3. Validate capability_groups_used
    groups_used = plan.get("capability_groups_used", [])
    valid_groups = set(CAPABILITY_GROUPS.keys())
    for group in groups_used:
        if group not in valid_groups:
            errors.append(f"Invalid capability_group '{group}'. Must be one of: {valid_groups}")

    # 4. Validate column_policies
    column_policies = plan.get("column_policies", [])
    for i, cp in enumerate(column_policies):
        _validate_column_policy(cp, i, errors)

    # 5. Validate operation_sequence
    operation_sequence = plan.get("operation_sequence", [])
    _validate_operation_sequence(operation_sequence, errors, warnings, decision_input)

    # 6. Validate feature_group_policies
    fg_policies = plan.get("feature_group_policies", [])
    for i, fgp in enumerate(fg_policies):
        _validate_feature_group_policy(fgp, i, errors)

    # 7. Validate rejected_operations
    rejected = plan.get("rejected_operations", [])
    for i, ro in enumerate(rejected):
        _validate_rejected_operation(ro, i, errors)

    return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def _repair_common_llm_mistakes(plan: Dict[str, Any]) -> List[str]:
    """Auto-repair known LLM field-value confusions. Returns repair warnings.

    The LLM sometimes confuses column_policies[*].action values (keep/drop/...)
    with feature_group_policies[*].policy values (preserve/filter/...), and vice
    versa. These repairs fix such mistakes silently so the plan can proceed,
    while recording a warning for observability.
    """
    warnings: List[str] = []

    # Repair feature_group_policies[*].policy
    for i, fgp in enumerate(plan.get("feature_group_policies", [])):
        policy = fgp.get("policy", "")
        if policy and policy not in VALID_POLICIES:
            repaired = ACTION_TO_POLICY_REPAIR.get(policy, "") or _fuzzy_repair(policy, VALID_POLICIES)
            if repaired and repaired != policy:
                fgp["policy"] = repaired
                warnings.append(
                    f"Auto-repaired feature_group_policies[{i}].policy: "
                    f"'{policy}' → '{repaired}' (LLM used column action value in group policy field)"
                )

    # Repair column_policies[*].action
    for i, cp in enumerate(plan.get("column_policies", [])):
        action = cp.get("action", "")
        if action and action not in VALID_ACTIONS:
            repaired = POLICY_TO_ACTION_REPAIR.get(action, "") or _fuzzy_repair(action, VALID_ACTIONS)
            if repaired and repaired != action:
                cp["action"] = repaired
                warnings.append(
                    f"Auto-repaired column_policies[{i}].action: "
                    f"'{action}' → '{repaired}' (LLM used group policy value in column action field)"
                )

    return warnings


def _fuzzy_repair(value: str, valid_set: set) -> str:
    """Attempt to find the closest valid value via substring or prefix match."""
    value_lower = value.lower().strip()
    for valid in valid_set:
        if value_lower in valid or valid in value_lower:
            return valid
    for valid in valid_set:
        if len(value_lower) >= 3 and len(valid) >= 3:
            if valid[:3] == value_lower[:3]:
                return valid
    return ""


def _validate_global_policy(gp: Dict, errors: List[str], warnings: List[str]):
    leakage = gp.get("leakage_prevention", {})
    if not leakage:
        errors.append("global_policy.leakage_prevention is required.")
    else:
        if leakage.get("fit_transform_scope") not in ("train_fold_only",):
            errors.append("fit_transform_scope must be 'train_fold_only'.")
        if not leakage.get("target_column_excluded", False):
            errors.append("target_column_excluded must be true.")
        if not leakage.get("id_columns_excluded", True):
            warnings.append("id_columns_excluded is false — ID columns may leak into model.")
        if leakage.get("target_aware_selection_allowed", False):
            warnings.append("target_aware_selection_allowed is true — ensure fold-safe execution.")

    variant = gp.get("variant_strategy", {})
    if variant.get("mode") not in VALID_VARIANT_MODES:
        errors.append(f"variant_strategy.mode must be one of: {VALID_VARIANT_MODES}")


def _validate_column_policy(cp: Dict, idx: int, errors: List[str]):
    prefix = f"column_policies[{idx}]"
    if not cp.get("column_name"):
        errors.append(f"{prefix}: missing column_name.")
    if cp.get("action") not in VALID_ACTIONS:
        errors.append(f"{prefix}: invalid action '{cp.get('action')}'.")
    if not cp.get("reason"):
        errors.append(f"{prefix}: missing reason.")


def _validate_operation_sequence(ops: List[Dict], errors: List[str], warnings: List[str], decision_input: Dict = None):
    if not ops:
        errors.append("operation_sequence must not be empty.")
        return

    seen_op_ids = set()
    last_order = 0

    for i, op in enumerate(ops):
        prefix = f"operation_sequence[{i}]"

        step_order = op.get("step_order", 0)
        if step_order <= last_order:
            warnings.append(f"{prefix}: step_order {step_order} is not strictly > {last_order}.")
        last_order = step_order

        capability_id = op.get("capability_id", "")
        if not capability_id:
            errors.append(f"{prefix}: missing capability_id.")
            continue

        # Check Registry
        cap = get_fp_capability_by_id(capability_id)
        if cap is None:
            errors.append(f"{prefix}: capability_id '{capability_id}' is not in the FP Capability Registry.")
            continue

        if cap.status != "available":
            errors.append(f"{prefix}: capability '{capability_id}' has status '{cap.status}', not 'available'.")

        # Check execution_scope
        scope = op.get("execution_scope", "")
        if scope not in VALID_EXECUTION_SCOPES:
            errors.append(f"{prefix}: invalid execution_scope '{scope}'.")

        # fit-type operations must respect capability's declared fit_scope
        fit_types = {"imputation", "scaling", "transformation", "feature_selection", "dimensionality_reduction"}
        if cap.operation_type in fit_types:
            # fit_scope is the maximum allowed scope; scope must not be looser
            allowed_scope = cap.fit_scope or "fold_only"
            scope_rank = {"fold_only": 0, "train_only": 1, "dataset_profile_only": 2}
            if scope_rank.get(scope, -1) > scope_rank.get(allowed_scope, 0):
                errors.append(
                    f"{prefix}: operation_type '{cap.operation_type}' fit_scope is '{allowed_scope}' but got looser scope '{scope}'."
                )

        # Target-aware operations must match capability's fit_scope
        if cap.requires_target:
            allowed_scope = cap.fit_scope or "fold_only"
            scope_rank = {"fold_only": 0, "train_only": 1, "dataset_profile_only": 2}
            if scope_rank.get(scope, -1) > scope_rank.get(allowed_scope, 0):
                errors.append(
                    f"{prefix}: target-aware operation '{capability_id}' fit_scope is '{allowed_scope}' but got looser scope '{scope}'."
                )

        # Check operation_id uniqueness
        operation_id = op.get("operation_id", "")
        if operation_id:
            if operation_id in seen_op_ids:
                errors.append(f"{prefix}: duplicate operation_id '{operation_id}'.")
            seen_op_ids.add(operation_id)

        # Check rationale
        rationale = op.get("decision_rationale", {})
        if not rationale:
            errors.append(f"{prefix}: missing decision_rationale.")
        else:
            for rfield in RATIONALE_REQUIRED:
                if rfield not in rationale or (
                    isinstance(rationale[rfield], (list, str)) and not rationale[rfield]
                ):
                    errors.append(f"{prefix}: decision_rationale missing '{rfield}'.")

        # Check parameters schema
        if cap.parameters_schema:
            params = op.get("parameters", {})
            for pkey, pschema in cap.parameters_schema.items():
                if "default" not in pschema and pkey not in params:
                    warnings.append(f"{prefix}: parameter '{pkey}' has no default and was not specified.")


def _validate_feature_group_policy(fgp: Dict, idx: int, errors: List[str]):
    prefix = f"feature_group_policies[{idx}]"
    if not fgp.get("feature_group"):
        errors.append(f"{prefix}: missing feature_group.")
    if fgp.get("policy") not in VALID_POLICIES:
        errors.append(f"{prefix}: invalid policy '{fgp.get('policy')}'.")
    operations = fgp.get("operations", [])
    for j, op in enumerate(operations):
        if not op.get("capability_id"):
            errors.append(f"{prefix}.operations[{j}]: missing capability_id.")
        rationale = op.get("decision_rationale", {})
        for rfield in RATIONALE_REQUIRED:
            if rfield not in rationale:
                errors.append(f"{prefix}.operations[{j}]: decision_rationale missing '{rfield}'.")


def _validate_rejected_operation(ro: Dict, idx: int, errors: List[str]):
    prefix = f"rejected_operations[{idx}]"
    if not ro.get("capability_id"):
        errors.append(f"{prefix}: missing capability_id.")
    if not ro.get("reason"):
        errors.append(f"{prefix}: missing reason.")
