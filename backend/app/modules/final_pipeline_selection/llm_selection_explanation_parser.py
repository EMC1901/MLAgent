import json
import logging
from typing import Dict, Any, Optional

from app.modules.final_pipeline_selection.schemas import LLMSelectionExplanation, CandidateDifferenceSummary
from app.modules.final_pipeline_selection.enums import LLMConfidenceLevel

logger = logging.getLogger(__name__)


def parse_llm_selection_explanation(raw_response: str) -> Optional[LLMSelectionExplanation]:
    """Parse JSON from LLM raw response. Returns None if unparseable."""
    try:
        # Try direct JSON parse
        data = _extract_json(raw_response)
        if data is None:
            logger.error("Failed to extract JSON from LLM response")
            return None

        explanation = LLMSelectionExplanation(
            why_selected=str(data.get("why_selected", "")),
            candidate_difference_summary=[
                CandidateDifferenceSummary(
                    candidate=str(item.get("candidate", "")),
                    summary=str(item.get("summary", "")),
                )
                for item in data.get("candidate_difference_summary", [])
            ],
            selection_rationale_natural_language=str(
                data.get("selection_rationale_natural_language", "")
            ),
            human_review_notes=[
                str(note) for note in data.get("human_review_notes", [])
            ],
            risk_notes=[str(note) for note in data.get("risk_notes", [])],
            confidence_level=_normalize_confidence(data.get("confidence_level", "medium")),
        )

        logger.info("Successfully parsed LLM selection explanation")
        return explanation

    except Exception as e:
        logger.error("Error parsing LLM selection explanation: %s", str(e))
        return None


def _extract_json(raw: str) -> Optional[Dict[str, Any]]:
    """Extract JSON object from raw text, handling markdown fences."""
    text = raw.strip()
    # Remove markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first fence line
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        # Remove last fence line
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON between braces
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


def _normalize_confidence(level: str) -> str:
    level = level.lower().strip()
    if level in ("low", "medium", "high"):
        return level
    return LLMConfidenceLevel.MEDIUM
