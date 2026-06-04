import logging
import threading
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    model_name: str = ""
    thinking_enabled: bool = False
    api_key: str = ""
    base_url: str = ""


class LLMConfigStore:
    """Thread-safe in-memory store for user-provided LLM configuration.

    When a custom config is set, LLMClient instances read from this store
    instead of the static settings defaults. Only one custom config can be
    active at a time (no per-task isolation).
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._config: Optional[LLMConfig] = None
        self._custom_configured = False

    def set_config(self, model_name: str, thinking_enabled: bool, api_key: str, base_url: str = "") -> None:
        with self._lock:
            self._config = LLMConfig(
                model_name=model_name.strip(),
                thinking_enabled=thinking_enabled,
                api_key=api_key.strip(),
                base_url=base_url.strip(),
            )
            self._custom_configured = True
            logger.info(
                "LLM custom config set: model=%s thinking=%s base_url=%s api_key=***%s",
                self._config.model_name,
                self._config.thinking_enabled,
                self._config.base_url or "(default)",
                self._config.api_key[-4:] if len(self._config.api_key) >= 4 else "",
            )

    def get_config(self) -> Optional[LLMConfig]:
        with self._lock:
            return self._config

    def clear_config(self) -> None:
        with self._lock:
            if self._custom_configured:
                logger.info("LLM custom config cleared, reverting to defaults")
            self._config = None
            self._custom_configured = False

    def is_custom_configured(self) -> bool:
        with self._lock:
            return self._custom_configured and self._config is not None


llm_config_store = LLMConfigStore()
