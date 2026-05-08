import json
import re
import logging
from app.modules.interpretability_analysis.schemas import LLMInterpretabilitySummary
from app.modules.interpretability_analysis.exceptions import LLMInterpretabilitySummaryException

logger = logging.getLogger(__name__)


def parse_llm_interpretability_summary(raw_response: str) -> LLMInterpretabilitySummary:
    if not raw_response or not raw_response.strip():
        raise LLMInterpretabilitySummaryException("LLM response is empty.")

    try:
        json_str = _extract_json(raw_response)
        data = json.loads(json_str)

        return LLMInterpretabilitySummary(
            top_material_patterns=data.get("top_material_patterns", []),
            feature_groups_interpretation=data.get("feature_groups_interpretation", []),
            domain_hypotheses=data.get("domain_hypotheses", []),
            limitations=data.get("limitations", []),
            human_review_notes=data.get("human_review_notes", []),
            confidence_level=data.get("confidence_level", "medium"),
        )
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse LLM JSON: %s. Raw: %s...", str(e), raw_response[:200])
        return _build_fallback_summary(raw_response)
    except Exception as e:
        logger.error("Unexpected error parsing LLM response: %s", str(e))
        raise LLMInterpretabilitySummaryException(f"Parse failed: {str(e)}")


def _extract_json(raw: str) -> str:
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if match:
        return match.group(1).strip()
    brace_start = raw.find("{")
    brace_end = raw.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        return raw[brace_start:brace_end + 1]
    return raw


def _build_fallback_summary(raw_response: str) -> LLMInterpretabilitySummary:
    logger.warning("Using fallback summary from raw LLM text.")
    return LLMInterpretabilitySummary(
        top_material_patterns=[],
        feature_groups_interpretation=[],
        domain_hypotheses=[],
        limitations=["LLM produced unparseable output; system interpretability results are available."],
        human_review_notes=["Manually review the interpretability results."],
        confidence_level="low",
    )
