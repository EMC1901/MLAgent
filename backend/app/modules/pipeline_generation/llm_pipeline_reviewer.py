import json
import logging

logger = logging.getLogger(__name__)


class LLMPipelineReviewer:

    def review(self, system_prompt: str, user_message: str) -> dict:
        """Invoke LLM for advisory review. Returns raw response dict.
        Falls back to a safe advisory-completed result when LLM is unavailable."""
        try:
            from app.modules.task_interpretation.llm_client import LLMClient
            client = LLMClient()
            raw_response = client.generate(system_prompt, user_message)
            return {"raw_response": raw_response}
        except Exception as e:
            logger.info("LLM unavailable, using synthetic advisory review: %s", str(e))
            fallback = {
                "review_status": "advisory_unavailable",
                "execution_impact": "non_blocking",
                "risk_level": "unknown",
                "checklist": [],
                "blocking_issues": [],
                "non_blocking_risks": [],
                "resource_warnings": [],
                "future_improvement_suggestions": [
                    "Re-run LLM review after training metrics are available for richer feedback.",
                ],
                "confidence_level": "low",
            }
            return {"raw_response": json.dumps(fallback, ensure_ascii=False)}
