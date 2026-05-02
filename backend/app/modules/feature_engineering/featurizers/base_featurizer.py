from abc import ABC, abstractmethod
from typing import Any
import pandas as pd


class BaseFeaturizer(ABC):

    @abstractmethod
    def featurize(
        self,
        raw_dataframe: pd.DataFrame,
        context: dict,
        resolved_strategy: Any,
    ) -> dict:
        """Generate features and return a FeaturizationResult dict."""
        ...

    @abstractmethod
    def featurizer_name(self) -> str:
        ...
