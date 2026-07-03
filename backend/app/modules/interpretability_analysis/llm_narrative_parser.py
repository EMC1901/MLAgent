import json
import re
import logging
from typing import Dict, Any, List, Set

from app.modules.interpretability_analysis.schemas import LLMNarrativeOutput
from app.modules.interpretability_analysis.exceptions import LLMNarrativeException

logger = logging.getLogger(__name__)


def parse_llm_narrative(
    raw_response: str,
    valid_evidence_ids: List[str],
) -> LLMNarrativeOutput:
    """Parse LLM narrative output and validate evidence references.

    Args:
        raw_response: Raw LLM response string.
        valid_evidence_ids: List of all valid evidence IDs from the evidence normalizer.

    Returns:
        LLMNarrativeOutput with parsed and validated content.

    Raises:
        LLMNarrativeException: If the response is empty or fundamentally unparseable.
    """
    if not raw_response or not raw_response.strip():
        raise LLMNarrativeException("LLM narrative response is empty.")

    try:
        json_str = _extract_json(raw_response)
        data = json.loads(json_str)

        insights = data.get("insights", [])
        # Retain ALL evidence references — valid or not.
        # The VALIDATOR (llm_narrative_validator) is responsible for checking
        # whether every insight has at least one valid reference and for flagging
        # invalid ones as issues. The parser should NOT silently drop invalid refs
        # because that would hide evidence-grounding failures.
        valid_set: Set[str] = set(valid_evidence_ids)
        for insight in insights:
            if isinstance(insight, dict):
                refs = insight.get("evidence_references", [])
                invalid = [r for r in refs if r not in valid_set]
                if invalid:
                    logger.warning(
                        "Insight '%s' references invalid evidence IDs (preserved for validation): %s",
                        insight.get("hypothesis_id", "?"), invalid)

        return LLMNarrativeOutput(
            narrative_title=data.get("narrative_title", ""),
            executive_summary=data.get("executive_summary", ""),
            insights=insights,
            limitations_section=data.get("limitations_section", []),
            validation_suggestions=data.get("validation_suggestions", []),
        )
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse LLM narrative JSON: %s. Raw: %s...",
                       str(e), raw_response[:200])
        return _build_fallback_narrative(raw_response, valid_evidence_ids)
    except Exception as e:
        logger.error("Unexpected error parsing LLM narrative: %s", str(e))
        raise LLMNarrativeException(f"Narrative parse failed: {str(e)}")


def _extract_json(raw: str) -> str:
    """Extract JSON from LLM response, handling code fences and raw braces."""
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if match:
        return match.group(1).strip()
    brace_start = raw.find("{")
    brace_end = raw.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        return raw[brace_start:brace_end + 1]
    return raw


def _build_fallback_narrative(
    raw_response: str,
    valid_evidence_ids: List[str],
) -> LLMNarrativeOutput:
    """Build a fallback narrative when JSON parsing fails."""
    logger.warning("Using fallback narrative from raw LLM text.")
    return LLMNarrativeOutput(
        narrative_title="Interpretability Analysis Narrative",
        executive_summary=(
            "The LLM produced output that could not be parsed as structured JSON. "
            "Please review the raw response and the structured Scientific Insight Report "
            "for details."
        ),
        insights=[],
        limitations_section=[{
            "category": "parse_error",
            "description": "LLM output was unparseable as JSON; the structured "
                           "ScientificInsightReport contains the raw evidence.",
        }],
        validation_suggestions=[],
    )
