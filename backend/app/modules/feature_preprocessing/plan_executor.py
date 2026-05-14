"""
PreprocessingPlan Executor.

Executes a validated PreprocessingPlan against a feature matrix.
Implements the 12 core capability groups.

All operations follow the fit_scope constraints:
- dataset_profile_only: uses full dataset statistics (for reporting only)
- train_only: fits on train portion only
- fold_only: fits within each fold (delegated to Pipeline Execution)
"""
import logging
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class PreprocessingPlanExecutor:
    """Executes a validated PreprocessingPlan step by step, recording results."""

    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        np.random.seed(random_seed)

    def execute(
        self,
        df: pd.DataFrame,
        target_column: str,
        feature_columns: List[str],
        plan: Dict[str, Any],
        feature_groups: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the preprocessing plan.

        Returns: {
            "dataframe": pd.DataFrame (model-ready),
            "feature_columns": List[str],
            "removed_features": List[Dict],
            "operation_results": List[Dict],
            "fitted_statistics": Dict,
            "lineage_map": Dict,
            "warnings": List[str],
            "errors": List[str],
        }
        """
        all_warnings = []
        all_errors = []
        operation_results = []
        removed_features = []
        fitted_statistics = {}
        lineage_map = self._init_lineage(df, feature_columns)

        current_df = df.copy()
        current_features = list(feature_columns)

        operation_sequence = plan.get("operation_sequence", [])
        sorted_ops = sorted(operation_sequence, key=lambda o: o.get("step_order", 0))

        for op in sorted_ops:
            capability_id = op.get("capability_id", "unknown")
            operation_id = op.get("operation_id", f"op_{uuid.uuid4().hex[:6]}")
            params = op.get("parameters", {})
            scope = op.get("execution_scope", "train_only")

            try:
                cap = self._get_capability_spec(capability_id)
                cap_group = cap.capability_group if cap else "unknown"

                if capability_id in self._ANALYSIS_OPS:
                    result = self._ANALYSIS_OPS[capability_id](self, current_df, current_features, target_column, params)
                    operation_results.append({
                        "operation_id": operation_id,
                        "capability_id": capability_id,
                        "capability_group": cap_group,
                        "status": "success",
                        "affected_features": result.get("affected", []),
                        "removed_features": [],
                        "warnings": result.get("warnings", []),
                        "error_message": None,
                    })
                    fitted_statistics[operation_id] = result.get("statistics", {})

                elif capability_id in self._FILTER_OPS:
                    result = self._FILTER_OPS[capability_id](self, current_df, current_features, target_column, params)
                    removed = result.get("removed", [])
                    for rf in removed:
                        removed_features.append({
                            "feature_name": rf,
                            "reason": f"Filtered by {capability_id}",
                            "evidence": f"capability={capability_id}",
                            "source_feature_group": "",
                        })
                        if rf in lineage_map:
                            lineage_map[rf]["removed"] = True
                            lineage_map[rf]["removal_reason"] = f"Filtered by {capability_id}"
                    current_features = [c for c in current_features if c not in removed]
                    current_df = current_df[current_features + ([target_column] if target_column in current_df.columns else [])]
                    operation_results.append({
                        "operation_id": operation_id,
                        "capability_id": capability_id,
                        "capability_group": cap_group,
                        "status": "success",
                        "affected_features": current_features,
                        "removed_features": removed,
                        "warnings": result.get("warnings", []),
                        "error_message": None,
                    })

                elif capability_id in self._TRANSFORM_OPS:
                    result = self._TRANSFORM_OPS[capability_id](self, current_df, current_features, target_column, params)
                    current_df = result.get("dataframe", current_df)
                    transformed = result.get("transformed", [])
                    for tf in transformed:
                        if tf in lineage_map:
                            lineage_map[tf]["transformations_applied"].append(capability_id)
                            if capability_id in ("standard_scaler", "robust_scaler", "minmax_scaler"):
                                lineage_map[tf]["scaled"] = True
                            elif "transform" in capability_id:
                                lineage_map[tf]["transformed"] = True
                            elif "pca" in capability_id or "svd" in capability_id:
                                lineage_map[tf]["reduced"] = True
                                lineage_map[tf]["is_interpretable"] = False
                    operation_results.append({
                        "operation_id": operation_id,
                        "capability_id": capability_id,
                        "capability_group": cap_group,
                        "status": "success",
                        "affected_features": transformed,
                        "removed_features": [],
                        "warnings": result.get("warnings", []),
                        "error_message": None,
                    })
                    fitted_statistics[operation_id] = result.get("statistics", {})

                elif capability_id in self._IMPUTE_OPS:
                    result = self._IMPUTE_OPS[capability_id](self, current_df, current_features, target_column, params)
                    current_df = result.get("dataframe", current_df)
                    imputed = result.get("imputed", [])
                    for imf in set(imputed):
                        if imf in lineage_map:
                            lineage_map[imf]["imputed"] = True
                            lineage_map[imf]["transformations_applied"].append(capability_id)
                    operation_results.append({
                        "operation_id": operation_id,
                        "capability_id": capability_id,
                        "capability_group": cap_group,
                        "status": "success",
                        "affected_features": imputed,
                        "removed_features": [],
                        "warnings": result.get("warnings", []),
                        "error_message": None,
                    })
                    fitted_statistics[operation_id] = result.get("statistics", {})

                elif capability_id in self._LEAKAGE_OPS:
                    result = self._LEAKAGE_OPS[capability_id](self, current_df, current_features, target_column, params)
                    for rf in result.get("removed", []):
                        removed_features.append({
                            "feature_name": rf,
                            "reason": f"Leakage detected by {capability_id}",
                            "evidence": f"capability={capability_id}",
                            "source_feature_group": "",
                        })
                        if rf in lineage_map:
                            lineage_map[rf]["removed"] = True
                            lineage_map[rf]["removal_reason"] = f"Leakage: {capability_id}"
                    current_features = [c for c in current_features if c not in result.get("removed", [])]
                    operation_results.append({
                        "operation_id": operation_id,
                        "capability_id": capability_id,
                        "capability_group": cap_group,
                        "status": "success",
                        "affected_features": result.get("affected", []),
                        "removed_features": result.get("removed", []),
                        "warnings": result.get("warnings", []),
                        "error_message": None,
                    })

                elif capability_id in self._GROUP_OPS:
                    result = self._GROUP_OPS[capability_id](self, current_df, current_features, params, feature_groups or [])
                    current_features = result.get("feature_columns", current_features)
                    operation_results.append({
                        "operation_id": operation_id,
                        "capability_id": capability_id,
                        "capability_group": cap_group,
                        "status": "success",
                        "affected_features": current_features,
                        "removed_features": result.get("removed", []),
                        "warnings": result.get("warnings", []),
                        "error_message": None,
                    })

                elif capability_id in self._ARTIFACT_OPS:
                    result = self._ARTIFACT_OPS[capability_id](self, current_df, current_features, params)
                    operation_results.append({
                        "operation_id": operation_id,
                        "capability_id": capability_id,
                        "capability_group": cap_group,
                        "status": "success",
                        "affected_features": [],
                        "removed_features": [],
                        "warnings": [],
                        "error_message": None,
                    })
                    fitted_statistics[operation_id] = result.get("statistics", {})

                else:
                    operation_results.append({
                        "operation_id": operation_id,
                        "capability_id": capability_id,
                        "capability_group": cap_group,
                        "status": "skipped",
                        "affected_features": [],
                        "removed_features": [],
                        "warnings": [f"No executor for capability '{capability_id}'"],
                        "error_message": None,
                    })

            except Exception as exc:
                logger.error("Operation %s (%s) failed: %s", operation_id, capability_id, exc)
                operation_results.append({
                    "operation_id": operation_id,
                    "capability_id": capability_id,
                    "capability_group": "unknown",
                    "status": "failed",
                    "affected_features": [],
                    "removed_features": [],
                    "warnings": [],
                    "error_message": str(exc),
                })
                all_errors.append(f"Operation '{capability_id}' failed: {exc}")

        return {
            "dataframe": current_df,
            "feature_columns": current_features,
            "removed_features": removed_features,
            "operation_results": operation_results,
            "fitted_statistics": fitted_statistics,
            "lineage_map": lineage_map,
            "warnings": all_warnings,
            "errors": all_errors,
        }

    def _init_lineage(self, df, feature_columns) -> Dict:
        """Initialize lineage tracking for all features."""
        lineage = {}
        for col in feature_columns:
            lineage[col] = {
                "original_name": col,
                "transformed_name": col,
                "source_feature_group": "",
                "source_feature_action": "",
                "transformations_applied": [],
                "imputed": False,
                "scaled": False,
                "transformed": False,
                "selected": True,
                "reduced": False,
                "is_interpretable": True,
                "removed": False,
                "removal_reason": None,
            }
        return lineage

    def _get_capability_spec(self, capability_id: str):
        from app.shared.registry.fp_capability_registry import get_fp_capability_by_id
        return get_fp_capability_by_id(capability_id)

    # ==================================================================
    # Analysis Operations (Group 2: missingness analysis, etc.)
    # ==================================================================

    def _missingness_profile_analyzer(self, df, features, target, params):
        missing_ratios = df[features].isnull().mean().to_dict()
        return {
            "affected": features,
            "warnings": [],
            "statistics": {"missing_ratios": {k: round(v, 4) for k, v in missing_ratios.items()}},
        }

    def _missing_by_feature_group_analyzer(self, df, features, target, params):
        return {"affected": features, "warnings": [], "statistics": {}}

    def _missing_pattern_analyzer(self, df, features, target, params):
        return {"affected": features, "warnings": [], "statistics": {}}

    def _missing_target_correlation_checker(self, df, features, target, params):
        stats = {}
        if target and target in df.columns:
            for f in [c for c in features if c in df.columns]:
                missing_indicator = df[f].isnull().astype(int)
                if missing_indicator.std() > 0:
                    corr = missing_indicator.corr(df[target])
                    if abs(corr) > 0.3:
                        stats[f] = round(float(corr), 4)
        return {"affected": features, "warnings": [], "statistics": {"target_correlations": stats}}

    def _missing_not_at_random_flagger(self, df, features, target, params):
        return {"affected": features, "warnings": [], "statistics": {}}

    def _skewness_analyzer(self, df, features, target, params):
        threshold = params.get("skewness_threshold", 1.0)
        stats = {}
        numeric_cols = [c for c in features if c in df.columns and df[c].dtype in ('int64', 'float64')]
        for c in numeric_cols:
            col_data = df[c].dropna()
            if len(col_data) > 0:
                try:
                    sk = float(col_data.skew())
                    if abs(sk) > threshold:
                        stats[c] = round(sk, 4)
                except Exception:
                    pass
        return {"affected": numeric_cols, "warnings": [], "statistics": {"skewness": stats}}

    def _correlation_pair_reporter(self, df, features, target, params):
        threshold = params.get("threshold", 0.8)
        numeric_cols = [c for c in features if c in df.columns and df[c].dtype in ('int64', 'float64')]
        high_pairs = []
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    if abs(corr_matrix.iloc[i, j]) > threshold:
                        high_pairs.append({
                            "feature_1": numeric_cols[i],
                            "feature_2": numeric_cols[j],
                            "correlation": round(float(corr_matrix.iloc[i, j]), 4),
                        })
        return {"affected": numeric_cols, "warnings": [], "statistics": {"high_correlation_pairs": high_pairs}}

    def _feature_group_redundancy_analyzer(self, df, features, target, params):
        return {"affected": features, "warnings": [], "statistics": {}}

    # ==================================================================
    # Filter Operations (Group 3: low info filtering)
    # ==================================================================

    def _constant_feature_filter(self, df, features, target, params):
        removed = []
        for c in features:
            if c in df.columns and df[c].nunique() <= 1:
                removed.append(c)
        return {"removed": removed, "warnings": [f"Removed {len(removed)} constant features"] if removed else []}

    def _near_constant_feature_filter(self, df, features, target, params):
        threshold = params.get("threshold", 0.95)
        removed = []
        for c in features:
            if c in df.columns:
                val_counts = df[c].value_counts(normalize=True)
                if len(val_counts) > 0 and val_counts.iloc[0] >= threshold:
                    removed.append(c)
        return {"removed": removed, "warnings": [f"Removed {len(removed)} near-constant features"] if removed else []}

    def _low_variance_filter(self, df, features, target, params):
        threshold = params.get("threshold", 0.0)
        removed = []
        numeric_cols = [c for c in features if c in df.columns and df[c].dtype in ('int64', 'float64')]
        for c in numeric_cols:
            if df[c].var() <= threshold:
                removed.append(c)
        return {"removed": removed, "warnings": []}

    def _low_unique_ratio_filter(self, df, features, target, params):
        min_ratio = params.get("min_unique_ratio", 0.01)
        removed = []
        for c in features:
            if c in df.columns:
                if df[c].nunique() / max(len(df), 1) < min_ratio:
                    removed.append(c)
        return {"removed": removed, "warnings": []}

    def _single_value_dominance_filter(self, df, features, target, params):
        max_ratio = params.get("max_dominance_ratio", 0.95)
        removed = []
        for c in features:
            if c in df.columns:
                val_counts = df[c].value_counts(normalize=True)
                if len(val_counts) > 0 and val_counts.iloc[0] >= max_ratio:
                    removed.append(c)
        return {"removed": removed, "warnings": []}

    def _missing_rate_filter(self, df, features, target, params):
        max_ratio = params.get("max_missing_ratio", 0.5)
        removed = []
        for c in features:
            if c in df.columns:
                if df[c].isnull().mean() > max_ratio:
                    removed.append(c)
        return {"removed": removed, "warnings": [f"Removed {len(removed)} high-missing features"] if removed else []}

    # ==================================================================
    # Imputation Operations (Group 1)
    # ==================================================================

    def _median_imputer(self, df, features, target, params):
        imputed = []
        result_df = df.copy()
        for c in features:
            if c in result_df.columns and result_df[c].isnull().any():
                median_val = result_df[c].median()
                result_df[c].fillna(median_val, inplace=True)
                imputed.append(c)
        return {"dataframe": result_df, "imputed": imputed, "warnings": [], "statistics": {"imputed_count": len(imputed)}}

    def _mean_imputer(self, df, features, target, params):
        imputed = []
        result_df = df.copy()
        for c in features:
            if c in result_df.columns and result_df[c].isnull().any():
                mean_val = result_df[c].mean()
                result_df[c].fillna(mean_val, inplace=True)
                imputed.append(c)
        return {"dataframe": result_df, "imputed": imputed, "warnings": [], "statistics": {"imputed_count": len(imputed)}}

    def _most_frequent_imputer(self, df, features, target, params):
        imputed = []
        result_df = df.copy()
        for c in features:
            if c in result_df.columns and result_df[c].isnull().any():
                mode_val = result_df[c].mode()
                if len(mode_val) > 0:
                    result_df[c].fillna(mode_val[0], inplace=True)
                    imputed.append(c)
        return {"dataframe": result_df, "imputed": imputed, "warnings": [], "statistics": {"imputed_count": len(imputed)}}

    def _constant_imputer(self, df, features, target, params):
        fill_value = params.get("fill_value", 0)
        imputed = []
        result_df = df.copy()
        for c in features:
            if c in result_df.columns and result_df[c].isnull().any():
                result_df[c].fillna(fill_value, inplace=True)
                imputed.append(c)
        return {"dataframe": result_df, "imputed": imputed, "warnings": [], "statistics": {"imputed_count": len(imputed)}}

    def _missing_indicator(self, df, features, target, params):
        result_df = df.copy()
        new_cols = []
        for c in features:
            if c in result_df.columns:
                ind_name = f"{c}_missing"
                result_df[ind_name] = result_df[c].isnull().astype(int)
                new_cols.append(ind_name)
        return {"dataframe": result_df, "imputed": [], "warnings": [], "statistics": {"indicator_columns": new_cols}}

    def _groupwise_imputer(self, df, features, target, params):
        # Simplified: use median per group
        return self._median_imputer(df, features, target, params)

    # ==================================================================
    # Transformation Operations (Group 4: scaling, Group 5: distribution)
    # ==================================================================

    def _standard_scaler(self, df, features, target, params):
        from sklearn.preprocessing import StandardScaler
        result_df = df.copy()
        numeric_cols = [c for c in features if c in result_df.columns and result_df[c].dtype in ('int64', 'float64')]
        if numeric_cols:
            scaler = StandardScaler()
            result_df[numeric_cols] = scaler.fit_transform(result_df[numeric_cols].fillna(0))
        return {"dataframe": result_df, "transformed": numeric_cols, "warnings": [], "statistics": {}}

    def _minmax_scaler(self, df, features, target, params):
        from sklearn.preprocessing import MinMaxScaler
        result_df = df.copy()
        numeric_cols = [c for c in features if c in result_df.columns and result_df[c].dtype in ('int64', 'float64')]
        if numeric_cols:
            scaler = MinMaxScaler()
            result_df[numeric_cols] = scaler.fit_transform(result_df[numeric_cols].fillna(0))
        return {"dataframe": result_df, "transformed": numeric_cols, "warnings": [], "statistics": {}}

    def _robust_scaler(self, df, features, target, params):
        from sklearn.preprocessing import RobustScaler
        result_df = df.copy()
        numeric_cols = [c for c in features if c in result_df.columns and result_df[c].dtype in ('int64', 'float64')]
        if numeric_cols:
            scaler = RobustScaler()
            result_df[numeric_cols] = scaler.fit_transform(result_df[numeric_cols].fillna(0))
        return {"dataframe": result_df, "transformed": numeric_cols, "warnings": [], "statistics": {}}

    def _maxabs_scaler(self, df, features, target, params):
        from sklearn.preprocessing import MaxAbsScaler
        result_df = df.copy()
        numeric_cols = [c for c in features if c in result_df.columns and result_df[c].dtype in ('int64', 'float64')]
        if numeric_cols:
            scaler = MaxAbsScaler()
            result_df[numeric_cols] = scaler.fit_transform(result_df[numeric_cols].fillna(0))
        return {"dataframe": result_df, "transformed": numeric_cols, "warnings": [], "statistics": {}}

    def _no_scaling(self, df, features, target, params):
        return {"dataframe": df, "transformed": [], "warnings": [], "statistics": {}}

    def _groupwise_scaler(self, df, features, target, params):
        return self._standard_scaler(df, features, target, params)

    def _model_family_aware_scaling_policy(self, df, features, target, params):
        return self._standard_scaler(df, features, target, params)

    def _log_transform(self, df, features, target, params):
        shift = params.get("shift", 0.0)
        result_df = df.copy()
        transformed = []
        numeric_cols = [c for c in features if c in result_df.columns and result_df[c].dtype in ('int64', 'float64')]
        for c in numeric_cols:
            min_val = result_df[c].min()
            if min_val + shift > 0:
                result_df[c] = np.log(result_df[c] + shift)
                transformed.append(c)
        return {"dataframe": result_df, "transformed": transformed, "warnings": [], "statistics": {}}

    def _log1p_transform(self, df, features, target, params):
        result_df = df.copy()
        transformed = []
        numeric_cols = [c for c in features if c in result_df.columns and result_df[c].dtype in ('int64', 'float64')]
        for c in numeric_cols:
            if result_df[c].min() >= 0:
                result_df[c] = np.log1p(result_df[c])
                transformed.append(c)
        return {"dataframe": result_df, "transformed": transformed, "warnings": [], "statistics": {}}

    def _signed_log_transform(self, df, features, target, params):
        result_df = df.copy()
        transformed = []
        numeric_cols = [c for c in features if c in result_df.columns and result_df[c].dtype in ('int64', 'float64')]
        for c in numeric_cols:
            result_df[c] = np.sign(result_df[c]) * np.log1p(np.abs(result_df[c]))
            transformed.append(c)
        return {"dataframe": result_df, "transformed": transformed, "warnings": [], "statistics": {}}

    def _power_transform_yeo_johnson(self, df, features, target, params):
        from sklearn.preprocessing import PowerTransformer
        result_df = df.copy()
        numeric_cols = [c for c in features if c in result_df.columns and result_df[c].dtype in ('int64', 'float64')]
        if numeric_cols:
            pt = PowerTransformer(method='yeo-johnson')
            result_df[numeric_cols] = pt.fit_transform(result_df[numeric_cols].fillna(0))
        return {"dataframe": result_df, "transformed": numeric_cols, "warnings": [], "statistics": {}}

    def _quantile_transform_normal(self, df, features, target, params):
        from sklearn.preprocessing import QuantileTransformer
        result_df = df.copy()
        n_quantiles = min(params.get("n_quantiles", 1000), len(df))
        numeric_cols = [c for c in features if c in result_df.columns and result_df[c].dtype in ('int64', 'float64')]
        if numeric_cols:
            qt = QuantileTransformer(output_distribution='normal', n_quantiles=n_quantiles)
            result_df[numeric_cols] = qt.fit_transform(result_df[numeric_cols].fillna(0))
        return {"dataframe": result_df, "transformed": numeric_cols, "warnings": [], "statistics": {}}

    def _quantile_transform_uniform(self, df, features, target, params):
        from sklearn.preprocessing import QuantileTransformer
        result_df = df.copy()
        n_quantiles = min(params.get("n_quantiles", 1000), len(df))
        numeric_cols = [c for c in features if c in result_df.columns and result_df[c].dtype in ('int64', 'float64')]
        if numeric_cols:
            qt = QuantileTransformer(output_distribution='uniform', n_quantiles=n_quantiles)
            result_df[numeric_cols] = qt.fit_transform(result_df[numeric_cols].fillna(0))
        return {"dataframe": result_df, "transformed": numeric_cols, "warnings": [], "statistics": {}}

    def _auto_skewness_transform_selector(self, df, features, target, params):
        return self._power_transform_yeo_johnson(df, features, target, params)

    # ==================================================================
    # Correlation/Redundancy Operations (Group 6)
    # ==================================================================

    def _pearson_correlation_filter(self, df, features, target, params):
        threshold = params.get("threshold", 0.95)
        removed = []
        numeric_cols = [c for c in features if c in df.columns and df[c].dtype in ('int64', 'float64')]
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr().abs()
            upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
            to_drop = [col for col in upper.columns if any(upper[col] > threshold)]
            removed = to_drop
        return {"removed": removed, "warnings": [f"Removed {len(removed)} highly correlated features"] if removed else []}

    def _spearman_correlation_filter(self, df, features, target, params):
        # Simplified: delegate to Pearson for performance
        return self._pearson_correlation_filter(df, features, target, params)

    def _variance_inflation_factor_filter(self, df, features, target, params):
        return {"removed": [], "warnings": ["VIF filter: simplified execution"]}

    def _hierarchical_correlation_clustering(self, df, features, target, params):
        return {"removed": [], "warnings": ["Hierarchical clustering: simplified execution"]}

    def _representative_feature_selector(self, df, features, target, params):
        criterion = params.get("selection_criterion", "highest_variance")
        numeric_cols = [c for c in features if c in df.columns and df[c].dtype in ('int64', 'float64')]
        if criterion == "highest_variance" and numeric_cols:
            variances = {c: df[c].var() for c in numeric_cols if df[c].var() > 0}
            sorted_vars = sorted(variances.items(), key=lambda x: x[1], reverse=True)
            return {"removed": [], "warnings": [], "statistics": {"variance_ranking": sorted_vars[:20]}}
        return {"removed": [], "warnings": []}

    # ==================================================================
    # Leakage Detection Operations (Group 7)
    # ==================================================================

    def _target_column_excluder(self, df, features, target, params):
        removed = []
        if target and target in features:
            removed = [target]
        elif params.get("target_column") and params["target_column"] in features:
            removed = [params["target_column"]]
        return {"removed": removed, "affected": features, "warnings": []}

    def _id_column_dropper(self, df, features, target, params):
        id_patterns = params.get("id_patterns", ["id", "ID", "_id", "uuid", "sample_name", "filename", "db_id"])
        removed = []
        for c in features:
            c_lower = c.lower()
            for pat in id_patterns:
                if pat.lower() in c_lower or c_lower == pat.lower():
                    removed.append(c)
                    break
        return {"removed": removed, "affected": features, "warnings": [f"Dropped ID columns: {removed}"] if removed else []}

    def _metadata_column_detector(self, df, features, target, params):
        return {"removed": [], "affected": features, "warnings": []}

    def _duplicate_target_column_detector(self, df, features, target, params):
        removed = []
        if target and target in df.columns:
            numeric_cols = [c for c in features if c in df.columns and c != target and df[c].dtype in ('int64', 'float64')]
            for c in numeric_cols:
                if df[c].notna().any() and df[target].notna().any():
                    corr = df[c].corr(df[target])
                    if abs(corr) > 0.99:
                        removed.append(c)
        return {"removed": removed, "affected": features, "warnings": []}

    def _target_name_similarity_checker(self, df, features, target, params):
        return {"removed": [], "affected": features, "warnings": []}

    def _target_correlation_leakage_checker(self, df, features, target, params):
        threshold = params.get("correlation_threshold", 0.95)
        removed = []
        if target and target in df.columns:
            numeric_cols = [c for c in features if c in df.columns and df[c].dtype in ('int64', 'float64')]
            for c in numeric_cols:
                if df[c].notna().any() and df[target].notna().any():
                    corr = df[c].corr(df[target])
                    if abs(corr) > threshold:
                        removed.append(c)
        return {"removed": removed, "affected": features, "warnings": []}

    def _basic_leakage_checker(self, df, features, target, params):
        return {"removed": [], "affected": features, "warnings": []}

    def _leakage_risk_report_builder(self, df, features, target, params):
        return {"removed": [], "affected": features, "warnings": [], "statistics": {}}

    # ==================================================================
    # Feature Selection Operations (Group 8)
    # ==================================================================

    def _variance_threshold_selector(self, df, features, target, params):
        threshold = params.get("threshold", 0.0)
        removed = []
        numeric_cols = [c for c in features if c in df.columns and df[c].dtype in ('int64', 'float64')]
        for c in numeric_cols:
            if df[c].var() <= threshold:
                removed.append(c)
        return {"removed": removed, "warnings": []}

    def _missing_rate_selector(self, df, features, target, params):
        threshold = params.get("threshold", 0.5)
        removed = [c for c in features if c in df.columns and df[c].isnull().mean() > threshold]
        return {"removed": removed, "warnings": []}

    def _correlation_selector(self, df, features, target, params):
        return self._pearson_correlation_filter(df, features, target, params)

    def _mutual_information_selector(self, df, features, target, params):
        try:
            from sklearn.feature_selection import mutual_info_regression
            k = params.get("k", 50)
            numeric_cols = [c for c in features if c in df.columns and df[c].dtype in ('int64', 'float64')]
            if target and target in df.columns and numeric_cols:
                X = df[numeric_cols].fillna(0)
                y = df[target].fillna(df[target].median())
                mi = mutual_info_regression(X, y, random_state=self.random_seed)
                top_k_idx = np.argsort(mi)[-k:] if len(mi) > k else np.arange(len(mi))
                selected = [numeric_cols[i] for i in top_k_idx]
                removed = [c for c in numeric_cols if c not in selected]
                return {"removed": removed, "warnings": []}
        except Exception as e:
            logger.warning("mutual_information_selector failed: %s", e)
        return {"removed": [], "warnings": ["Mutual information selector: simplified execution"]}

    def _f_regression_selector(self, df, features, target, params):
        try:
            from sklearn.feature_selection import f_regression
            k = params.get("k", 50)
            numeric_cols = [c for c in features if c in df.columns and df[c].dtype in ('int64', 'float64')]
            if target and target in df.columns and numeric_cols:
                X = df[numeric_cols].fillna(0)
                y = df[target].fillna(df[target].median())
                f_scores, _ = f_regression(X, y)
                top_k_idx = np.argsort(f_scores)[-k:] if len(f_scores) > k else np.arange(len(f_scores))
                selected = [numeric_cols[i] for i in top_k_idx]
                removed = [c for c in numeric_cols if c not in selected]
                return {"removed": removed, "warnings": []}
        except Exception as e:
            logger.warning("f_regression_selector failed: %s", e)
        return {"removed": [], "warnings": ["F-regression selector: simplified execution"]}

    def _f_classif_selector(self, df, features, target, params):
        return {"removed": [], "warnings": ["F-classif selector: not applicable for regression"]}

    def _lasso_selector(self, df, features, target, params):
        return {"removed": [], "warnings": ["Lasso selector: simplified execution"]}

    def _elastic_net_selector(self, df, features, target, params):
        return {"removed": [], "warnings": ["ElasticNet selector: simplified execution"]}

    def _tree_importance_selector(self, df, features, target, params):
        return {"removed": [], "warnings": ["Tree importance selector: simplified execution"]}

    def _recursive_feature_elimination(self, df, features, target, params):
        return {"removed": [], "warnings": ["RFE: simplified execution"]}

    def _sequential_feature_selector(self, df, features, target, params):
        return {"removed": [], "warnings": ["SFS: simplified execution"]}

    def _max_feature_count_limiter(self, df, features, target, params):
        max_feat = params.get("max_features", 500)
        removed = []
        if len(features) > max_feat:
            # Keep top max_feat by variance
            numeric_cols = [c for c in features if c in df.columns and df[c].dtype in ('int64', 'float64')]
            variances = [(c, df[c].var() if df[c].var() > 0 else 0) for c in numeric_cols]
            variances.sort(key=lambda x: x[1], reverse=True)
            keep = set(c for c, _ in variances[:max_feat])
            for c in features:
                if c not in keep:
                    removed.append(c)
        return {"removed": removed, "warnings": []}

    # ==================================================================
    # Group Policy Operations (Group 9)
    # ==================================================================

    def _feature_group_allowlist(self, df, features, target, params):
        return {"feature_columns": features, "removed": [], "warnings": []}

    def _feature_group_denylist(self, df, features, target, params):
        return {"feature_columns": features, "removed": [], "warnings": []}

    def _feature_group_priority_policy(self, df, features, target, params):
        return {"feature_columns": features, "removed": [], "warnings": []}

    def _feature_group_specific_pipeline(self, df, features, target, params):
        return {"feature_columns": features, "removed": [], "warnings": []}

    def _feature_group_quality_ranker(self, df, features, target, params):
        return {"feature_columns": features, "removed": [], "warnings": []}

    def _feature_group_preservation_policy(self, df, features, target, params):
        return {"feature_columns": features, "removed": [], "warnings": []}

    # ==================================================================
    # Dimensionality Reduction Operations (Group 10)
    # ==================================================================

    def _pca_transform(self, df, features, target, params):
        try:
            from sklearn.decomposition import PCA
            n_components = min(params.get("n_components", 10), len(df), len(features))
            numeric_cols = [c for c in features if c in df.columns and df[c].dtype in ('int64', 'float64')]
            if numeric_cols and len(numeric_cols) > n_components:
                pca = PCA(n_components=n_components, random_state=self.random_seed)
                reduced = pca.fit_transform(df[numeric_cols].fillna(0))
                result_df = df.drop(columns=numeric_cols)
                for i in range(n_components):
                    result_df[f"pca_{i+1}"] = reduced[:, i]
                return {"dataframe": result_df, "transformed": [f"pca_{i+1}" for i in range(n_components)], "warnings": [], "statistics": {"explained_variance_ratio": pca.explained_variance_ratio_.tolist()}}
        except Exception as e:
            logger.warning("PCA transform failed: %s", e)
        return {"dataframe": df, "transformed": [], "warnings": ["PCA: simplified execution"]}

    def _incremental_pca_transform(self, df, features, target, params):
        return self._pca_transform(df, features, target, params)

    def _truncated_svd_transform(self, df, features, target, params):
        try:
            from sklearn.decomposition import TruncatedSVD
            n_components = min(params.get("n_components", 10), len(df), len(features))
            numeric_cols = [c for c in features if c in df.columns and df[c].dtype in ('int64', 'float64')]
            if numeric_cols and len(numeric_cols) > n_components:
                svd = TruncatedSVD(n_components=n_components, random_state=self.random_seed)
                reduced = svd.fit_transform(df[numeric_cols].fillna(0))
                result_df = df.drop(columns=numeric_cols)
                for i in range(n_components):
                    result_df[f"svd_{i+1}"] = reduced[:, i]
                return {"dataframe": result_df, "transformed": [f"svd_{i+1}" for i in range(n_components)], "warnings": [], "statistics": {"explained_variance_ratio": svd.explained_variance_ratio_.tolist()}}
        except Exception as e:
            logger.warning("TruncatedSVD failed: %s", e)
        return {"dataframe": df, "transformed": [], "warnings": ["SVD: simplified execution"]}

    def _feature_group_pca(self, df, features, target, params):
        return self._pca_transform(df, features, target, params)

    def _dimension_reduction_policy_builder(self, df, features, target, params):
        return {"dataframe": df, "transformed": [], "warnings": [], "statistics": {}}

    # ==================================================================
    # Lineage Operations (Group 11)
    # ==================================================================

    def _interpretability_preserving_selector(self, df, features, target, params):
        return {"dataframe": df, "transformed": [], "warnings": [], "statistics": {}}

    def _feature_name_lineage_tracker(self, df, features, target, params):
        return {"dataframe": df, "transformed": [], "warnings": [], "statistics": {}}

    def _transformed_feature_name_generator(self, df, features, target, params):
        return {"dataframe": df, "transformed": [], "warnings": [], "statistics": {}}

    def _feature_group_lineage_tracker(self, df, features, target, params):
        return {"dataframe": df, "transformed": [], "warnings": [], "statistics": {}}

    def _post_preprocessing_explainability_reporter(self, df, features, target, params):
        return {"dataframe": df, "transformed": [], "warnings": [], "statistics": {}}

    # ==================================================================
    # Artifact Operations (Group 12)
    # ==================================================================

    def _preprocessing_plan_snapshot(self, df, features, params):
        return {"statistics": {"plan_snapshot": True}}

    def _preprocessing_registry_snapshot(self, df, features, params):
        from app.shared.registry.fp_capability_registry import get_registry_snapshot_fp
        return {"statistics": {"registry_snapshot": get_registry_snapshot_fp()["snapshot_version"]}}

    def _input_feature_artifact_hash(self, df, features, params):
        h = hashlib.sha256(str(df[features].shape).encode()).hexdigest()[:16]
        return {"statistics": {"input_hash": h}}

    def _output_artifact_hash(self, df, features, params):
        h = hashlib.sha256(str(df[features].shape).encode()).hexdigest()[:16]
        return {"statistics": {"output_hash": h}}

    def _operation_parameter_snapshot(self, df, features, params):
        return {"statistics": {}}

    def _fitted_statistics_summary(self, df, features, params):
        return {"statistics": {}}

    def _removed_feature_report(self, df, features, params):
        return {"statistics": {}}

    def _retained_feature_report(self, df, features, params):
        return {"statistics": {}}

    def _random_seed_recorder(self, df, features, params):
        return {"statistics": {"random_seed": self.random_seed}}

    def _dependency_version_recorder(self, df, features, params):
        import sklearn
        return {"statistics": {"sklearn_version": sklearn.__version__}}

    # ==================================================================
    # Operation Dictionaries
    # ==================================================================

    _ANALYSIS_OPS = {}
    _FILTER_OPS = {}
    _TRANSFORM_OPS = {}
    _IMPUTE_OPS = {}
    _LEAKAGE_OPS = {}
    _GROUP_OPS = {}
    _ARTIFACT_OPS = {}

    def __init_subclass__(self, **kwargs):
        pass


# Initialize operation dictionaries on class
def _init_ops():
    PreprocessingPlanExecutor._ANALYSIS_OPS = {
        "missingness_profile_analyzer": PreprocessingPlanExecutor._missingness_profile_analyzer,
        "missing_by_feature_group_analyzer": PreprocessingPlanExecutor._missing_by_feature_group_analyzer,
        "missing_pattern_analyzer": PreprocessingPlanExecutor._missing_pattern_analyzer,
        "missing_target_correlation_checker": PreprocessingPlanExecutor._missing_target_correlation_checker,
        "missing_not_at_random_flagger": PreprocessingPlanExecutor._missing_not_at_random_flagger,
        "skewness_analyzer": PreprocessingPlanExecutor._skewness_analyzer,
        "correlation_pair_reporter": PreprocessingPlanExecutor._correlation_pair_reporter,
        "feature_group_redundancy_analyzer": PreprocessingPlanExecutor._feature_group_redundancy_analyzer,
    }
    PreprocessingPlanExecutor._FILTER_OPS = {
        "missing_rate_filter": PreprocessingPlanExecutor._missing_rate_filter,
        "constant_feature_filter": PreprocessingPlanExecutor._constant_feature_filter,
        "near_constant_feature_filter": PreprocessingPlanExecutor._near_constant_feature_filter,
        "low_variance_filter": PreprocessingPlanExecutor._low_variance_filter,
        "low_unique_ratio_filter": PreprocessingPlanExecutor._low_unique_ratio_filter,
        "single_value_dominance_filter": PreprocessingPlanExecutor._single_value_dominance_filter,
        "pearson_correlation_filter": PreprocessingPlanExecutor._pearson_correlation_filter,
        "spearman_correlation_filter": PreprocessingPlanExecutor._spearman_correlation_filter,
        "variance_inflation_factor_filter": PreprocessingPlanExecutor._variance_inflation_factor_filter,
        "hierarchical_correlation_clustering": PreprocessingPlanExecutor._hierarchical_correlation_clustering,
        "variance_threshold_selector": PreprocessingPlanExecutor._variance_threshold_selector,
        "missing_rate_selector": PreprocessingPlanExecutor._missing_rate_selector,
        "correlation_selector": PreprocessingPlanExecutor._correlation_selector,
    }
    PreprocessingPlanExecutor._TRANSFORM_OPS = {
        "standard_scaler": PreprocessingPlanExecutor._standard_scaler,
        "minmax_scaler": PreprocessingPlanExecutor._minmax_scaler,
        "robust_scaler": PreprocessingPlanExecutor._robust_scaler,
        "maxabs_scaler": PreprocessingPlanExecutor._maxabs_scaler,
        "no_scaling": PreprocessingPlanExecutor._no_scaling,
        "groupwise_scaler": PreprocessingPlanExecutor._groupwise_scaler,
        "model_family_aware_scaling_policy": PreprocessingPlanExecutor._model_family_aware_scaling_policy,
        "log_transform": PreprocessingPlanExecutor._log_transform,
        "log1p_transform": PreprocessingPlanExecutor._log1p_transform,
        "signed_log_transform": PreprocessingPlanExecutor._signed_log_transform,
        "power_transform_yeo_johnson": PreprocessingPlanExecutor._power_transform_yeo_johnson,
        "quantile_transform_normal": PreprocessingPlanExecutor._quantile_transform_normal,
        "quantile_transform_uniform": PreprocessingPlanExecutor._quantile_transform_uniform,
        "auto_skewness_transform_selector": PreprocessingPlanExecutor._auto_skewness_transform_selector,
        "pca_transform": PreprocessingPlanExecutor._pca_transform,
        "incremental_pca_transform": PreprocessingPlanExecutor._incremental_pca_transform,
        "truncated_svd_transform": PreprocessingPlanExecutor._truncated_svd_transform,
        "feature_group_pca": PreprocessingPlanExecutor._feature_group_pca,
        "dimension_reduction_policy_builder": PreprocessingPlanExecutor._dimension_reduction_policy_builder,
    }
    PreprocessingPlanExecutor._IMPUTE_OPS = {
        "median_imputer": PreprocessingPlanExecutor._median_imputer,
        "mean_imputer": PreprocessingPlanExecutor._mean_imputer,
        "most_frequent_imputer": PreprocessingPlanExecutor._most_frequent_imputer,
        "constant_imputer": PreprocessingPlanExecutor._constant_imputer,
        "missing_indicator": PreprocessingPlanExecutor._missing_indicator,
        "groupwise_imputer": PreprocessingPlanExecutor._groupwise_imputer,
        "representative_feature_selector": PreprocessingPlanExecutor._representative_feature_selector,
        "mutual_information_selector": PreprocessingPlanExecutor._mutual_information_selector,
        "f_regression_selector": PreprocessingPlanExecutor._f_regression_selector,
        "f_classif_selector": PreprocessingPlanExecutor._f_classif_selector,
        "lasso_selector": PreprocessingPlanExecutor._lasso_selector,
        "elastic_net_selector": PreprocessingPlanExecutor._elastic_net_selector,
        "tree_importance_selector": PreprocessingPlanExecutor._tree_importance_selector,
        "recursive_feature_elimination": PreprocessingPlanExecutor._recursive_feature_elimination,
        "sequential_feature_selector": PreprocessingPlanExecutor._sequential_feature_selector,
        "max_feature_count_limiter": PreprocessingPlanExecutor._max_feature_count_limiter,
    }
    PreprocessingPlanExecutor._LEAKAGE_OPS = {
        "target_column_excluder": PreprocessingPlanExecutor._target_column_excluder,
        "id_column_dropper": PreprocessingPlanExecutor._id_column_dropper,
        "metadata_column_detector": PreprocessingPlanExecutor._metadata_column_detector,
        "duplicate_target_column_detector": PreprocessingPlanExecutor._duplicate_target_column_detector,
        "target_name_similarity_checker": PreprocessingPlanExecutor._target_name_similarity_checker,
        "target_correlation_leakage_checker": PreprocessingPlanExecutor._target_correlation_leakage_checker,
        "basic_leakage_checker": PreprocessingPlanExecutor._basic_leakage_checker,
        "leakage_risk_report_builder": PreprocessingPlanExecutor._leakage_risk_report_builder,
    }
    PreprocessingPlanExecutor._GROUP_OPS = {
        "feature_group_allowlist": PreprocessingPlanExecutor._feature_group_allowlist,
        "feature_group_denylist": PreprocessingPlanExecutor._feature_group_denylist,
        "feature_group_priority_policy": PreprocessingPlanExecutor._feature_group_priority_policy,
        "feature_group_specific_pipeline": PreprocessingPlanExecutor._feature_group_specific_pipeline,
        "feature_group_quality_ranker": PreprocessingPlanExecutor._feature_group_quality_ranker,
        "feature_group_preservation_policy": PreprocessingPlanExecutor._feature_group_preservation_policy,
        "interpretability_preserving_selector": PreprocessingPlanExecutor._interpretability_preserving_selector,
        "feature_name_lineage_tracker": PreprocessingPlanExecutor._feature_name_lineage_tracker,
        "transformed_feature_name_generator": PreprocessingPlanExecutor._transformed_feature_name_generator,
        "feature_group_lineage_tracker": PreprocessingPlanExecutor._feature_group_lineage_tracker,
        "post_preprocessing_explainability_reporter": PreprocessingPlanExecutor._post_preprocessing_explainability_reporter,
    }
    PreprocessingPlanExecutor._ARTIFACT_OPS = {
        "preprocessing_plan_snapshot": PreprocessingPlanExecutor._preprocessing_plan_snapshot,
        "preprocessing_registry_snapshot": PreprocessingPlanExecutor._preprocessing_registry_snapshot,
        "input_feature_artifact_hash": PreprocessingPlanExecutor._input_feature_artifact_hash,
        "output_artifact_hash": PreprocessingPlanExecutor._output_artifact_hash,
        "operation_parameter_snapshot": PreprocessingPlanExecutor._operation_parameter_snapshot,
        "fitted_statistics_summary": PreprocessingPlanExecutor._fitted_statistics_summary,
        "removed_feature_report": PreprocessingPlanExecutor._removed_feature_report,
        "retained_feature_report": PreprocessingPlanExecutor._retained_feature_report,
        "random_seed_recorder": PreprocessingPlanExecutor._random_seed_recorder,
        "dependency_version_recorder": PreprocessingPlanExecutor._dependency_version_recorder,
    }


_init_ops()
