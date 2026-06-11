import logging
from typing import Dict, Any
from app.modules.task_interpretation.llm_client import LLMClient
from app.modules.interpretability_analysis.exceptions import LLMInterpretabilitySummaryException

logger = logging.getLogger(__name__)


class LLMInterpretabilitySummarizer:

    def __init__(self):
        self.llm_client = LLMClient()

    def summarize(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        logger.info("Calling LLM for interpretability summarization ...")

        try:
            raw_response = self.llm_client.generate(system_prompt, user_message)
        except Exception as e:
            logger.error("LLM interpretability summary call failed: %s", str(e))
            raise LLMInterpretabilitySummaryException(f"LLM call failed: {str(e)}")

        # Read provider/model AFTER generate() — it calls _resolve_config() internally
        request_info = {
            "provider": self.llm_client.provider,
            "model": self.llm_client.model,
            "system_prompt": system_prompt,
            "user_message": user_message,
        }

        logger.info("LLM interpretability summarization done — provider=%s model=%s",
                     self.llm_client.provider, self.llm_client.model)

        return {
            "request_info": request_info,
            "raw_response": raw_response,
        }
