"""Statistical descriptor featurizer.

Generates additional features from existing numeric descriptors:
  - Pairwise ratios (col_a / col_b) for columns with non-zero values
  - Pairwise products (col_a * col_b)
  - Basic rolling statistics if time-series columns detected

No third-party dependencies required.
"""
import logging
import time
import pandas as pd
import numpy as np
from app.modules.feature_engineering.featurizers.base_featurizer import BaseFeaturizer

logger = logging.getLogger(__name__)


class DescriptorStatisticalFeaturizer(BaseFeaturizer):

    def featurizer_name(self) -> str:
        return "descriptor_statistical"

    def featurize(self, raw_dataframe, context, resolved_strategy) -> dict:
        start_time = time.time()

        # Identify numeric columns
        numeric_cols = raw_dataframe.select_dtypes(include=[np.number]).columns.tolist()
        n_numeric = len(numeric_cols)

        if n_numeric < 2:
            return {
                "status": "failed",
                "feature_dataframe": pd.DataFrame(index=raw_dataframe.index),
                "feature_columns": [],
                "executed_featurizers": [{
                    "name": self.featurizer_name(),
                    "display_name": "Descriptor Statistical Features",
                    "status": "failed",
                    "n_features_generated": 0,
                    "failed_sample_count": len(raw_dataframe),
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    "dependency_versions": {},
                }],
                "failed_samples": [],
                "failed_sample_count": 0,
                "warnings": [],
                "errors": [f"Need at least 2 numeric columns, found {n_numeric}."],
            }

        feature_dfs = []
        warnings = []

        # Cap feature explosion: use at most 15 numeric columns
        cols = numeric_cols[:15]
        data = raw_dataframe[cols].astype(float)

        # 1. Pairwise ratios
        ratio_pairs = []
        for i in range(len(cols)):
            for j in range(len(cols)):
                if i != j:
                    ratio_pairs.append((cols[i], cols[j]))
        if len(ratio_pairs) > 100:
            warnings.append(f"Limiting ratios to 100 of {len(ratio_pairs)} pairs.")
            ratio_pairs = ratio_pairs[:100]

        ratio_data = {}
        for col_a, col_b in ratio_pairs:
            denom = data[col_b].replace(0, np.nan)
            ratio_data[f"ratio_{col_a}_over_{col_b}"] = data[col_a] / denom
        if ratio_data:
            feature_dfs.append(pd.DataFrame(ratio_data, index=raw_dataframe.index))

        # 2. Pairwise products (limited to 50)
        prod_cols = cols[:10]
        prod_pairs = []
        for i in range(len(prod_cols)):
            for j in range(i + 1, len(prod_cols)):
                prod_pairs.append((prod_cols[i], prod_cols[j]))
        if len(prod_pairs) > 50:
            prod_pairs = prod_pairs[:50]

        prod_data = {}
        for col_a, col_b in prod_pairs:
            prod_data[f"product_{col_a}_{col_b}"] = data[col_a] * data[col_b]
        if prod_data:
            feature_dfs.append(pd.DataFrame(prod_data, index=raw_dataframe.index))

        # 3. Basic summary stats per row
        stat_data = {}
        stat_data["descriptor_mean"] = data.mean(axis=1)
        stat_data["descriptor_std"] = data.std(axis=1)
        stat_data["descriptor_min"] = data.min(axis=1)
        stat_data["descriptor_max"] = data.max(axis=1)
        stat_data["descriptor_range"] = stat_data["descriptor_max"] - stat_data["descriptor_min"]
        feature_dfs.append(pd.DataFrame(stat_data, index=raw_dataframe.index))

        result_df = pd.concat(feature_dfs, axis=1)
        result_df = result_df.fillna(0)
        feature_columns = list(result_df.columns)
        n_features = len(feature_columns)

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "status": "success" if n_features > 0 else "failed",
            "feature_dataframe": result_df,
            "feature_columns": feature_columns,
            "executed_featurizers": [{
                "name": self.featurizer_name(),
                "display_name": "Descriptor Statistical Features",
                "status": "success" if n_features > 0 else "failed",
                "n_features_generated": n_features,
                "failed_sample_count": 0,
                "execution_time_ms": elapsed_ms,
                "dependency_versions": {},
            }],
            "failed_samples": [],
            "failed_sample_count": 0,
            "warnings": warnings,
            "errors": [],
        }
