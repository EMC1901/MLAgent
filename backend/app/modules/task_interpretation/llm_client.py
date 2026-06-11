import asyncio
import httpx
import logging
import random
import sys
import threading
import time
from typing import List, Dict, Any
from app.shared.config.settings import settings
from app.shared.config.llm_config_store import llm_config_store
from app.modules.task_interpretation.exceptions import LLMCallException


def _diag(msg, *args):
    formatted = msg % args if args else msg
    print(f"DIAG     [llm] {formatted}", file=sys.stderr, flush=True)


logger = logging.getLogger(__name__)


class LLMClient:
    # Class-level cooldown: all LLMClient instances share the same rate budget.
    _last_call_time: float = 0.0
    _cooldown_lock = threading.Lock()
    _cooldown_lock_async: asyncio.Lock | None = None

    def __init__(self):
        # Immutable settings — safe to snapshot at import time.
        self.timeout = settings.LLM_TIMEOUT
        self.max_retries = settings.LLM_MAX_RETRIES
        self.temperature = settings.LLM_TEMPERATURE
        self.reasoning_effort = settings.LLM_REASONING_EFFORT
        # Resolve mutable config so that self.model / self.provider / etc.
        # are available for callers that read them before generate().
        # generate() re-resolves to pick up Switch Model changes.
        self._resolve_config()

    def _resolve_config(self):
        """Read mutable LLM config at call time so Switch Model takes effect immediately."""
        custom = llm_config_store.get_config()
        if custom:
            self.model = custom.model_name
            self.api_key = custom.api_key
            self.base_url = (custom.base_url or settings.LLM_BASE_URL).rstrip("/")
            self.thinking = custom.thinking_enabled
            self.provider = "dashscope" if "dashscope" in self.base_url.lower() else "custom"
        elif settings.LLM_MODEL:
            self.model = settings.LLM_MODEL
            self.api_key = settings.LLM_API_KEY
            self.base_url = settings.LLM_BASE_URL.rstrip("/")
            self.thinking = settings.LLM_THINKING
            self.provider = settings.LLM_PROVIDER
        else:
            self.model = ""
            self.api_key = ""
            self.base_url = ""
            self.thinking = False
            self.provider = ""

    def _check_configured(self):
        if not self.model:
            raise LLMCallException(
                "No LLM model configured. Please configure an LLM model via "
                "Settings → Switch Model before running any task."
            )

    def _backoff_delay(self, attempt: int, status_code: int = 0, retry_after: str | None = None) -> float:
        """Calculate backoff delay with jitter to avoid thundering herd.

        429 rate limits use longer base delays. Honors Retry-After header
        when the server provides it. Adds ±25% jitter to spread retries
        across concurrent callers.
        """
        if retry_after and retry_after.isdigit():
            return float(retry_after)
        base = 10.0 if status_code == 429 else 2.0
        delay = base * (2 ** (attempt - 1))
        jitter = delay * 0.25 * (2 * random.random() - 1)
        return max(1.0, delay + jitter)

    @classmethod
    def _wait_for_cooldown(cls):
        """Enforce a minimum interval between LLM calls across all modules.

        Multiple modules (task_interpretation → workflow_planning → model_search
        → ...) call the LLM API sequentially. Without an inter-call cooldown,
        they collectively exhaust the provider's rate limit before any single
        module completes its retry cycle.
        """
        cooldown = getattr(settings, "LLM_CALL_COOLDOWN_SECONDS", 20)
        with cls._cooldown_lock:
            elapsed = time.time() - cls._last_call_time
            if elapsed < cooldown:
                wait = cooldown - elapsed
                logger.info(
                    "LLM inter-call cooldown: waiting %.1fs "
                    "(%.1fs elapsed since last call, minimum interval %.1fs)",
                    wait, elapsed, cooldown,
                )
                time.sleep(wait)
            cls._last_call_time = time.time()

    def generate(self, system_prompt: str, user_message: str) -> str:
        self._resolve_config()
        self._check_configured()

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
            if self.provider in ("dashscope",):
                # GLM-5.1 / DashScope uses enable_thinking
                request_body["enable_thinking"] = True
            else:
                # DeepSeek-style thinking configuration
                request_body["thinking"] = {"type": "enabled"}
                request_body["reasoning_effort"] = self.reasoning_effort

        prompt_chars = len(system_prompt) + len(user_message)
        logger.info(
            "LLM call started — provider=%s model=%s prompt_chars=%d timeout=%ds retries=%d",
            self.provider, self.model, prompt_chars, self.timeout, self.max_retries,
        )
        _diag("generate: provider=%s model=%s timeout=%ds retries=%d prompt_chars=%d",
              self.provider, self.model, self.timeout, self.max_retries,
              prompt_chars)

        # Enforce inter-call cooldown before first attempt (not between retries)
        self._wait_for_cooldown()

        last_error = None
        current_timeout = self.timeout
        for attempt in range(self.max_retries + 1):
            _diag("generate: attempt %d/%d (timeout=%ds) ...", attempt + 1, self.max_retries + 1, current_timeout)
            try:
                response = httpx.post(
                    f"{self.base_url}/chat/completions",
                    json=request_body,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=current_timeout,
                )
                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens")
                completion_tokens = usage.get("completion_tokens")
                total_tokens = usage.get("total_tokens")
                logger.info(
                    "LLM call completed — provider=%s model=%s "
                    "prompt_tokens=%s completion_tokens=%s total_tokens=%s response_chars=%d",
                    self.provider, self.model,
                    prompt_tokens, completion_tokens, total_tokens,
                    len(content) if content else 0,
                )
                _diag("generate: SUCCESS — tokens_used=%s response_chars=%d",
                      usage, len(content) if content else 0)
                return content

            except httpx.TimeoutException as e:
                last_error = e
                _diag("generate: TIMEOUT (attempt %d/%d)", attempt + 1, self.max_retries + 1)
                # Exponential backoff for read timeouts: the model may just need
                # more time to process a large prompt. Double the timeout for the
                # next attempt so we don't keep hitting the same wall.
                # Cap at 600s to bound total retry duration and stay within
                # frontend HTTP client timeouts (typically 10-15 min).
                current_timeout = min(current_timeout * 2, 600)
            except httpx.HTTPStatusError as e:
                last_error = e
                _diag("generate: HTTP error %d (attempt %d/%d): %s",
                      e.response.status_code, attempt + 1, self.max_retries + 1,
                      e.response.text[:200])
                if e.response.status_code in (401, 403):
                    break
                if e.response.status_code == 429:
                    retry_after = e.response.headers.get("Retry-After")
                    delay = self._backoff_delay(attempt + 1, 429, retry_after)
                    _diag("generate: RATE LIMITED (429) — waiting %.1fs (Retry-After: %s)",
                          delay, retry_after or "none")
                    time.sleep(delay)
                    with self._cooldown_lock:
                        LLMClient._last_call_time = time.time()
                    continue
            except Exception as e:
                last_error = e
                _diag("generate: UNEXPECTED ERROR — %s: %s", type(e).__name__, str(e))

            if attempt < self.max_retries:
                delay = self._backoff_delay(attempt + 1)
                _diag("generate: retrying in %.1fs (attempt %d/%d)", delay, attempt + 1, self.max_retries + 1)
                time.sleep(delay)

        _diag("generate: FAILED after %d attempts — last_error=%s: %s",
              self.max_retries + 1, type(last_error).__name__ if last_error else "None", str(last_error))
        raise LLMCallException(
            f"LLM call failed after {self.max_retries + 1} attempt(s): {str(last_error)}"
        )

    @classmethod
    async def _wait_for_cooldown_async(cls):
        """Async version of _wait_for_cooldown — cancellable."""
        if cls._cooldown_lock_async is None:
            cls._cooldown_lock_async = asyncio.Lock()

        cooldown = getattr(settings, "LLM_CALL_COOLDOWN_SECONDS", 20)
        async with cls._cooldown_lock_async:
            elapsed = time.time() - cls._last_call_time
            if elapsed < cooldown:
                wait = cooldown - elapsed
                logger.info(
                    "LLM inter-call cooldown (async): waiting %.1fs "
                    "(%.1fs elapsed since last call, minimum interval %.1fs)",
                    wait, elapsed, cooldown,
                )
                await asyncio.sleep(wait)
            cls._last_call_time = time.time()

    async def async_generate(self, system_prompt: str, user_message: str) -> str:
        """Cancellable async version of generate().

        Uses httpx.AsyncClient so the HTTP request runs on the event loop.
        When the calling asyncio task is cancelled (e.g. Ctrl+C / server
        shutdown), the request is aborted immediately instead of blocking
        a thread that can't be interrupted.
        """
        self._resolve_config()
        self._check_configured()

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
            if self.provider in ("dashscope",):
                request_body["enable_thinking"] = True
            else:
                request_body["thinking"] = {"type": "enabled"}
                request_body["reasoning_effort"] = self.reasoning_effort

        prompt_chars = len(system_prompt) + len(user_message)
        logger.info(
            "LLM call started (async) — provider=%s model=%s prompt_chars=%d timeout=%ds retries=%d",
            self.provider, self.model, prompt_chars, self.timeout, self.max_retries,
        )
        _diag("async_generate: provider=%s model=%s timeout=%ds retries=%d prompt_chars=%d",
              self.provider, self.model, self.timeout, self.max_retries,
              prompt_chars)

        await self._wait_for_cooldown_async()

        last_error = None
        current_timeout = self.timeout
        for attempt in range(self.max_retries + 1):
            _diag("async_generate: attempt %d/%d (timeout=%ds) ...",
                  attempt + 1, self.max_retries + 1, current_timeout)
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        json=request_body,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        timeout=current_timeout,
                    )
                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens")
                completion_tokens = usage.get("completion_tokens")
                total_tokens = usage.get("total_tokens")
                logger.info(
                    "LLM call completed (async) — provider=%s model=%s "
                    "prompt_tokens=%s completion_tokens=%s total_tokens=%s response_chars=%d",
                    self.provider, self.model,
                    prompt_tokens, completion_tokens, total_tokens,
                    len(content) if content else 0,
                )
                _diag("async_generate: SUCCESS — tokens_used=%s response_chars=%d",
                      usage, len(content) if content else 0)
                return content

            except httpx.TimeoutException as e:
                last_error = e
                _diag("async_generate: TIMEOUT (attempt %d/%d)", attempt + 1, self.max_retries + 1)
                current_timeout = min(current_timeout * 2, 600)
            except httpx.HTTPStatusError as e:
                last_error = e
                _diag("async_generate: HTTP error %d (attempt %d/%d): %s",
                      e.response.status_code, attempt + 1, self.max_retries + 1,
                      e.response.text[:200])
                if e.response.status_code in (401, 403):
                    break
                if e.response.status_code == 429:
                    retry_after = e.response.headers.get("Retry-After")
                    delay = self._backoff_delay(attempt + 1, 429, retry_after)
                    _diag("async_generate: RATE LIMITED (429) — waiting %.1fs (Retry-After: %s)",
                          delay, retry_after or "none")
                    await asyncio.sleep(delay)
                    self.__class__._last_call_time = time.time()
                    continue
            except Exception as e:
                last_error = e
                _diag("async_generate: UNEXPECTED ERROR — %s: %s", type(e).__name__, str(e))

            if attempt < self.max_retries:
                delay = self._backoff_delay(attempt + 1)
                _diag("async_generate: retrying in %.1fs (attempt %d/%d)",
                      delay, attempt + 1, self.max_retries + 1)
                await asyncio.sleep(delay)

        _diag("async_generate: FAILED after %d attempts — last_error=%s: %s",
              self.max_retries + 1, type(last_error).__name__ if last_error else "None", str(last_error))
        raise LLMCallException(
            f"LLM call failed after {self.max_retries + 1} attempt(s): {str(last_error)}"
        )
