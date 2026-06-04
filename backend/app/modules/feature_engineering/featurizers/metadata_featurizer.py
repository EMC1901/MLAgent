"""Metadata featurizer.

Extracts metadata columns from the dataset that describe experimental
conditions, synthesis parameters, or measurement metadata.

Identifies columns that are not formula, structure, or target variables,
and passes them through as features.
"""
import logging
import time
import pandas as pd
import numpy as np
from app.modules.feature_engineering.featurizers.base_featurizer import BaseFeaturizer

logger = logging.getLogger(__name__)

# Column name patterns that signal metadata content
_METADATA_KEYWORDS = [
    "temperature", "temp", "pressure", "time", "duration",
    "synthesis", "annealing", "calcination", "sintering",
    "atmosphere", "gas", "flow", "rate", "ph", "concentration",
    "solvent", "precursor", "substrate", "thickness",
    "method", "technique", "instrument", "condition",
    "batch", "sample_id", "reference", "comment", "note",
    "purity", "grain_size", "particle_size", "morphology",
]


class MetadataFeaturizer(BaseFeaturizer):

    def featurizer_name(self) -> str:
        return "metadata_feature_extractor"

    def _is_metadata_column(self, col_name: str, exclude_cols: set) -> bool:
        col_lower = col_name.lower().strip()
        if col_name in exclude_cols:
            return False
        for kw in _METADATA_KEYWORDS:
            if kw in col_lower:
                return True
        return False

    def featurize(self, raw_dataframe, context, resolved_strategy) -> dict:
        start_time = time.time()

        data_context = context.get("data_context") or {}
        input_columns = data_context.get("input_columns", [])
        target_column = data_context.get("target_column", "")

        exclude = {"formula", "composition", "structure", "cif", "poscar"}
        exclude.add(target_column)
        for col in input_columns:
            exclude.add(col)

        metadata_cols = [
            c for c in raw_dataframe.columns
            if self._is_metadata_column(c, exclude)
        ]

        if not metadata_cols:
            return {
                "status": "skipped",
                "feature_dataframe": pd.DataFrame(index=raw_dataframe.index),
                "feature_columns": [],
                "executed_featurizers": [{
                    "name": self.featurizer_name(),
                    "display_name": "Metadata Extractor",
                    "status": "skipped",
                    "n_features_generated": 0,
                    "failed_sample_count": 0,
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    "dependency_versions": {},
                }],
                "failed_samples": [],
                "failed_sample_count": 0,
                "warnings": ["No metadata columns identified."],
                "errors": [],
            }

        result_df = raw_dataframe[metadata_cols].copy()

        # Convert non-numeric metadata to one-hot where feasible
        final_dfs = []
        for col in metadata_cols:
            if pd.api.types.is_numeric_dtype(result_df[col]):
                final_dfs.append(result_df[[col]])
            else:
                # Low-cardinality categorical → one-hot; high-cardinality → skip
                n_unique = result_df[col].nunique()
                if n_unique <= 15:
                    prefix = f"metadata_{col}"
                    dummies = pd.get_dummies(result_df[col], prefix=prefix)
                    final_dfs.append(dummies.astype(float))
                else:
                    pass  # Skip high-cardinality non-numeric

        if not final_dfs:
            return {
                "status": "skipped",
                "feature_dataframe": pd.DataFrame(index=raw_dataframe.index),
                "feature_columns": [],
                "executed_featurizers": [{
                    "name": self.featurizer_name(),
                    "display_name": "Metadata Extractor",
                    "status": "skipped",
                    "n_features_generated": 0,
                    "failed_sample_count": 0,
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    "dependency_versions": {},
                }],
                "failed_samples": [],
                "failed_sample_count": 0,
                "warnings": ["Metadata columns found but none usable (all high-cardinality non-numeric)."],
                "errors": [],
            }

        result = pd.concat(final_dfs, axis=1)
        result = result.fillna(0)
        feature_columns = list(result.columns)
        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "status": "success",
            "feature_dataframe": result,
            "feature_columns": feature_columns,
            "executed_featurizers": [{
                "name": self.featurizer_name(),
                "display_name": "Metadata Extractor",
                "status": "success",
                "n_features_generated": len(feature_columns),
                "failed_sample_count": 0,
                "execution_time_ms": elapsed_ms,
                "dependency_versions": {},
            }],
            "failed_samples": [],
            "failed_sample_count": 0,
            "warnings": [],
            "errors": [],
        }
