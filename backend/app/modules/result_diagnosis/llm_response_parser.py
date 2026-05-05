import json
import re
import logging
from typing import Dict, Any
from app.modules.result_diagnosis.exceptions import LLMDiagnosisParseException

logger = logging.getLogger(__name__)


def parse_llm_response(raw_response: str) -> Dict[str, Any]:
    if not raw_response or not raw_response.strip():
        raise LLMDiagnosisParseException("LLM response is empty.")

    text = raw_response.strip()

    # Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code blocks
    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding JSON object boundaries
    brace_start = text.find('{')
    brace_end = text.rfind('}')
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start:brace_end + 1])
        except json.JSONDecodeError:
            pass

    raise LLMDiagnosisParseException("Failed to parse LLM response as valid JSON.")
