import json
import re
from typing import Dict, Any
from app.modules.workflow_planning.exceptions import WorkflowPlanParseException


def parse_llm_response(raw_text: str) -> Dict[str, Any]:
    if not raw_text or not raw_text.strip():
        raise WorkflowPlanParseException("LLM returned empty response.")

    cleaned = raw_text.strip()

    code_fence_pattern = r"^```(?:json)?\s*\n(.*?)\n```\s*$"
    match = re.search(code_fence_pattern, cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise WorkflowPlanParseException(
            f"Failed to parse LLM output as JSON: {str(e)}. "
            f"Raw text (first 500 chars): {raw_text[:500]}"
        )
