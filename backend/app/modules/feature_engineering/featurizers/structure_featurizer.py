import logging
import pandas as pd
from app.modules.feature_engineering.featurizers.base_featurizer import BaseFeaturizer

logger = logging.getLogger(__name__)


class StructureFeaturizer(BaseFeaturizer):

    def featurizer_name(self) -> str:
        return "structure_descriptors"

    def featurize(self, raw_dataframe, context, resolved_strategy) -> dict:
        """MVP placeholder: structure featurization is not yet supported.

        If the data already has numeric descriptor columns, we could fall back
        to DescriptorFeaturizer. Otherwise return not-available.
        """
        data_context = context.get("data_context") or {}
        input_columns = data_context.get("input_columns", [])

        # Check if there are numeric columns that could serve as descriptors
        numeric_cols = []
        for col in raw_dataframe.columns:
            if col in (input_columns or []):
                continue
            if pd.api.types.is_numeric_dtype(raw_dataframe[col]):
                numeric_cols.append(col)

        if numeric_cols:
            feature_df = raw_dataframe[numeric_cols].copy()
            feature_columns = list(feature_df.columns)
            return {
                "status": "success",
                "feature_dataframe": feature_df,
                "feature_columns": feature_columns,
                "executed_featurizers": [{
                    "name": "structure_descriptors_fallback",
                    "status": "fallback_to_existing_descriptors",
                    "n_features_generated": len(feature_columns),
                    "failed_sample_count": 0,
                }],
                "failed_samples": [],
                "warnings": [
                    "Structure featurization is not yet supported. "
                    "Using existing numeric columns as fallback descriptors. "
                    "Full structure feature engineering (pymatgen/matminer) is planned for "
                    "a future version."
                ],
                "errors": [],
            }

        return {
            "status": "failed",
            "feature_dataframe": None,
            "feature_columns": [],
            "executed_featurizers": [],
            "failed_samples": [],
            "warnings": [
                "Structure featurization is not yet supported in MVP. "
                "No numeric fallback columns available. "
                "Please provide descriptor columns or wait for structure featurizer support."
            ],
            "errors": ["STRUCTURE_FEATURIZER_NOT_AVAILABLE"],
        }
