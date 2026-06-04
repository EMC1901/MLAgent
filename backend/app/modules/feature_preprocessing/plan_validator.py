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
import logging
from typing import Dict, Any, List
from app.shared.registry.fp_capability_registry import get_fp_capability_by_id, CAPABILITY_GROUPS


logger = logging.getLogger(__name__)


VALID_EXECUTION_SCOPES = {"dataset_profile_only", "train_only", "fold_only"}
VALID_FIT_TRANSFORM_SCOPES = {"train_fold_only", "fold_only", "train_only", "dataset_profile_only"}
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

    logger.debug("=== validate_preprocessing_plan ===")

    if not plan:
        errors.append("PreprocessingPlan is empty.")
        logger.debug("FAILED: plan is empty")
        return {"is_valid": False, "errors": errors, "warnings": warnings}

    n_ops = len(plan.get("operation_sequence", []))
    n_cols = len(plan.get("column_policies", []))
    logger.debug("plan structure: %d ops, %d column_policies, %d feature_group_policies, %d capability_groups_used",
          n_ops, n_cols,
          len(plan.get("feature_group_policies", [])),
          len(plan.get("capability_groups_used", [])))

    # 0. Auto-repair common LLM field-value confusions before strict validation
    repair_warnings = _repair_common_llm_mistakes(plan)
    if repair_warnings:
        logger.debug("auto-repair: %d fixes applied — %s", len(repair_warnings), repair_warnings)
    warnings.extend(repair_warnings)

    # 1. Top-level required fields
    required_top = ["plan_version", "global_policy", "capability_groups_used", "operation_sequence", "rejected_operations", "warnings_for_downstream"]
    for field in required_top:
        if field not in plan:
            errors.append(f"Missing required field: '{field}'")
            logger.debug("missing top-level field: %s", field)

    if errors:
        logger.debug("FAILED after top-level field check: %d errors", len(errors))
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
            logger.debug("invalid capability_group: %s", group)

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

    is_valid = len(errors) == 0
    logger.debug("validation result: is_valid=%s errors=%d warnings=%d",
          is_valid, len(errors), len(warnings))
    if errors:
        logger.debug("ERRORS: %s", errors[:10])
    if warnings:
        logger.debug("WARNINGS: %s", warnings[:10])
    return {"is_valid": is_valid, "errors": errors, "warnings": warnings}


def _repair_common_llm_mistakes(plan: Dict[str, Any]) -> List[str]:
    """Auto-repair known LLM field-value confusions. Returns repair warnings.

    Repairs performed:
    1.  feature_group_policies[*].policy — LLM confuses keep/drop/... (column
        actions) with preserve/filter/... (group policies).
    2.  column_policies[*].action — reverse of above.
    3.  operation_sequence[*].target_columns / .target_feature_groups — LLM
        outputs null instead of [] for empty lists, which Pydantic rejects.
    4.  Any other list-typed field where the LLM wrote null instead of [].
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

    # Repair null → [] for list fields in operation_sequence
    _repair_null_lists(plan, warnings)

    return warnings


# Fields whose value should be a list but the LLM may emit null
_LIST_FIELDS_TO_REPAIR = {
    "target_columns", "target_feature_groups", "capability_groups_used",
    "column_policies", "feature_group_policies", "operation_sequence",
    "warnings_for_downstream", "model_family_specific_notes",
    "rejected_operations", "operations", "evidence", "preprocessing_needs",
    "feature_names", "affected_columns",
}

# Fields whose value should be a dict but the LLM may emit null
_DICT_FIELDS_TO_REPAIR = {
    "parameters",
}

# Nested model fields — LLM may emit null instead of omitting the key,
# causing Pydantic to reject with "Input should be a valid object"
_NESTED_MODEL_FIELDS_TO_REPAIR = {
    "decision_rationale", "leakage_prevention", "variant_strategy",
    "global_policy",
}


def _repair_null_lists(obj, warnings: List[str], path: str = "plan"):
    """Recursively replace None with valid default for known typed fields."""
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if v is None:
                if k in _LIST_FIELDS_TO_REPAIR:
                    obj[k] = []
                    warnings.append(f"Auto-repaired {path}.{k}: null → []")
                elif k in _DICT_FIELDS_TO_REPAIR:
                    obj[k] = {}
                    warnings.append(f"Auto-repaired {path}.{k}: null → {{}}")
                elif k in _NESTED_MODEL_FIELDS_TO_REPAIR:
                    obj[k] = {}
                    warnings.append(f"Auto-repaired {path}.{k}: null → {{}} (nested model)")
            elif isinstance(v, (dict, list)):
                _repair_null_lists(v, warnings, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, (dict, list)):
                _repair_null_lists(item, warnings, f"{path}[{i}]")


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
        logger.debug("global_policy: missing leakage_prevention")
    else:
        scope = leakage.get("fit_transform_scope", "")
        if scope not in VALID_FIT_TRANSFORM_SCOPES:
            errors.append(f"fit_transform_scope '{scope}' is invalid. Must be one of: {VALID_FIT_TRANSFORM_SCOPES}")
            logger.debug("global_policy: invalid fit_transform_scope='%s'", scope)
        elif scope != "train_fold_only":
            logger.debug("global_policy: fit_transform_scope='%s' (non-legacy, accepted)", scope)
        if not leakage.get("target_column_excluded", False):
            errors.append("target_column_excluded must be true.")
            logger.debug("global_policy: target_column_excluded=false")
        if not leakage.get("id_columns_excluded", True):
            warnings.append("id_columns_excluded is false — ID columns may leak into model.")
            logger.debug("global_policy: id_columns_excluded=false")
        if leakage.get("target_aware_selection_allowed", False):
            warnings.append("target_aware_selection_allowed is true — ensure fold-safe execution.")
            logger.debug("global_policy: target_aware_selection_allowed=true")

    variant = gp.get("variant_strategy", {})
    if variant.get("mode") not in VALID_VARIANT_MODES:
        errors.append(f"variant_strategy.mode must be one of: {VALID_VARIANT_MODES}")
        logger.debug("global_policy: invalid variant_strategy.mode='%s'", variant.get("mode"))


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
        logger.debug("operation_sequence: empty")
        return

    logger.debug("operation_sequence: validating %d operations ...", len(ops))
    seen_op_ids = set()
    last_order = 0
    rationale_issues = 0

    for i, op in enumerate(ops):
        prefix = f"operation_sequence[{i}]"

        step_order = op.get("step_order", 0)
        if step_order <= last_order:
            warnings.append(f"{prefix}: step_order {step_order} is not strictly > {last_order}.")
        last_order = step_order

        capability_id = op.get("capability_id", "")
        if not capability_id:
            errors.append(f"{prefix}: missing capability_id.")
            logger.debug("op[%d]: missing capability_id", i)
            continue

        # Check Registry
        cap = get_fp_capability_by_id(capability_id)
        if cap is None:
            errors.append(f"{prefix}: capability_id '{capability_id}' is not in the FP Capability Registry.")
            logger.debug("op[%d]: unknown capability_id='%s'", i, capability_id)
            continue

        if cap.status != "available":
            errors.append(f"{prefix}: capability '{capability_id}' has status '{cap.status}', not 'available'.")
            logger.debug("op[%d]: capability '%s' status=%s", i, capability_id, cap.status)

        # Check execution_scope
        scope = op.get("execution_scope", "")
        if scope not in VALID_EXECUTION_SCOPES:
            errors.append(f"{prefix}: invalid execution_scope '{scope}'.")
            logger.debug("op[%d]: invalid execution_scope='%s' for '%s'", i, scope, capability_id)

        # fit-type operations must respect capability's declared fit_scope
        fit_types = {"imputation", "scaling", "transformation", "feature_selection", "dimensionality_reduction"}
        if cap.operation_type in fit_types:
            allowed_scope = cap.fit_scope or "fold_only"
            scope_rank = {"fold_only": 0, "train_only": 1, "dataset_profile_only": 2}
            if scope_rank.get(scope, -1) > scope_rank.get(allowed_scope, 0):
                errors.append(
                    f"{prefix}: operation_type '{cap.operation_type}' fit_scope is '{allowed_scope}' but got looser scope '{scope}'."
                )
                logger.debug("op[%d]: scope mismatch — '%s' fit_scope=%s but plan gave %s", i, capability_id, allowed_scope, scope)

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

        # Check rationale — empty fields are warnings, not errors
        rationale = op.get("decision_rationale", {})
        if not rationale:
            warnings.append(f"{prefix}: missing decision_rationale (empty object).")
            rationale_issues += 1
        else:
            for rfield in RATIONALE_REQUIRED:
                val = rationale.get(rfield)
                # None or missing → error (structural problem)
                if rfield not in rationale:
                    errors.append(f"{prefix}: decision_rationale missing '{rfield}'.")
                    logger.debug("op[%d]: rationale missing field '%s'", i, rfield)
                # Empty string or empty list → warning (LLM decided no evidence/risk/etc. needed)
                elif isinstance(val, (list, str)) and not val:
                    warnings.append(f"{prefix}: decision_rationale.{rfield} is empty.")
                    rationale_issues += 1

        # Check parameters schema
        if cap.parameters_schema:
            params = op.get("parameters", {})
            for pkey, pschema in cap.parameters_schema.items():
                if "default" not in pschema and pkey not in params:
                    warnings.append(f"{prefix}: parameter '{pkey}' has no default and was not specified.")

        # Log each operation for traceability
        logger.debug("op[%d]: id=%s cap=%s scope=%s group=%s fit_scope=%s",
              i, operation_id or "?", capability_id, scope,
              cap.capability_group if cap else "?", cap.fit_scope if cap else "?")

    logger.debug("operation_sequence DONE: %d ops checked, %d rationale issues (warnings)",
          len(ops), rationale_issues)


def _validate_feature_group_policy(fgp: Dict, idx: int, errors: List[str]):
    prefix = f"feature_group_policies[{idx}]"
    if not fgp.get("feature_group"):
        errors.append(f"{prefix}: missing feature_group.")
    if fgp.get("policy") not in VALID_POLICIES:
        errors.append(f"{prefix}: invalid policy '{fgp.get('policy')}'.")
    operations = fgp.get("operations", [])
    for j, op in enumerate(operations):
        cap_id = op.get("capability_id", "")
        if not cap_id:
            errors.append(f"{prefix}.operations[{j}]: missing capability_id.")
        else:
            cap = get_fp_capability_by_id(cap_id)
            if cap is None:
                errors.append(f"{prefix}.operations[{j}]: capability_id '{cap_id}' is not in the FP Capability Registry.")
            elif cap.status != "available":
                errors.append(f"{prefix}.operations[{j}]: capability '{cap_id}' has status '{cap.status}', not 'available'.")
        rationale = op.get("decision_rationale", {})
        for rfield in RATIONALE_REQUIRED:
            val = rationale.get(rfield)
            if rfield not in rationale:
                errors.append(f"{prefix}.operations[{j}]: decision_rationale missing '{rfield}'.")
            elif isinstance(val, (list, str)) and not val:
                # Empty list/string is semantically valid (no evidence/risk cited)
                pass


def _validate_rejected_operation(ro: Dict, idx: int, errors: List[str]):
    prefix = f"rejected_operations[{idx}]"
    cap_id = ro.get("capability_id", "")
    if not cap_id:
        errors.append(f"{prefix}: missing capability_id.")
    else:
        cap = get_fp_capability_by_id(cap_id)
        if cap is None:
            errors.append(f"{prefix}: capability_id '{cap_id}' is not in the FP Capability Registry.")
    if not ro.get("reason"):
        errors.append(f"{prefix}: missing reason.")
