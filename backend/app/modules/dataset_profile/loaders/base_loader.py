from abc import ABC, abstractmethod
from typing import Any


class BaseLoader(ABC):
    """Unified interface for all dataset loaders.

    Each loader receives a context dict from context_builder and
    a source_resolution dict from source_resolver, and returns
    a (DataFrame, loading_result_dict) tuple.
    """

    @abstractmethod
    def load(self, context: dict, source_resolution: dict) -> Any:
        """Load dataset and return a pandas DataFrame or None on failure."""
        ...

    @abstractmethod
    def loader_name(self) -> str:
        ...
