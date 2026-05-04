import json
import logging
import re
from typing import Dict, Any
from pydantic import ValidationError
from app.modules.model_search.schemas import LLMModelSearchSuggestion
from app.modules.model_search.exceptions import LLMModelSearchParseException

logger = logging.getLogger(__name__)


def parse_llm_model_search_response(raw_response: str) -> dict:
    """Parse LLM raw response into validated LLMModelSearchSuggestion dict."""
    logger.info("Parsing LLM model search response.")

    json_text = raw_response.strip()

    # Strip markdown code blocks if present
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", json_text)
    if m:
        json_text = m.group(1).strip()

    # Try to extract JSON object
    if not json_text.startswith("{"):
        m = re.search(r"\{[\s\S]*\}", json_text)
        if m:
            json_text = m.group(0)
        else:
            raise LLMModelSearchParseException(
                "Could not locate JSON object in LLM model search response."
            )

    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.error("Failed to decode LLM model search JSON: %s", str(e))
        raise LLMModelSearchParseException(
            f"LLM model search response is not valid JSON: {str(e)}"
        )

    try:
        validated = LLMModelSearchSuggestion(**parsed)
        return validated.model_dump()
    except ValidationError as e:
        logger.warning("LLM model search response schema validation warning: %s", str(e))
        # Return best-effort parsed result with defaults
        defaults = LLMModelSearchSuggestion().model_dump()
        defaults.update({k: v for k, v in parsed.items() if k in defaults})
        return defaults
