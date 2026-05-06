import json
import re
import logging
from typing import Dict, Any
from app.modules.workflow_refinement.exceptions import LLMWorkflowRefinementParseException

logger = logging.getLogger(__name__)


def parse_llm_response(raw_response: str) -> Dict[str, Any]:
    """Parse the LLM raw response into a structured dict."""
    if not raw_response or not raw_response.strip():
        raise LLMWorkflowRefinementParseException("LLM returned empty response.")

    text = raw_response.strip()

    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    text_clean = text
    text_clean = re.sub(r'```(?:json)?\s*|\s*```', '', text_clean)
    try:
        return json.loads(text_clean)
    except json.JSONDecodeError as e:
        raise LLMWorkflowRefinementParseException(
            f"Failed to parse LLM response as JSON: {str(e)[:200]}"
        )
