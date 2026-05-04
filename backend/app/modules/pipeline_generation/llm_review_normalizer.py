import logging
from app.modules.pipeline_generation.schemas import (
    LLMAdvisoryReview,
    LLMAdvisoryChecklistItem,
    LLMAdvisoryRisk,
)

logger = logging.getLogger(__name__)

# Mapping of old-style approval phrases → risk level
APPROVAL_TO_RISK = {
    "needs_improvement": "medium",
    "needs review": "medium",
    "conditional": "medium",
    "rejected": "high",
    "not approved": "high",
    "approved": "low",
    "good": "low",
    "excellent": "none",
}

# Mapping of old 0.0–1.0 confidence_score → confidence_level
def _score_to_level(score) -> str:
    try:
        s = float(score)
    except (TypeError, ValueError):
        return "medium"
    if s >= 0.7:
        return "high"
    if s >= 0.3:
        return "medium"
    return "low"


def normalize_llm_review(parsed_data: dict) -> LLMAdvisoryReview:
    """Normalize LLM raw parsed output into a standard LLMAdvisoryReview.
    Handles both standard (new schema) and non-standard (old/approval-style) LLM output.
    """
    notes = []

    # ---- Strip forbidden fields ----
    forbidden = {
        "approval_status", "approved", "rejected", "conditional",
        "needs_improvement", "final_decision", "execution_allowed",
        "ready_for_execution", "modify_pipeline", "recommended_code",
        "python_code",
    }
    raw_summary = {}
    for k in forbidden:
        if k in parsed_data:
            raw_summary[k] = parsed_data.pop(k)
            notes.append(f"LLM returned non-standard field '{k}'. Normalized into advisory format.")

    # ---- Determine review_status ----
    review_status = parsed_data.get("review_status", "advisory_completed")
    if review_status not in ("advisory_completed", "advisory_failed", "advisory_unavailable"):
        review_status = "advisory_completed"
        notes.append(f"Non-standard review_status normalized to 'advisory_completed'.")

    # ---- Determine execution_impact ----
    execution_impact = parsed_data.get("execution_impact", "non_blocking")
    if execution_impact not in ("non_blocking", "potentially_blocking"):
        # If old-style approval was present, still non_blocking because system is authoritative
        execution_impact = "non_blocking"
        notes.append("execution_impact forced to 'non_blocking' (system validator is authoritative).")

    # ---- Determine risk_level ----
    risk_level = parsed_data.get("risk_level", "")
    if risk_level not in ("none", "low", "medium", "high"):
        # Try to infer from old-style overall_assessment
        overall = parsed_data.get("overall_assessment", "")
        if overall:
            raw_summary["overall_assessment"] = overall
        inferred = APPROVAL_TO_RISK.get(str(overall).strip().lower(), "medium")
        # But if LLM said "needs_improvement" with no actual issues, default to low
        if inferred == "medium" and not parsed_data.get("non_blocking_risks"):
            inferred = "low"
        risk_level = inferred
        if overall:
            notes.append(
                f"risk_level inferred from overall_assessment='{overall}' → '{risk_level}'."
            )

    # ---- Determine confidence_level ----
    confidence_level = parsed_data.get("confidence_level", "")
    if confidence_level not in ("low", "medium", "high"):
        # Try old-style numeric confidence_score
        if "confidence_score" in parsed_data:
            confidence_level = _score_to_level(parsed_data.pop("confidence_score"))
            notes.append(f"confidence_score converted to confidence_level='{confidence_level}'.")
        else:
            confidence_level = "medium"

    # ---- Build checklist ----
    checklist = []
    raw_checklist = parsed_data.get("checklist", [])
    if isinstance(raw_checklist, list):
        for item in raw_checklist:
            if isinstance(item, dict):
                status = item.get("status", "pass")
                if status not in ("pass", "warning", "not_applicable"):
                    status = "warning"
                checklist.append(LLMAdvisoryChecklistItem(
                    dimension=item.get("dimension", ""),
                    status=status,
                    comment=item.get("comment", ""),
                ))
    if not checklist:
        notes.append("LLM returned no checklist; review may be incomplete.")

    # ---- Build blocking/non-blocking risks ----
    blocking_issues = []
    non_blocking_risks = []

    for risk_list, target, default_severity in [
        ("blocking_issues", blocking_issues, "high"),
        ("non_blocking_risks", non_blocking_risks, "low"),
    ]:
        raw_risks = parsed_data.get(risk_list, [])
        if isinstance(raw_risks, list):
            for r in raw_risks:
                if isinstance(r, dict):
                    sev = r.get("severity", default_severity)
                    if sev not in ("low", "medium", "high"):
                        sev = default_severity
                    target.append(LLMAdvisoryRisk(
                        category=r.get("category", ""),
                        severity=sev,
                        message=r.get("message", ""),
                        suggested_action=r.get("suggested_action", ""),
                    ))

    # ---- Convert old-style risk_notes / consistency_findings if present ----
    for old_note in parsed_data.get("risk_notes", []):
        if isinstance(old_note, dict):
            non_blocking_risks.append(LLMAdvisoryRisk(
                category="legacy",
                severity=old_note.get("severity", "low"),
                message=old_note.get("description", ""),
                suggested_action="",
            ))
            notes.append("Old-style risk_notes converted to non_blocking_risks.")

    for old_finding in parsed_data.get("consistency_findings", []):
        if isinstance(old_finding, dict):
            non_blocking_risks.append(LLMAdvisoryRisk(
                category=old_finding.get("area", "consistency"),
                severity="low",
                message=old_finding.get("finding", ""),
                suggested_action="",
            ))
            notes.append("Old-style consistency_findings converted to non_blocking_risks.")

    # ---- Resource warnings ----
    resource_warnings = []
    raw_rw = parsed_data.get("resource_warnings", [])
    if isinstance(raw_rw, list):
        resource_warnings = [str(w) for w in raw_rw]

    # ---- Future improvement suggestions ----
    suggestions = []
    raw_sug = parsed_data.get("future_improvement_suggestions", [])
    if isinstance(raw_sug, list):
        suggestions = [str(s) for s in raw_sug]
    # Also absorb old suggested_review_items
    old_items = parsed_data.get("suggested_review_items", [])
    if isinstance(old_items, list):
        for item in old_items:
            suggestions.append(str(item))
        if old_items:
            notes.append("Old-style suggested_review_items merged into future_improvement_suggestions.")

    return LLMAdvisoryReview(
        enabled=True,
        review_status=review_status,
        execution_impact=execution_impact,
        risk_level=risk_level,
        confidence_level=confidence_level,
        checklist=checklist,
        blocking_issues=blocking_issues,
        non_blocking_risks=non_blocking_risks,
        resource_warnings=resource_warnings,
        future_improvement_suggestions=suggestions,
        normalization_notes=notes,
        raw_llm_summary=raw_summary if raw_summary else {},
    )
