import logging
import pandas as pd
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from app.modules.feature_preprocessing.exceptions import ScalingFailedException
from app.modules.feature_preprocessing.enums import ScalingStrategy

logger = logging.getLogger(__name__)


class Scaler:
    """Wraps sklearn scalers (Standard, Robust, MinMax)."""

    def __init__(self, strategy: str = ScalingStrategy.STANDARD_SCALER):
        self.strategy = strategy
        self._scaler = None
        self._fitted_columns: list = []

    def fit_transform(self, df: pd.DataFrame, feature_columns: list) -> pd.DataFrame:
        if not feature_columns:
            return df

        result_df = df.copy()

        try:
            if self.strategy == ScalingStrategy.ROBUST_SCALER:
                self._scaler = RobustScaler()
            elif self.strategy == ScalingStrategy.MINMAX_SCALER:
                self._scaler = MinMaxScaler()
            else:
                self._scaler = StandardScaler()

            result_df[feature_columns] = self._scaler.fit_transform(
                result_df[feature_columns]
            )
            self._fitted_columns = list(feature_columns)
        except Exception as e:
            raise ScalingFailedException(f"Scaling failed: {e}")

        return result_df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self._scaler is None:
            return df
        if not self._fitted_columns:
            return df

        result_df = df.copy()
        result_df[self._fitted_columns] = self._scaler.transform(
            result_df[self._fitted_columns]
        )
        return result_df

    @property
    def fitted_columns(self) -> list:
        return self._fitted_columns
