import logging
from typing import Optional, List

from app.modules.final_output.schemas import LLMReportOutput, LLMReportValidationResult
from app.modules.final_output.enums import FORBIDDEN_PATTERNS, FORBIDDEN_LLM_FIELDS

logger = logging.getLogger(__name__)


def validate_llm_report(
    report: Optional[LLMReportOutput],
    raw_response: str = "",
) -> LLMReportValidationResult:
    result = LLMReportValidationResult()

    if report is None:
        result.is_valid = False
        result.schema_valid = False
        result.issues.append("LLM report is None (parse failed).")
        return result

    # Schema validation
    if not report.executive_summary:
        result.schema_valid = False
        result.issues.append("executive_summary is empty.")

    if report.confidence_level not in ("low", "medium", "high"):
        result.warnings.append(f"Invalid confidence_level: {report.confidence_level}")

    # Security scan
    _scan_security(report, raw_response, result)

    result.is_valid = result.schema_valid and result.is_safe
    if not result.is_valid:
        logger.warning("LLM report validation failed: issues=%s", result.issues)

    return result


def _pattern_matches(text: str, pattern: str) -> bool:
    """Check if pattern appears as a meaningful token in text.

    Uses word-boundary logic: a match is valid only when the pattern
    is not preceded by an alphanumeric character (avoids 'import'
    matching inside 'important'). Patterns ending in a non-alpha char
    (space, paren, dot) skip the trailing boundary check.
    """
    text_lower = text.lower()
    pattern_lower = pattern.lower()
    idx = 0
    while True:
        idx = text_lower.find(pattern_lower, idx)
        if idx == -1:
            return False
        # Must not be preceded by an alphanumeric char (word boundary before)
        if idx > 0 and text_lower[idx - 1].isalnum():
            idx += 1
            continue
        # If pattern ends with a non-alpha character (space, (, ., etc.),
        # skip the after-boundary check — the trailing char itself acts as boundary
        needs_after_check = pattern_lower[-1].isalpha()
        if needs_after_check:
            after_pos = idx + len(pattern_lower)
            if after_pos < len(text_lower) and text_lower[after_pos].isalpha():
                idx += 1
                continue
        return True


def _scan_security(
    report: LLMReportOutput,
    raw_response: str,
    result: LLMReportValidationResult,
):
    text_fields = [
        report.executive_summary or "",
        report.task_overview or "",
        report.dataset_summary or "",
        report.workflow_summary or "",
        report.feature_engineering_summary or "",
        report.model_search_summary or "",
        report.final_model_summary or "",
        report.metric_summary or "",
        report.interpretability_summary or "",
        report.material_insight_summary or "",
        report.limitations_and_risks or "",
        report.reproducibility_notes or "",
        report.artifact_summary or "",
        report.next_steps or "",
    ]

    combined_text = " ".join(text_fields).lower()
    for pattern in FORBIDDEN_PATTERNS:
        # Use word-boundary-aware matching to avoid false positives
        # e.g. "import " should not match "important"
        if _pattern_matches(combined_text, pattern.lower()):
            result.is_safe = False
            result.issues.append(f"Forbidden pattern detected: '{pattern}'")

    raw_lower = raw_response.lower()
    for field in FORBIDDEN_LLM_FIELDS:
        # Match as JSON key: "field_name" (with surrounding quotes)
        # This avoids matching substrings in natural language text
        quoted = f'"{field.lower()}"'
        if quoted in raw_lower:
            result.is_safe = False
            result.issues.append(f"Forbidden field detected in raw response: '{field}'")

    if "```python" in raw_lower or "```" in raw_lower:
        result.warnings.append("Raw response contains code fence markers.")
