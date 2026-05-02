import logging
import pandas as pd
import numpy as np
from app.modules.feature_engineering.featurizers.base_featurizer import BaseFeaturizer

logger = logging.getLogger(__name__)


class DescriptorFeaturizer(BaseFeaturizer):

    def featurizer_name(self) -> str:
        return "existing_descriptors"

    def featurize(self, raw_dataframe, context, resolved_strategy) -> dict:
        data_context = context.get("data_context") or {}
        target_column = data_context.get("target_column")
        input_columns = data_context.get("input_columns", [])

        all_columns = list(raw_dataframe.columns)
        exclude_cols = set()
        if target_column and target_column in all_columns:
            exclude_cols.add(target_column)

        # Exclude non-numeric and ID-like columns
        id_patterns = ["id", "sample_id", "index", "row_id"]
        for col in all_columns:
            if col.lower() in id_patterns:
                exclude_cols.add(col)

        numeric_cols = []
        non_numeric_cols = []
        for col in all_columns:
            if col in exclude_cols:
                continue
            if pd.api.types.is_numeric_dtype(raw_dataframe[col]):
                numeric_cols.append(col)
            else:
                non_numeric_cols.append(col)

        if not numeric_cols:
            return {
                "status": "failed",
                "feature_dataframe": None,
                "feature_columns": [],
                "executed_featurizers": [],
                "failed_samples": [],
                "warnings": [],
                "errors": ["No numeric descriptor columns found in data."],
            }

        feature_df = raw_dataframe[numeric_cols].copy()
        warnings = []
        if non_numeric_cols:
            warnings.append(
                f"Excluded {len(non_numeric_cols)} non-numeric columns: {non_numeric_cols}"
            )

        feature_columns = list(feature_df.columns)
        executed = [{
            "name": self.featurizer_name(),
            "status": "success",
            "n_features_generated": len(feature_columns),
            "failed_sample_count": 0,
        }]

        return {
            "status": "success",
            "feature_dataframe": feature_df,
            "feature_columns": feature_columns,
            "executed_featurizers": executed,
            "failed_samples": [],
            "warnings": warnings,
            "errors": [],
        }
