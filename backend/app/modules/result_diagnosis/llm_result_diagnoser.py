import logging
from typing import Dict, Any
from app.modules.task_interpretation.llm_client import LLMClient
from app.modules.result_diagnosis.exceptions import LLMDiagnosisCallException

logger = logging.getLogger(__name__)


class LLMResultDiagnoser:

    def __init__(self):
        self.llm_client = LLMClient()

    def diagnose(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        provider = self.llm_client.provider
        model = self.llm_client.model

        request_info = {
            "provider": provider,
            "model": model,
            "system_prompt": system_prompt,
            "user_message": user_message,
        }

        logger.info("Calling LLM for result diagnosis: provider=%s model=%s", provider, model)

        try:
            raw_response = self.llm_client.generate(system_prompt, user_message)
        except Exception as e:
            logger.error("LLM result diagnosis call failed: %s", str(e))
            raise LLMDiagnosisCallException(f"LLM call failed: {str(e)}")

        return {
            "request_info": request_info,
            "raw_response": raw_response,
        }
