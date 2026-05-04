import logging
import pandas as pd
from sklearn.feature_selection import VarianceThreshold
from app.modules.feature_preprocessing.exceptions import FeatureSelectionFailedException
from app.modules.feature_preprocessing.enums import FeatureSelectionStrategy

logger = logging.getLogger(__name__)


class FeatureSelector:
    """Wraps sklearn VarianceThreshold for basic feature selection."""

    def __init__(self, strategy: str = FeatureSelectionStrategy.VARIANCE_THRESHOLD):
        self.strategy = strategy
        self._selector = None
        self._dropped_columns: list = []
        self._retained_columns: list = []

    def fit_transform(self, df: pd.DataFrame, feature_columns: list) -> pd.DataFrame:
        if not feature_columns or self.strategy == FeatureSelectionStrategy.NONE:
            self._retained_columns = list(feature_columns)
            self._dropped_columns = []
            return df

        result_df = df.copy()

        try:
            if self.strategy == FeatureSelectionStrategy.VARIANCE_THRESHOLD:
                self._selector = VarianceThreshold(threshold=0.0)
                transformed = self._selector.fit_transform(result_df[feature_columns])
                retained_cols = result_df[feature_columns].columns[
                    self._selector.get_support()
                ].tolist()
                dropped_cols = [
                    c for c in feature_columns if c not in retained_cols
                ]

                self._retained_columns = retained_cols
                self._dropped_columns = dropped_cols

                # Build new dataframe with retained feature columns
                result_cols = [c for c in result_df.columns if c not in feature_columns]
                result_df = pd.concat(
                    [
                        result_df[result_cols],
                        result_df[feature_columns][retained_cols],
                    ],
                    axis=1,
                )
        except Exception as e:
            raise FeatureSelectionFailedException(f"Feature selection failed: {e}")

        return result_df

    @property
    def dropped_columns(self) -> list:
        return self._dropped_columns

    @property
    def retained_columns(self) -> list:
        return self._retained_columns
