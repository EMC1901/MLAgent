import logging
from app.modules.feature_preprocessing.preprocessors.imputer import Imputer
from app.modules.feature_preprocessing.preprocessors.scaler import Scaler
from app.modules.feature_preprocessing.preprocessors.encoder import Encoder
from app.modules.feature_preprocessing.preprocessors.feature_selector import FeatureSelector

logger = logging.getLogger(__name__)


class PreprocessingPipeline:
    """Composite pipeline that bundles fitted preprocessor components.

    Can be serialized via joblib for reuse in model training and inference.
    """

    def __init__(self):
        self.imputer: Imputer = None
        self.scaler: Scaler = None
        self.encoder: Encoder = None
        self.feature_selector: FeatureSelector = None
        self._feature_columns: list = []

    def set_components(
        self,
        imputer: Imputer,
        scaler: Scaler,
        encoder: Encoder,
        feature_selector: FeatureSelector,
        feature_columns: list,
    ):
        self.imputer = imputer
        self.scaler = scaler
        self.encoder = encoder
        self.feature_selector = feature_selector
        self._feature_columns = list(feature_columns)

    def transform(self, df):
        """Apply the full pipeline to new data."""
        import pandas as pd

        result = df.copy()
        non_feature_cols = [c for c in result.columns if c not in self._feature_columns]

        # Determine feature columns present in input
        present_features = [c for c in self._feature_columns if c in result.columns]
        if not present_features:
            return result

        feature_df = result[present_features].copy()

        if self.imputer is not None:
            feature_df = self.imputer.transform(feature_df)
        if self.scaler is not None:
            feature_df = self.scaler.transform(feature_df)
        if self.encoder is not None:
            feature_df = self.encoder.transform(feature_df)
        if self.feature_selector is not None and self.feature_selector._retained_columns:
            retain = [c for c in self.feature_selector._retained_columns if c in feature_df.columns]
            feature_df = feature_df[retain]

        # Reassemble
        result_parts = [result[non_feature_cols]] if non_feature_cols else []
        result_parts.append(feature_df)
        return pd.concat(result_parts, axis=1)

    @property
    def feature_columns(self) -> list:
        return self._feature_columns


def build_pipeline(execution_result: dict, feature_columns: list) -> PreprocessingPipeline:
    """Build a PreprocessingPipeline from the execution results."""
    pipeline = PreprocessingPipeline()
    pipeline.set_components(
        imputer=execution_result.get("imputer"),
        scaler=execution_result.get("scaler"),
        encoder=execution_result.get("encoder"),
        feature_selector=execution_result.get("feature_selector"),
        feature_columns=feature_columns,
    )
    return pipeline
