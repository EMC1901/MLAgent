import copy
import logging
import re
from typing import Any, Dict, List, Set, Tuple

from app.modules.interpretability_analysis.schemas import LLMScientificInsightOutput
from app.modules.interpretability_analysis.enums import (
    DANGEROUS_PATTERNS_LITERAL,
    DANGEROUS_PATTERNS_REGEX,
    FORBIDDEN_LLM_FIELDS,
)

logger = logging.getLogger(__name__)

VALID_ACADEMIC_CLAIM_TYPES = {
    "model_observation",
    "candidate_hypothesis",
    "design_rule",
    "mechanism_hypothesis",
    "applicability_boundary",
    "validated_conclusion",
}

VALID_VALIDATION_STATUSES = {
    "model_supported_only",
    "statistically_supported",
    "externally_validated",
    "experimentally_validated",
    "dft_or_simulation_validated",
    "insufficient_evidence",
}

VALIDATED_STATUSES = {
    "statistically_supported",
    "externally_validated",
    "experimentally_validated",
    "dft_or_simulation_validated",
}

MODEL_SUPPORTED_CLAIM_TYPES = {
    "model_observation",
    "candidate_hypothesis",
    "design_rule",
    "mechanism_hypothesis",
    "applicability_boundary",
}

CAUSAL_WORD_RE = re.compile(
    r"\b(causes?|caused|causing|determines?|determined|controls?|controlled|drives?|drove|driven|leads?\s+to|results?\s+in)\b",
    re.IGNORECASE,
)

# More targeted replacements keep useful LLM claims while removing unsupported
# causal language. This is intentionally conservative: it weakens claims, never
# strengthens them.
CAUSAL_REPLACEMENTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bdriven\s+by\b", re.IGNORECASE), "associated with"),
    (re.compile(r"\bdrives?\b", re.IGNORECASE), "is associated with"),
    (re.compile(r"\bdrove\b", re.IGNORECASE), "was associated with"),
    (re.compile(r"\bleads?\s+to\b", re.IGNORECASE), "is associated with"),
    (re.compile(r"\bresults?\s+in\b", re.IGNORECASE), "is associated with"),
    (re.compile(r"\bcauses?\b", re.IGNORECASE), "is associated with"),
    (re.compile(r"\bcaused\s+by\b", re.IGNORECASE), "associated with"),
    (re.compile(r"\bcausing\b", re.IGNORECASE), "associated with"),
    (re.compile(r"\bdetermines?\b", re.IGNORECASE), "is associated with"),
    (re.compile(r"\bdetermined\s+by\b", re.IGNORECASE), "associated with"),
    (re.compile(r"\bcontrols?\b", re.IGNORECASE), "is associated with"),
    (re.compile(r"\bcontrolled\s+by\b", re.IGNORECASE), "associated with"),
]

IMPORTANCE_RESTATEMENT_RE = re.compile(
    r"\b(feature|descriptor|variable)\b.{0,60}\b(important|importance|ranked|top[-\s]?ranked)\b",
    re.IGNORECASE,
)


def validate_llm_scientific_insights(
    output: LLMScientificInsightOutput,
    raw_response: str,
    valid_evidence_ids: Set[str],
) -> Dict[str, Any]:
    """Validate, repair, downgrade, and filter LLM academic insights.

    Global safety/schema problems still invalidate the whole response. Problems
    local to one insight no longer discard the whole LLM result: usable claims
    are retained after conservative repair/downgrade, and unusable claims are
    moved to rejected_claims with an audit reason.
    """
    issues: List[str] = []
    warnings: List[str] = []
    repaired: List[str] = []
    rejected_claims: List[Dict[str, Any]] = list(output.rejected_claims or [])
    accepted_insights: List[Dict[str, Any]] = []

    dangerous = _scan_dangerous_patterns(raw_response)
    if dangerous:
        issues.append(f"LLM scientific insight output contains dangerous patterns: {dangerous}")

    forbidden = _scan_forbidden_fields(output)
    if forbidden:
        issues.append(f"LLM scientific insight output contains forbidden fields: {forbidden}")

    # Do not try to salvage output that trips global safety guards.
    if issues:
        output.academic_insights = []
        logger.info(
            "LLM scientific insight validation: valid=False issues=%d warnings=%d accepted=0 rejected=%d repaired=0",
            len(issues),
            len(warnings),
            len(rejected_claims),
        )
        return {
            "is_valid": False,
            "issues": issues,
            "warnings": warnings,
            "accepted_insights": [],
            "rejected_claims": rejected_claims,
            "repaired_claim_ids": repaired,
        }

    for index, raw_insight in enumerate(output.academic_insights or []):
        insight = copy.deepcopy(raw_insight)
        claim_id = str(insight.get("claim_id") or f"insight_{index + 1}")
        insight["claim_id"] = claim_id
        claim = str(insight.get("claim") or "")
        claim_type = str(insight.get("claim_type") or "")
        validation_status = str(insight.get("validation_status") or "")
        refs = [str(ref) for ref in _as_list(insight.get("supporting_evidence_ids")) if ref]
        local_warnings: List[str] = []

        if not claim.strip():
            _reject(rejected_claims, insight, "empty claim", ["non-empty claim text"])
            continue

        if claim_type not in VALID_ACADEMIC_CLAIM_TYPES:
            local_warnings.append(f"invalid claim_type '{claim_type}' downgraded to candidate_hypothesis")
            insight["claim_type"] = "candidate_hypothesis"
            claim_type = "candidate_hypothesis"
            repaired.append(claim_id)

        if validation_status not in VALID_VALIDATION_STATUSES:
            local_warnings.append(f"invalid validation_status '{validation_status}' downgraded to model_supported_only")
            insight["validation_status"] = "model_supported_only"
            validation_status = "model_supported_only"
            repaired.append(claim_id)

        valid_refs = [ref for ref in refs if ref in valid_evidence_ids]
        invalid_refs = [ref for ref in refs if ref not in valid_evidence_ids]
        if invalid_refs:
            local_warnings.append(f"invalid evidence IDs removed: {invalid_refs}")
            repaired.append(claim_id)
        if not valid_refs:
            _reject(
                rejected_claims,
                insight,
                "no valid supporting evidence IDs",
                ["at least one supporting_evidence_id present in evidence_index"],
            )
            continue
        insight["supporting_evidence_ids"] = valid_refs

        evidence_strength = str(insight.get("evidence_strength") or "").lower()
        if evidence_strength not in {"weak", "moderate", "strong"}:
            insight["evidence_strength"] = "moderate"
            local_warnings.append("nonstandard evidence_strength normalized to moderate")
            repaired.append(claim_id)

        confidence = str(insight.get("confidence") or "").lower()
        if confidence not in {"low", "medium", "high"}:
            insight["confidence"] = "medium"
            local_warnings.append("nonstandard confidence normalized to medium")
            repaired.append(claim_id)

        if claim_type == "validated_conclusion" and validation_status not in VALIDATED_STATUSES:
            insight["claim_type"] = "candidate_hypothesis"
            insight["validation_status"] = "model_supported_only"
            insight["allowed_wording"] = "model-supported candidate hypothesis"
            _append_risk(
                insight,
                "Claim was downgraded because no independent validation evidence was provided.",
            )
            local_warnings.append("validated_conclusion downgraded to candidate_hypothesis")
            repaired.append(claim_id)
            claim_type = "candidate_hypothesis"
            validation_status = "model_supported_only"

        if validation_status == "insufficient_evidence" and claim_type not in {
            "model_observation",
            "candidate_hypothesis",
            "applicability_boundary",
        }:
            insight["claim_type"] = "candidate_hypothesis"
            insight["allowed_wording"] = "insufficiently supported candidate hypothesis"
            _append_risk(insight, "Evidence was marked insufficient; treat this as a weak lead only.")
            local_warnings.append(f"{claim_type} downgraded because validation_status is insufficient_evidence")
            repaired.append(claim_id)

        claim = str(insight.get("claim") or "")
        validation_status = str(insight.get("validation_status") or "")
        if CAUSAL_WORD_RE.search(claim) and validation_status not in VALIDATED_STATUSES:
            sanitized_claim = _sanitize_causal_wording(claim)
            if sanitized_claim != claim:
                insight["claim"] = sanitized_claim
                insight["allowed_wording"] = "model-supported association, not causal conclusion"
                _append_risk(
                    insight,
                    "Original LLM wording used causal language; wording was weakened because no independent validation was provided.",
                )
                local_warnings.append("unsupported causal wording was weakened")
                repaired.append(claim_id)
            else:
                _reject(
                    rejected_claims,
                    insight,
                    "unsupported causal wording could not be safely repaired",
                    ["independent validation evidence or non-causal wording"],
                )
                continue

        if IMPORTANCE_RESTATEMENT_RE.search(str(insight.get("claim") or "")) and not str(insight.get("material_meaning") or "").strip():
            _reject(
                rejected_claims,
                insight,
                "feature-importance restatement without materials-science translation",
                ["material_meaning that translates model evidence into a material concept"],
            )
            continue

        if not str(insight.get("material_meaning") or "").strip():
            insight["material_meaning"] = "Model-supported association; materials interpretation requires human/domain review."
            local_warnings.append("missing material_meaning filled with conservative review note")
            repaired.append(claim_id)

        if not _as_list(insight.get("evidence_chain")):
            insight["evidence_chain"] = [{
                "step": "model_evidence",
                "summary": "Claim retained because it cites valid evidence IDs; detailed chain was not supplied by the LLM.",
            }]
            local_warnings.append("missing evidence_chain filled conservatively")
            repaired.append(claim_id)

        if not str(insight.get("falsifiable_prediction") or "").strip():
            insight["falsifiable_prediction"] = "Evaluate this association on an independent holdout, external dataset, or targeted simulation/experiment."
            local_warnings.append("missing falsifiable_prediction filled conservatively")
            repaired.append(claim_id)

        if not _as_list(insight.get("suggested_validation")):
            insight["suggested_validation"] = [
                "external holdout test",
                "bootstrap or subgroup contrast",
                "domain-specific simulation or experiment if actionable",
            ]
            local_warnings.append("missing suggested_validation filled conservatively")
            repaired.append(claim_id)

        for warning in local_warnings:
            warnings.append(f"Insight '{claim_id}': {warning}")

        accepted_insights.append(insight)

    output.academic_insights = accepted_insights
    output.rejected_claims = rejected_claims

    for rejected in output.rejected_claims:
        if isinstance(rejected, dict) and not rejected.get("reason"):
            warnings.append("A rejected claim is missing a reason.")

    if not accepted_insights:
        issues.append("No acceptable academic insights remained after validation and repair.")

    is_valid = len(issues) == 0
    logger.info(
        "LLM scientific insight validation: valid=%s issues=%d warnings=%d accepted=%d rejected=%d repaired=%d",
        is_valid,
        len(issues),
        len(warnings),
        len(accepted_insights),
        len(rejected_claims),
        len(set(repaired)),
    )
    return {
        "is_valid": is_valid,
        "issues": issues,
        "warnings": warnings,
        "accepted_insights": accepted_insights,
        "rejected_claims": rejected_claims,
        "repaired_claim_ids": sorted(set(repaired)),
    }


def _reject(rejected_claims: List[Dict[str, Any]], insight: Dict[str, Any], reason: str, missing_evidence: List[str]) -> None:
    rejected_claims.append({
        "claim_id": insight.get("claim_id", ""),
        "claim": insight.get("claim", ""),
        "reason": reason,
        "missing_evidence": missing_evidence,
        "supporting_evidence_ids": _as_list(insight.get("supporting_evidence_ids")),
    })


def _append_risk(insight: Dict[str, Any], risk: str) -> None:
    risks = _as_list(insight.get("counterexamples_or_risks"))
    if risk not in risks:
        risks.append(risk)
    insight["counterexamples_or_risks"] = risks


def _sanitize_causal_wording(text: str) -> str:
    sanitized = text
    for pattern, replacement in CAUSAL_REPLACEMENTS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def _scan_dangerous_patterns(raw: str) -> str:
    if not raw:
        return ""
    raw_lower = raw.lower()
    found = []
    for pattern in DANGEROUS_PATTERNS_LITERAL:
        count = len(re.findall(re.escape(pattern.lower()), raw_lower))
        if count:
            found.append(f"{pattern}(x{count})")
    for regex, label in DANGEROUS_PATTERNS_REGEX:
        count = len(re.findall(regex, raw_lower))
        if count:
            found.append(f"{label}(x{count})")
    return ", ".join(found)


def _scan_forbidden_fields(output: LLMScientificInsightOutput) -> str:
    output_dict = output.model_dump() if hasattr(output, "model_dump") else {}
    forbidden_set = {field.lower() for field in FORBIDDEN_LLM_FIELDS}
    found: List[str] = []
    _collect_matching_keys(output_dict, forbidden_set, found)
    return ", ".join(sorted(set(found)))


def _collect_matching_keys(obj: Any, forbidden_set: Set[str], found: List[str], prefix: str = "") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else str(key)
            if str(key).lower() in forbidden_set:
                found.append(full_key)
            if isinstance(value, (dict, list)):
                _collect_matching_keys(value, forbidden_set, found, full_key)
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            if isinstance(item, (dict, list)):
                _collect_matching_keys(item, forbidden_set, found, f"{prefix}[{index}]")


def _as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]