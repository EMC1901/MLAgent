import logging
from typing import Optional, List, Dict, Any

from app.modules.final_pipeline_selection.schemas import LLMSelectionExplanation

logger = logging.getLogger(__name__)

# Forbidden patterns in LLM output (security scan)
FORBIDDEN_PATTERNS = [
    "import ",
    "def ",
    "class ",
    "eval(",
    "exec(",
    "subprocess",
    "os.system",
    "open(",
    "write(",
    "delete ",
    "remove(",
    "shutil",
    "model.fit",
    "model.predict",
    "Pipeline(",
    "optuna.create_study",
]

# Forbidden field names
FORBIDDEN_FIELDS = [
    "python_code",
    "script",
    "shell_command",
    "sql",
    "change_selection",
    "new_ranking",
    "override_score",
    "modified_metric",
    "selected_pipeline_override",
]


class LLMExplanationValidationResult:
    def __init__(self):
        self.is_valid: bool = True
        self.is_safe: bool = True
        self.schema_valid: bool = True
        self.issues: List[str] = []
        self.warnings: List[str] = []


def validate_llm_selection_explanation(
    explanation: Optional[LLMSelectionExplanation],
    raw_response: str = "",
) -> LLMExplanationValidationResult:
    result = LLMExplanationValidationResult()

    if explanation is None:
        result.is_valid = False
        result.schema_valid = False
        result.issues.append("LLM explanation is None (parse failed).")
        return result

    # Schema validation
    if not explanation.why_selected:
        result.schema_valid = False
        result.issues.append("why_selected is empty.")

    if not explanation.selection_rationale_natural_language:
        result.warnings.append("selection_rationale_natural_language is empty.")

    if explanation.confidence_level not in ("low", "medium", "high"):
        result.warnings.append(f"Invalid confidence_level: {explanation.confidence_level}")

    # Security scan
    _scan_security(explanation, raw_response, result)

    result.is_valid = result.schema_valid and result.is_safe
    if not result.is_valid:
        logger.warning("LLM explanation validation failed: issues=%s", result.issues)

    return result


def _scan_security(
    explanation: LLMSelectionExplanation,
    raw_response: str,
    result: LLMExplanationValidationResult,
):
    # Scan text fields for forbidden code patterns
    text_fields = [
        explanation.why_selected or "",
        explanation.selection_rationale_natural_language or "",
    ]
    text_fields.extend(explanation.human_review_notes or [])
    text_fields.extend(explanation.risk_notes or [])
    for summary in (explanation.candidate_difference_summary or []):
        text_fields.append(summary.summary or "")
        text_fields.append(summary.candidate or "")

    combined_text = " ".join(text_fields).lower()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.lower() in combined_text:
            result.is_safe = False
            result.issues.append(f"Forbidden pattern detected: '{pattern}'")

    # Scan raw response for forbidden field names
    raw_lower = raw_response.lower()
    for field in FORBIDDEN_FIELDS:
        if field.lower() in raw_lower:
            result.is_safe = False
            result.issues.append(f"Forbidden field detected in raw response: '{field}'")

    # Scan for Python code blocks
    if "```python" in raw_lower or "```" in raw_lower:
        result.warnings.append("Raw response contains code fence markers.")


def scan_for_forbidden_content(text: str) -> List[str]:
    """Standalone security scan; returns list of detected forbidden patterns."""
    detections = []
    text_lower = text.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.lower() in text_lower:
            detections.append(pattern)
    return detections
