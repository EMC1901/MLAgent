import httpx
import logging
import time
from typing import List, Dict, Any
from app.shared.config.settings import settings
from app.modules.task_interpretation.exceptions import LLMCallException

logger = logging.getLogger(__name__)


class LLMClient:

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL.rstrip("/")
        self.timeout = settings.LLM_TIMEOUT
        self.max_retries = settings.LLM_MAX_RETRIES
        self.temperature = settings.LLM_TEMPERATURE
        self.thinking = settings.LLM_THINKING

    def _backoff_delay(self, attempt: int, status_code: int = 0, retry_after: str | None = None) -> float:
        """Calculate backoff delay. 429 uses longer delays and may respect Retry-After header."""
        if retry_after and retry_after.isdigit():
            return float(retry_after)
        base = 5.0 if status_code == 429 else 1.0
        return base * (2 ** (attempt - 1))

    def generate(self, system_prompt: str, user_message: str) -> str:
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        request_body = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        if self.thinking:
            request_body["thinking"] = {"type": "enabled"}

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = httpx.post(
                    f"{self.base_url}/chat/completions",
                    json=request_body,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]
                logger.info(
                    "LLM call succeeded: provider=%s model=%s tokens_used=%s",
                    self.provider,
                    self.model,
                    data.get("usage", {}),
                )
                return content

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning("LLM call timeout (attempt %d/%d)", attempt + 1, self.max_retries + 1)
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.error("LLM API error: status=%d body=%s", e.response.status_code, e.response.text)
                if e.response.status_code in (401, 403):
                    break
                if e.response.status_code == 429:
                    retry_after = e.response.headers.get("Retry-After")
                    delay = self._backoff_delay(attempt + 1, 429, retry_after)
                    logger.warning(
                        "LLM rate limited (429). Waiting %.1fs before retry %d/%d (Retry-After: %s)",
                        delay, attempt + 1, self.max_retries + 1, retry_after or "none",
                    )
                    time.sleep(delay)
                    continue
            except Exception as e:
                last_error = e
                logger.error("LLM call unexpected error: %s", str(e))

            if attempt < self.max_retries:
                delay = self._backoff_delay(attempt + 1)
                logger.info("Retrying LLM call in %.1fs (attempt %d/%d)", delay, attempt + 1, self.max_retries + 1)
                time.sleep(delay)

        raise LLMCallException(
            f"LLM call failed after {self.max_retries + 1} attempt(s): {str(last_error)}"
        )
