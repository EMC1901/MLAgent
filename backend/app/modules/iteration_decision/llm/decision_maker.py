import logging
import sys
import time
from typing import Dict, Any
from app.modules.task_interpretation.llm_client import LLMClient
from app.modules.iteration_decision.exceptions import LLMCallFailedException

logger = logging.getLogger(__name__)


def _diag(msg, *args):
    formatted = msg % args if args else msg
    print(f"DIAG     [id-llm] {formatted}", file=sys.stderr, flush=True)


class LLMDecisionMaker:

    def __init__(self):
        self.llm_client = LLMClient()
        self.llm_client.timeout = 480

    def decide(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        provider = self.llm_client.provider
        model = self.llm_client.model
        prompt_len = len(user_message)
        _diag("decide: provider=%s model=%s timeout=%ds prompt_chars=%d",
              provider, model, self.llm_client.timeout, prompt_len)
        logger.info("Calling LLM for iteration decision — provider=%s model=%s prompt_chars=%d",
                     provider, model, prompt_len)

        t0 = time.time()
        try:
            raw_response = self.llm_client.generate(system_prompt, user_message)
            dur = time.time() - t0
            resp_len = len(raw_response) if isinstance(raw_response, str) else 0
            _diag("decide: SUCCESS in %.1fs — response_chars=%d", dur, resp_len)
            logger.info("LLM response received in %.1fs — %d chars", dur, resp_len)
        except Exception as e:
            _diag("decide: FAILED after %.1fs — %s", time.time() - t0, str(e))
            logger.error("LLM iteration decision call failed after %.1fs: %s",
                         time.time() - t0, str(e))
            raise LLMCallFailedException(f"LLM call failed: {str(e)}")

        return {
            "provider": provider,
            "model": model,
            "raw_response": raw_response,
        }
