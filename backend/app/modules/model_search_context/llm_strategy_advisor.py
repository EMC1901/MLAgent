import logging
from typing import Dict, Any
from app.shared.config.settings import settings
from app.modules.task_interpretation.llm_client import LLMClient
from app.modules.model_search_context.exceptions import LLMCallException

logger = logging.getLogger(__name__)


class LLMStrategyAdvisor:

    def __init__(self):
        self.llm_client = LLMClient()
        # Override with model-context-specific settings (larger prompt needs longer timeout)
        if hasattr(settings, "MODEL_CONTEXT_LLM_TIMEOUT"):
            self.llm_client.timeout = settings.MODEL_CONTEXT_LLM_TIMEOUT
        if hasattr(settings, "MODEL_CONTEXT_LLM_MAX_RETRIES"):
            self.llm_client.max_retries = settings.MODEL_CONTEXT_LLM_MAX_RETRIES
        if hasattr(settings, "MODEL_CONTEXT_LLM_TEMPERATURE"):
            self.llm_client.temperature = settings.MODEL_CONTEXT_LLM_TEMPERATURE

    def generate(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        provider = self.llm_client.provider
        model = self.llm_client.model

        request_info = {
            "provider": provider,
            "model": model,
            "system_prompt": system_prompt,
            "user_message": user_message,
        }

        logger.info(
            "Calling LLM for model search strategy advice: provider=%s model=%s timeout=%ds retries=%d",
            provider, model, self.llm_client.timeout, self.llm_client.max_retries + 1,
        )

        try:
            raw_response = self.llm_client.generate(system_prompt, user_message)
        except Exception as e:
            logger.error("LLM call failed for model search context: %s", str(e))
            raise LLMCallException(f"LLM call failed: {str(e)}")

        return {
            "request_info": request_info,
            "raw_response": raw_response,
        }
