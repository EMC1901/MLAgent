import json
import re
import logging
from typing import Dict, Any
from app.modules.iteration_decision.exceptions import LLMParseFailedException

logger = logging.getLogger(__name__)


def parse_response(raw_response: str) -> Dict[str, Any]:
    if not raw_response or not raw_response.strip():
        raise LLMParseFailedException("LLM response is empty.")

    text = raw_response.strip()

    # Direct JSON parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Extract from markdown code block
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Find JSON object by braces
    brace_start = text.find('{')
    brace_end = text.rfind('}')
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start:brace_end + 1])
        except json.JSONDecodeError:
            pass

    raise LLMParseFailedException("Failed to parse LLM response as valid JSON.")
