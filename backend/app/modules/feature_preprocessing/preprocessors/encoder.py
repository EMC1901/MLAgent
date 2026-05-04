import logging
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from app.modules.feature_preprocessing.exceptions import EncodingFailedException
from app.modules.feature_preprocessing.enums import EncodingStrategy

logger = logging.getLogger(__name__)


class Encoder:
    """Wraps sklearn encoders for categorical features.

    MVP default is 'none' (no encoding). Categorical features are dropped
    during validation unless explicitly configured otherwise.
    """

    def __init__(self, strategy: str = EncodingStrategy.NONE):
        self.strategy = strategy
        self._encoder = None
        self._fitted_columns: list = []
        self._encoded_column_names: list = []

    def fit_transform(self, df: pd.DataFrame, categorical_columns: list) -> pd.DataFrame:
        if not categorical_columns or self.strategy == EncodingStrategy.NONE:
            return df

        result_df = df.copy()

        try:
            if self.strategy == EncodingStrategy.ONE_HOT:
                self._encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
                encoded = self._encoder.fit_transform(result_df[categorical_columns])
                encoded_cols = self._encoder.get_feature_names_out(categorical_columns)
                encoded_df = pd.DataFrame(encoded, columns=encoded_cols, index=result_df.index)
                result_df = result_df.drop(columns=categorical_columns)
                result_df = pd.concat([result_df, encoded_df], axis=1)
                self._fitted_columns = categorical_columns
                self._encoded_column_names = list(encoded_cols)
        except Exception as e:
            raise EncodingFailedException(f"Encoding failed: {e}")

        return result_df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self._encoder is None or self.strategy == EncodingStrategy.NONE:
            return df

        result_df = df.copy()
        encoded = self._encoder.transform(result_df[self._fitted_columns])
        encoded_df = pd.DataFrame(
            encoded, columns=self._encoded_column_names, index=result_df.index
        )
        result_df = result_df.drop(columns=self._fitted_columns)
        result_df = pd.concat([result_df, encoded_df], axis=1)
        return result_df
