import logging
import pandas as pd
from sklearn.impute import SimpleImputer
from app.modules.feature_preprocessing.exceptions import ImputationFailedException

logger = logging.getLogger(__name__)


class Imputer:
    """Wraps sklearn SimpleImputer for median/mean/most_frequent strategies."""

    def __init__(self, strategy: str = "median"):
        self.strategy = strategy
        self._imputer = None
        self._fitted_columns: list = []

    def fit_transform(self, df: pd.DataFrame, feature_columns: list) -> pd.DataFrame:
        if not feature_columns:
            return df

        result_df = df.copy()
        cols_with_missing = [c for c in feature_columns if df[c].isnull().any()]

        if not cols_with_missing:
            # No missing values, create a no-op imputer
            self._imputer = SimpleImputer(strategy="median")
            self._imputer.fit(pd.DataFrame({"dummy": [0]}))
            self._fitted_columns = []
            return result_df

        try:
            self._imputer = SimpleImputer(strategy=self.strategy)
            result_df[cols_with_missing] = self._imputer.fit_transform(
                result_df[cols_with_missing]
            )
            self._fitted_columns = cols_with_missing
        except Exception as e:
            raise ImputationFailedException(f"Imputation failed: {e}")

        return result_df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self._imputer is None:
            return df
        if not self._fitted_columns:
            return df

        result_df = df.copy()
        result_df[self._fitted_columns] = self._imputer.transform(
            result_df[self._fitted_columns]
        )
        return result_df

    @property
    def fitted_columns(self) -> list:
        return self._fitted_columns
