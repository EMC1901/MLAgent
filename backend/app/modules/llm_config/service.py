import logging
import time
from typing import Tuple

import httpx

from app.shared.config.llm_config_store import llm_config_store
from app.modules.llm_config.schemas import (
    LLMConfigRequest,
    LLMConfigResponse,
    LLMConfigValidateResponse,
)

logger = logging.getLogger(__name__)

_VALIDATION_TIMEOUT = 30
_VALIDATION_PROMPT = "Respond with exactly: OK"


def _build_url(base_url: str) -> str:
    url = (base_url or "https://api.openai.com/v1").rstrip("/")
    if not url.endswith("/chat/completions"):
        url = f"{url}/chat/completions"
    return url


def _infer_base_url(model_name: str, requested_base_url: str) -> str:
    """If user didn't provide a base_url, try to infer it from known providers."""
    if requested_base_url.strip():
        return requested_base_url.strip()
    model_lower = model_name.lower()
    if "deepseek" in model_lower:
        return "https://api.deepseek.com"
    if "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower or "o4" in model_lower:
        return "https://api.openai.com/v1"
    if "claude" in model_lower:
        return "https://api.anthropic.com"
    return "https://api.openai.com/v1"


async def validate_config(request: LLMConfigRequest) -> LLMConfigValidateResponse:
    """Test the LLM connection by sending a minimal chat completion request."""
    base_url = _infer_base_url(request.model_name, request.base_url)
    url = _build_url(base_url)
    model_name = request.model_name.strip()
    api_key = request.api_key.strip()

    request_body: dict = {
        "model": model_name,
        "messages": [{"role": "user", "content": _VALIDATION_PROMPT}],
        "temperature": 0.0,
        "max_tokens": 16,
    }
    if request.thinking_enabled:
        request_body["thinking"] = {"type": "enabled"}

    logger.info(
        "Validating LLM config: model=%s url=%s thinking=%s api_key=***%s",
        model_name, url, request.thinking_enabled,
        api_key[-4:] if len(api_key) >= 4 else "",
    )

    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=_VALIDATION_TIMEOUT) as client:
            response = await client.post(
                url,
                json=request_body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )
        elapsed_ms = (time.perf_counter() - t0) * 1000

        if response.status_code == 401:
            logger.warning("LLM config validation failed: HTTP 401 unauthorized — invalid API key")
            return LLMConfigValidateResponse(
                valid=False,
                message="Authentication failed (HTTP 401). The API key is invalid or expired.",
                model_name=model_name,
                latency_ms=round(elapsed_ms, 1),
            )
        if response.status_code == 403:
            logger.warning("LLM config validation failed: HTTP 403 forbidden")
            return LLMConfigValidateResponse(
                valid=False,
                message="Access denied (HTTP 403). The API key does not have permission for this model.",
                model_name=model_name,
                latency_ms=round(elapsed_ms, 1),
            )
        if response.status_code == 404:
            logger.warning("LLM config validation failed: HTTP 404 — model or endpoint not found")
            return LLMConfigValidateResponse(
                valid=False,
                message=f"Model '{model_name}' not found (HTTP 404). Check the model name and base URL.",
                model_name=model_name,
                latency_ms=round(elapsed_ms, 1),
            )
        if response.status_code == 429:
            logger.warning("LLM config validation failed: HTTP 429 rate limited")
            return LLMConfigValidateResponse(
                valid=False,
                message="Rate limited (HTTP 429). The provider is throttling requests. Try again later.",
                model_name=model_name,
                latency_ms=round(elapsed_ms, 1),
            )

        response.raise_for_status()
        data = response.json()

        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})
        tokens = usage.get("total_tokens", 0)

        if not content:
            logger.warning("LLM config validation failed: empty response content")
            return LLMConfigValidateResponse(
                valid=False,
                message="The model returned an empty response. It may not support chat completions.",
                model_name=model_name,
                latency_ms=round(elapsed_ms, 1),
            )

        logger.info(
            "LLM config validation SUCCESS: model=%s latency=%.0fms tokens=%d",
            model_name, elapsed_ms, tokens,
        )
        return LLMConfigValidateResponse(
            valid=True,
            message=f"Connection successful. Model '{model_name}' responded correctly.",
            model_name=model_name,
            latency_ms=round(elapsed_ms, 1),
            tokens_used=tokens,
        )

    except httpx.TimeoutException:
        logger.warning("LLM config validation failed: timeout after %ds", _VALIDATION_TIMEOUT)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return LLMConfigValidateResponse(
            valid=False,
            message=f"Connection timed out after {_VALIDATION_TIMEOUT}s. Check the base URL and network connectivity.",
            model_name=model_name,
            latency_ms=round(elapsed_ms, 1),
        )
    except httpx.ConnectError as e:
        logger.warning("LLM config validation failed: connection error — %s", str(e))
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return LLMConfigValidateResponse(
            valid=False,
            message=f"Failed to connect to the API endpoint. Check the base URL. ({str(e)[:200]})",
            model_name=model_name,
            latency_ms=round(elapsed_ms, 1),
        )
    except Exception as e:
        logger.warning("LLM config validation failed: unexpected error — %s: %s", type(e).__name__, str(e))
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return LLMConfigValidateResponse(
            valid=False,
            message=f"Validation error: {type(e).__name__}: {str(e)[:300]}",
            model_name=model_name,
            latency_ms=round(elapsed_ms, 1),
        )


async def set_config(request: LLMConfigRequest) -> Tuple[LLMConfigResponse, LLMConfigValidateResponse]:
    """Validate then store the LLM configuration."""
    validation = await validate_config(request)

    if validation.valid:
        base_url = _infer_base_url(request.model_name, request.base_url)
        llm_config_store.set_config(
            model_name=request.model_name,
            thinking_enabled=request.thinking_enabled,
            api_key=request.api_key,
            base_url=base_url,
        )

    response = LLMConfigResponse(
        model_name=request.model_name.strip(),
        thinking_enabled=request.thinking_enabled,
        api_key_masked=_mask_key(request.api_key),
        base_url=_infer_base_url(request.model_name, request.base_url),
        is_custom=validation.valid,
    )
    return response, validation


def get_config() -> LLMConfigResponse:
    """Return the current LLM config (with masked API key)."""
    config = llm_config_store.get_config()
    if config and llm_config_store.is_custom_configured():
        return LLMConfigResponse(
            model_name=config.model_name,
            thinking_enabled=config.thinking_enabled,
            api_key_masked=_mask_key(config.api_key),
            base_url=config.base_url,
            is_custom=True,
        )
    from app.shared.config.settings import settings
    return LLMConfigResponse(
        model_name=settings.LLM_MODEL,
        thinking_enabled=settings.LLM_THINKING,
        api_key_masked=_mask_key(settings.LLM_API_KEY),
        base_url=settings.LLM_BASE_URL,
        is_custom=False,
    )


def clear_config() -> LLMConfigResponse:
    """Reset to defaults."""
    llm_config_store.clear_config()
    return get_config()


def _mask_key(key: str) -> str:
    if not key:
        return "(not set)"
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]
