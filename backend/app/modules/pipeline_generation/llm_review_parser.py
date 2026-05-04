import json
import logging
from app.modules.pipeline_generation.schemas import (
    LLMAdvisoryReview,
    LLMAdvisoryChecklistItem,
    LLMAdvisoryRisk,
)
from app.modules.pipeline_generation.exceptions import LLMPipelineReviewException

logger = logging.getLogger(__name__)


def parse_llm_review_response(raw_response: str) -> dict:
    """Parse LLM raw response into a dict. Returns the raw parsed JSON
    (may be non-standard). Downstream Normalizer handles standardization."""
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError:
        # Try to extract JSON from a possibly noisy/markdown-wrapped response
        start = raw_response.find("{")
        end = raw_response.rfind("}")
        if start != -1 and end != -1:
            try:
                data = json.loads(raw_response[start:end + 1])
            except json.JSONDecodeError:
                raise LLMPipelineReviewException(
                    "Failed to parse LLM pipeline review response as JSON."
                )
        else:
            raise LLMPipelineReviewException(
                "Failed to parse LLM pipeline review response as JSON."
            )
    return data
