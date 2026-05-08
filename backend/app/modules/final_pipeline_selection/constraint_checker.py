import logging
from typing import List, Dict, Any

from app.modules.final_pipeline_selection.schemas import (
    CandidateSelectionItem,
    SelectionPolicy,
    ConstraintCheckResult,
)
from app.modules.final_pipeline_selection.enums import CandidateStatus

logger = logging.getLogger(__name__)


def check_constraints(
    candidates: List[CandidateSelectionItem],
    policy: SelectionPolicy,
    constraints: Dict[str, Any] = None,
) -> ConstraintCheckResult:
    constraints = constraints or {}
    result = ConstraintCheckResult(
        passed=True,
        hard_constraints_met=True,
        soft_constraints_met=True,
    )

    for c in candidates:
        if c.candidate_status == CandidateStatus.REJECTED:
            continue

        # Hard constraint: baseline as final
        if not policy.allow_baseline_as_final and c.pipeline_role == "baseline":
            c.candidate_status = CandidateStatus.REJECTED
            c.rejection_reason = "Baseline models not allowed as final selection."
            result.issues.append(f"Candidate {c.candidate_id}: baseline not allowed as final.")
            continue

        # Hard constraint: user constraints from selection input
        required_model_family = constraints.get("required_model_family")
        if required_model_family and c.model_family != required_model_family:
            c.candidate_status = CandidateStatus.REJECTED
            c.rejection_reason = f"Required model family is {required_model_family}."
            result.issues.append(f"Candidate {c.candidate_id}: model family mismatch.")
            continue

        max_hyperparameters = constraints.get("max_hyperparameters")
        if max_hyperparameters and len(c.hyperparameters) > max_hyperparameters:
            c.candidate_status = CandidateStatus.WARNING
            result.warnings.append(
                f"Candidate {c.candidate_id}: hyperparameter count {len(c.hyperparameters)} exceeds limit {max_hyperparameters}."
            )

    eligible = [c for c in candidates if c.candidate_status == CandidateStatus.ELIGIBLE]
    if not eligible:
        result.passed = False
        result.hard_constraints_met = False
        result.issues.append("No eligible candidates remain after constraint checking.")

    # Warn if only non-candidate (baseline) remains
    non_baseline = [c for c in eligible if c.pipeline_role != "baseline"]
    if not non_baseline and eligible:
        result.warnings.append("Only baseline candidates remain eligible.")

    logger.info("Constraint check: passed=%s, issues=%d, warnings=%d",
                result.passed, len(result.issues), len(result.warnings))
    return result
