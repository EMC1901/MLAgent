import re
import logging
from app.modules.interpretability_analysis.enums import (
    DANGEROUS_PATTERNS,
    FORBIDDEN_LLM_FIELDS,
    VALID_CONFIDENCE_LEVELS,
)
from app.modules.interpretability_analysis.schemas import (
    LLMInterpretabilitySummary,
    LLMValidationResult,
)

logger = logging.getLogger(__name__)


def validate_llm_interpretability_summary(
    summary: LLMInterpretabilitySummary,
    raw_response: str = "",
) -> LLMValidationResult:
    issues: list[str] = []
    warnings_list: list[str] = []

    dangerous_scan_result = _scan_dangerous_patterns(raw_response)
    if dangerous_scan_result:
        issues.append(f"LLM output contains dangerous patterns: {dangerous_scan_result}")

    forbidden_scan_result = _scan_forbidden_fields(summary)
    if forbidden_scan_result:
        issues.append(f"LLM output contains forbidden fields: {forbidden_scan_result}")

    if summary.confidence_level not in VALID_CONFIDENCE_LEVELS:
        issues.append(f"Invalid confidence_level: '{summary.confidence_level}'")

    for pattern in summary.top_material_patterns:
        if hasattr(pattern, "evidence_strength"):
            if pattern.evidence_strength not in ("weak", "moderate", "strong"):
                warnings_list.append(f"Invalid evidence_strength: '{pattern.evidence_strength}'")
        if hasattr(pattern, "caution") and not pattern.caution:
            warnings_list.append(f"Material pattern '{pattern.pattern[:50] if hasattr(pattern, 'pattern') else '?'}' missing caution note.")

    if summary.limitations and any("LLM produced unparseable output" in l for l in summary.limitations):
        warnings_list.append("Parser used fallback - raw LLM response was unparseable.")

    is_valid = len(issues) == 0

    logger.info("LLM interpretability validation: valid=%s issues=%d warnings=%d",
                is_valid, len(issues), len(warnings_list))

    return LLMValidationResult(
        is_valid=is_valid,
        issues=issues,
        warnings=warnings_list,
    )


def _scan_dangerous_patterns(raw: str) -> str:
    if not raw:
        return ""
    raw_lower = raw.lower()
    found = []
    for pattern in DANGEROUS_PATTERNS:
        pattern_lower = pattern.lower()
        count = len(re.findall(re.escape(pattern_lower), raw_lower))
        if count > 0:
            found.append(f"{pattern}(x{count})")
    return ", ".join(found) if found else ""


def _scan_forbidden_fields(summary: LLMInterpretabilitySummary) -> str:
    summary_dict = summary.model_dump() if hasattr(summary, "model_dump") else {}
    summary_str = str(summary_dict).lower()
    found = []
    for field in FORBIDDEN_LLM_FIELDS:
        if field.lower() in summary_str:
            found.append(field)
    return ", ".join(found) if found else ""
