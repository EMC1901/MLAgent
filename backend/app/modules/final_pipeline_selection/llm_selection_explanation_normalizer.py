import logging
from typing import Optional

from app.modules.final_pipeline_selection.schemas import LLMSelectionExplanation, CandidateDifferenceSummary
from app.modules.final_pipeline_selection.enums import LLMConfidenceLevel

logger = logging.getLogger(__name__)


def normalize_llm_selection_explanation(
    explanation: Optional[LLMSelectionExplanation],
) -> Optional[LLMSelectionExplanation]:
    """Normalize and sanitize LLM explanation output."""
    if explanation is None:
        return None

    # Trim whitespace in string fields
    explanation.why_selected = (explanation.why_selected or "").strip()
    explanation.selection_rationale_natural_language = (
        explanation.selection_rationale_natural_language or ""
    ).strip()

    # Normalize confidence level
    explanation.confidence_level = _normalize_confidence(explanation.confidence_level)

    # Clean human review notes
    explanation.human_review_notes = [
        note.strip() for note in (explanation.human_review_notes or []) if note and note.strip()
    ]

    # Clean risk notes
    explanation.risk_notes = [
        note.strip() for note in (explanation.risk_notes or []) if note and note.strip()
    ]

    # Clean candidate difference summaries
    cleaned_summaries = []
    for item in (explanation.candidate_difference_summary or []):
        candidate = (item.candidate or "").strip()
        summary = (item.summary or "").strip()
        if candidate or summary:
            cleaned_summaries.append(
                CandidateDifferenceSummary(candidate=candidate, summary=summary)
            )
    explanation.candidate_difference_summary = cleaned_summaries

    logger.info("Normalized LLM selection explanation")
    return explanation


def _normalize_confidence(level: str) -> str:
    level = (level or "").lower().strip()
    if level in ("low", "medium", "high"):
        return level
    return LLMConfidenceLevel.MEDIUM
