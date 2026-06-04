import re
import logging
from app.modules.interpretability_analysis.enums import (
    DANGEROUS_PATTERNS_LITERAL,
    DANGEROUS_PATTERNS_REGEX,
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

    # Literal substrings (already specific enough)
    for pattern in DANGEROUS_PATTERNS_LITERAL:
        pattern_lower = pattern.lower()
        count = len(re.findall(re.escape(pattern_lower), raw_lower))
        if count > 0:
            found.append(f"{pattern}(x{count})")

    # Regex patterns (word-boundary-aware to avoid false positives)
    for regex, label in DANGEROUS_PATTERNS_REGEX:
        count = len(re.findall(regex, raw_lower))
        if count > 0:
            found.append(f"{label}(x{count})")

    return ", ".join(found) if found else ""


def _scan_forbidden_fields(summary: LLMInterpretabilitySummary) -> str:
    """Check if any top-level keys in the LLM output match forbidden field names.

    Only checks actual JSON keys, not arbitrary substrings in values,
    to avoid false positives (e.g. 'description' containing 'script').
    """
    summary_dict = summary.model_dump() if hasattr(summary, "model_dump") else {}
    forbidden_set = {f.lower() for f in FORBIDDEN_LLM_FIELDS}
    found = []
    _collect_matching_keys(summary_dict, forbidden_set, found)
    return ", ".join(sorted(set(found))) if found else ""


def _collect_matching_keys(obj, forbidden_set: set, found: list, prefix: str = ""):
    """Recursively collect keys that match forbidden field names."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if key.lower() in forbidden_set:
                found.append(full_key)
            if isinstance(value, (dict, list)):
                _collect_matching_keys(value, forbidden_set, found, full_key)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, (dict, list)):
                _collect_matching_keys(item, forbidden_set, found, f"{prefix}[{i}]")
