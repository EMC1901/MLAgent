"""Enhanced descriptor cleaner featurizer.

Cleans and normalizes pre-existing descriptor columns:
  - Identifies numeric feature columns
  - Excludes target, ID, formula, composition columns
  - Drops all-NaN columns
  - Drops constant columns
  - Marks high-missing-ratio columns
  - Outputs feature group metadata
"""
import logging
import time
import pandas as pd
import numpy as np
from app.modules.feature_engineering.featurizers.base_featurizer import BaseFeaturizer

logger = logging.getLogger(__name__)

_NON_FEATURE_PATTERNS = [
    "sample_id", "id", "index", "formula", "composition",
    "material_id", "cif", "structure", "target",
]


class DescriptorCleanerFeaturizer(BaseFeaturizer):

    def featurizer_name(self) -> str:
        return "descriptor_cleaner"

    def featurize(self, raw_dataframe, context, resolved_strategy) -> dict:
        start_time = time.time()

        data_context = context.get("data_context") or {}
        target_column = data_context.get("target_column")

        df = raw_dataframe.copy()

        # Identify columns to exclude
        exclude_cols = set()
        for col in df.columns:
            col_lower = col.lower()
            for pattern in _NON_FEATURE_PATTERNS:
                if pattern in col_lower:
                    exclude_cols.add(col)
                    break

        if target_column and target_column in df.columns:
            exclude_cols.add(target_column)

        # Select numeric columns not in exclude set
        feature_cols = []
        for col in df.columns:
            if col in exclude_cols:
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                feature_cols.append(col)

        if not feature_cols:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "failed",
                "feature_dataframe": pd.DataFrame(index=df.index),
                "feature_columns": [],
                "executed_featurizers": [{
                    "name": self.featurizer_name(),
                    "display_name": "Descriptor Cleaner",
                    "status": "failed",
                    "n_features_generated": 0,
                    "failed_sample_count": len(df),
                    "execution_time_ms": elapsed_ms,
                    "dependency_versions": {},
                }],
                "failed_samples": [],
                "failed_sample_count": 0,
                "warnings": [],
                "errors": ["No numeric feature columns found after filtering."],
            }

        cleaned = df[feature_cols].copy()

        # Drop all-NaN columns
        all_nan = cleaned.columns[cleaned.isnull().all()].tolist()

        # Drop constant columns (single unique non-NaN value)
        constant = []
        for col in cleaned.columns:
            unique = cleaned[col].dropna().unique()
            if len(unique) <= 1:
                constant.append(col)

        # Identify high-missing-ratio columns (>50%)
        n_rows = len(cleaned)
        high_missing = []
        for col in cleaned.columns:
            missing_count = cleaned[col].isnull().sum()
            if missing_count / max(n_rows, 1) > 0.5:
                high_missing.append(col)

        # Drop all-nan and constant columns
        drop_cols = list(set(all_nan + constant))
        if drop_cols:
            cleaned = cleaned.drop(columns=drop_cols)

        remaining_cols = list(cleaned.columns)
        prefix = f"{self.featurizer_name()}__"
        rename_map = {c: f"{prefix}{c}" for c in remaining_cols}
        cleaned = cleaned.rename(columns=rename_map)
        feature_columns = list(cleaned.columns)

        n_features = len(feature_columns)
        elapsed_ms = int((time.time() - start_time) * 1000)

        warnings = []
        if all_nan:
            warnings.append(f"Dropped all-NaN columns: {all_nan}")
        if constant:
            warnings.append(f"Dropped constant columns: {constant}")
        if high_missing:
            warnings.append(f"Columns with >50% missing values: {high_missing}")

        status = "success" if n_features > 0 else "failed"

        return {
            "status": status,
            "feature_dataframe": cleaned,
            "feature_columns": feature_columns,
            "executed_featurizers": [{
                "name": self.featurizer_name(),
                "display_name": "Descriptor Cleaner",
                "status": status,
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
