import json
import logging
from typing import Dict, Any, Optional

from app.modules.final_output.schemas import LLMReportOutput

logger = logging.getLogger(__name__)


def parse_llm_report(raw_response: str) -> Optional[LLMReportOutput]:
    try:
        data = _extract_json(raw_response)
        if data is None:
            logger.error("Failed to extract JSON from LLM report response")
            return None

        report = LLMReportOutput(
            executive_summary=str(data.get("executive_summary", "")),
            task_overview=str(data.get("task_overview", "")),
            dataset_summary=str(data.get("dataset_summary", "")),
            workflow_summary=str(data.get("workflow_summary", "")),
            feature_engineering_summary=str(data.get("feature_engineering_summary", "")),
            model_search_summary=str(data.get("model_search_summary", "")),
            final_model_summary=str(data.get("final_model_summary", "")),
            metric_summary=str(data.get("metric_summary", "")),
            interpretability_summary=str(data.get("interpretability_summary", "")),
            material_insight_summary=str(data.get("material_insight_summary", "")),
            limitations_and_risks=str(data.get("limitations_and_risks", "")),
            reproducibility_notes=str(data.get("reproducibility_notes", "")),
            artifact_summary=str(data.get("artifact_summary", "")),
            next_steps=str(data.get("next_steps", "")),
            confidence_level=_normalize_confidence(data.get("confidence_level", "medium")),
        )

        logger.info("Successfully parsed LLM report")
        return report

    except Exception as e:
        logger.error("Error parsing LLM report: %s", str(e))
        return None


def _extract_json(raw: str) -> Optional[Dict[str, Any]]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

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
    return "medium"
