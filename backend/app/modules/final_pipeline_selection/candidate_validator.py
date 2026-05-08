import logging
from typing import List

from app.modules.final_pipeline_selection.schemas import CandidateSelectionItem
from app.modules.final_pipeline_selection.enums import CandidateStatus

logger = logging.getLogger(__name__)


def validate_candidates(
    candidates: List[CandidateSelectionItem],
    require_model_artifact: bool = True,
    require_prediction_artifact: bool = True,
) -> List[CandidateSelectionItem]:
    validated: List[CandidateSelectionItem] = []

    for c in candidates:
        issues: list = []

        if not c.trial_id:
            issues.append("Missing trial_id")
        if not c.model_id:
            issues.append("Missing model_id")
        if c.primary_metric_value is None:
            issues.append("Missing primary_metric_value")

        if issues:
            c.candidate_status = CandidateStatus.REJECTED
            c.rejection_reason = "; ".join(issues)
            logger.warning(
                "Candidate %s (model=%s) rejected: %s",
                c.candidate_id or "?",
                c.model_id or "?",
                c.rejection_reason,
            )
        else:
            c.candidate_status = CandidateStatus.ELIGIBLE

        validated.append(c)

    eligible = [c for c in validated if c.candidate_status == CandidateStatus.ELIGIBLE]
    rejected = [c for c in validated if c.candidate_status == CandidateStatus.REJECTED]

    logger.info(
        "Candidate validation: %d total, %d eligible, %d rejected",
        len(validated), len(eligible), len(rejected),
    )

    if rejected:
        for r in rejected:
            logger.info(
                "  Rejected: candidate_id=%s model_id=%s reason=%s",
                r.candidate_id, r.model_id, r.rejection_reason,
            )

    return validated
