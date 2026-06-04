from typing import List
from app.modules.iteration_decision.schemas import IterationPlan, RevisedWorkflowPlan, IterationRerunPlan
from app.modules.iteration_decision.enums import VALID_TARGET_STAGES


def validate_iteration_plan(plan: IterationPlan) -> dict:
    """Validate the built iteration plan for feasibility."""
    errors: List[str] = []
    warnings: List[str] = []

    if not plan:
        return {"is_valid": False, "errors": ["No iteration plan provided."], "warnings": []}

    # rerun_from_stage must be valid
    if plan.rerun_from_stage not in VALID_TARGET_STAGES:
        errors.append(f"Invalid rerun_from_stage: '{plan.rerun_from_stage}'.")

    # Must have at least one stage change
    if not plan.stage_changes:
        warnings.append("No stage changes specified — iteration may not improve results.")

    # Each stage change must have a valid stage
    for sc in plan.stage_changes:
        if sc.stage not in VALID_TARGET_STAGES:
            errors.append(f"Stage change has invalid stage: '{sc.stage}'.")
        if not sc.description:
            warnings.append(f"Stage '{sc.stage}' change has no description.")
        if not sc.rationale:
            warnings.append(f"Stage '{sc.stage}' change has no rationale.")

    # Must have a stop condition
    if not plan.stop_condition:
        warnings.append("No stop condition specified — iteration may run indefinitely.")

    is_valid = len(errors) == 0
    return {"is_valid": is_valid, "errors": errors, "warnings": warnings}


def validate_revised_workflow_plan(plan: RevisedWorkflowPlan) -> dict:
    """Validate the revised workflow plan structure."""
    errors: List[str] = []
    warnings: List[str] = []

    if not plan:
        return {"is_valid": False, "errors": ["No revised workflow plan."], "warnings": []}

    if not plan.changed_sections:
        warnings.append("Revised plan has no changed sections.")
    if not plan.llm_reasoning_summary:
        warnings.append("Revised plan has no reasoning summary.")

    is_valid = len(errors) == 0
    return {"is_valid": is_valid, "errors": errors, "warnings": warnings}


def validate_rerun_plan(plan: IterationRerunPlan) -> dict:
    """Validate the re-run plan."""
    errors: List[str] = []
    warnings: List[str] = []

    if not plan:
        return {"is_valid": False, "errors": ["No rerun plan."], "warnings": []}

    if plan.rerun_from_stage and plan.rerun_from_stage not in VALID_TARGET_STAGES:
        errors.append(f"Invalid rerun_from_stage: '{plan.rerun_from_stage}'.")
    if not plan.rerun_stages:
        warnings.append("Rerun plan has no stages to rerun.")
    if not plan.expected_improvement_targets:
        warnings.append("Rerun plan has no expected improvement targets.")

    is_valid = len(errors) == 0
    return {"is_valid": is_valid, "errors": errors, "warnings": warnings}
