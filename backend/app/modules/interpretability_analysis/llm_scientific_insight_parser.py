import json
import logging
import re
from typing import Any, Dict, List, Set

from app.modules.interpretability_analysis.schemas import LLMScientificInsightOutput
from app.modules.interpretability_analysis.exceptions import LLMScientificInsightException

logger = logging.getLogger(__name__)


def parse_llm_scientific_insights(
    raw_response: str,
    valid_evidence_ids: List[str],
) -> LLMScientificInsightOutput:
    """Parse the LLM academic-insight JSON without hiding bad references."""
    if not raw_response or not raw_response.strip():
        raise LLMScientificInsightException("LLM scientific insight response is empty.")

    try:
        data = json.loads(_extract_json(raw_response))
        insights = _as_list(data.get("academic_insights"))
        valid_set: Set[str] = set(valid_evidence_ids or [])
        for insight in insights:
            if isinstance(insight, dict):
                refs = _as_list(insight.get("supporting_evidence_ids"))
                invalid = [ref for ref in refs if ref not in valid_set]
                if invalid:
                    logger.warning(
                        "Academic insight '%s' references invalid evidence IDs: %s",
                        insight.get("claim_id", "?"),
                        invalid,
                    )

        return LLMScientificInsightOutput(
            narrative_title=str(data.get("narrative_title", "") or ""),
            executive_summary=str(data.get("executive_summary", "") or ""),
            academic_insights=[i for i in insights if isinstance(i, dict)],
            rejected_claims=[i for i in _as_list(data.get("rejected_claims")) if isinstance(i, dict)],
            missing_evidence=[i for i in _as_list(data.get("missing_evidence")) if isinstance(i, dict)],
            human_review_notes=[str(i) for i in _as_list(data.get("human_review_notes"))],
            limitations_section=[i for i in _as_list(data.get("limitations_section")) if isinstance(i, dict)],
            validation_suggestions=[i for i in _as_list(data.get("validation_suggestions")) if isinstance(i, dict)],
        )
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse LLM scientific insight JSON: %s. Raw: %s...", exc, raw_response[:200])
        return _build_fallback_output(raw_response)
    except Exception as exc:
        logger.error("Unexpected error parsing LLM scientific insights: %s", exc)
        raise LLMScientificInsightException(f"Scientific insight parse failed: {exc}")


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


def _as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _build_fallback_output(raw_response: str) -> LLMScientificInsightOutput:
    return LLMScientificInsightOutput(
        narrative_title="Scientific Interpretability Insight Review",
        executive_summary=(
            "The LLM response could not be parsed as the required JSON schema. "
            "Use the structured ScientificInsightReport and deterministic material "
            "pattern candidates for evidence-grounded review."
        ),
        academic_insights=[],
        rejected_claims=[{
            "claim": raw_response[:300],
            "reason": "LLM output was not parseable as structured JSON.",
            "missing_evidence": ["valid JSON response"],
        }],
        missing_evidence=[{
            "needed_evidence": "parseable structured JSON",
            "why_it_matters": "Claims cannot be audited without structured evidence references.",
        }],
        human_review_notes=["Review the raw LLM response and structured evidence manually."],
        limitations_section=[{
            "category": "parse_error",
            "description": "LLM output was unparseable; no generated academic insight was accepted.",
        }],
        validation_suggestions=[],
    )
