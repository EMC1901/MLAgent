"""FoldPipelineExecutor — executes fold-level preprocessing inside each CV fold.

Each operation is fit on X_train only, then applied to both X_train and X_val.
This prevents data leakage from validation folds into training statistics.

Supports: imputation, scaling, distribution transforms, feature selection, PCA.
"""
import time
import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
from app.modules.feature_preprocessing.schemas import FoldPipelineSpec

logger = logging.getLogger(__name__)


class FoldPreprocessingError(Exception):
    """Raised when fold-level preprocessing fails with full context."""
    def __init__(self, message: str, trial_id: str = "", fold_index: int = -1,
                 capability_id: str = "", params: dict = None):
        self.trial_id = trial_id
        self.fold_index = fold_index
        self.capability_id = capability_id
        self.params = params or {}
        super().__init__(message)


class FoldPipelineExecutor:
    """Executes FoldPipelineSpec operations inside a CV fold.

    For each fold: fit on X_train only, transform X_train and X_val.
    Uses sklearn-compatible fit/transform interface for consistency.
    """

    def __init__(self, spec: FoldPipelineSpec):
        self.spec = spec
        self.fitted_ops: Dict[str, Any] = {}  # operation_id -> fitted transformer

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit_transform(self, X_train: pd.DataFrame, y_train: Optional[pd.Series] = None,
                      trial_id: str = "", fold_index: int = -1) -> pd.DataFrame:
        """Fit all fold operations on training data, return transformed X_train."""
        t0 = time.time()
        X = X_train.copy()
        n_ops = len(self.spec.operations)
        logger.debug("trial=%s fold=%d — fitting %d fold ops on %d samples (%d cols) ...",
              trial_id, fold_index, n_ops, len(X), len(X.columns))
        for i, op in enumerate(self.spec.operations):
            t_op = time.time()
            try:
                X = self._execute_operation(op, X, y_train, is_fit=True,
                                            trial_id=trial_id, fold_index=fold_index)
                dur = time.time() - t_op
                logger.debug("trial=%s fold=%d op=%d/%d %s: fit OK (%.2fs)",
                      trial_id, fold_index, i + 1, n_ops, op.capability_id, dur)
            except Exception as e:
                logger.error(
                    "[fold-prep] trial=%s fold=%d op=%d/%d %s FAILED: %s | "
                    "X.shape=%s | params=%s",
                    trial_id, fold_index, i + 1, n_ops, op.capability_id,
                    e, X.shape, op.parameters,
                )
                raise FoldPreprocessingError(
                    f"Fold preprocessing failed at op '{op.capability_id}' "
                    f"(trial={trial_id}, fold={fold_index}): {e}",
                    trial_id=trial_id, fold_index=fold_index,
                    capability_id=op.capability_id, params=op.parameters,
                ) from e
        logger.debug("trial=%s fold=%d — %d fold ops fit+transformed in %.2fs",
              trial_id, fold_index, n_ops, time.time() - t0)
        return X

    def transform(self, X: pd.DataFrame, trial_id: str = "",
                  fold_index: int = -1) -> pd.DataFrame:
        """Apply already-fitted operations to validation/test data."""
        X = X.copy()
        for op in self.spec.operations:
            X = self._execute_operation(op, X, y=None, is_fit=False,
                                        trial_id=trial_id, fold_index=fold_index)
        return X

    # ------------------------------------------------------------------
    # Operation dispatch
    # ------------------------------------------------------------------

    _IMPUTER_MAP = {
        "median_imputer": ("SimpleImputer", "median"),
        "mean_imputer": ("SimpleImputer", "mean"),
        "most_frequent_imputer": ("SimpleImputer", "most_frequent"),
        "constant_imputer": ("SimpleImputer", "constant"),
    }

    _SCALER_MAP = {
        "standard_scaler": "StandardScaler",
        "minmax_scaler": "MinMaxScaler",
        "robust_scaler": "RobustScaler",
        "maxabs_scaler": "MaxAbsScaler",
    }

    _TRANSFORM_MAP = {
        "log_transform": "log",
        "log1p_transform": "log1p",
        "signed_log_transform": "signed_log",
        "power_transform_yeo_johnson": "yeo_johnson",
        "quantile_transform_normal": "quantile_normal",
        "quantile_transform_uniform": "quantile_uniform",
    }

    _SELECTOR_MAP = {
        "mutual_information_selector": "mutual_info",
        "f_regression_selector": "f_regression",
        "f_classif_selector": "f_classif",
        "lasso_selector": "lasso",
    }

    def _execute_operation(self, op, X: pd.DataFrame, y: Optional[pd.Series],
                           is_fit: bool, trial_id: str, fold_index: int) -> pd.DataFrame:
        cid = op.capability_id
        params = op.parameters or {}

        # --- Imputation ---
        if cid in self._IMPUTER_MAP:
            return self._apply_imputer(op, X, is_fit, params)

        # --- Scaling ---
        if cid in self._SCALER_MAP:
            return self._apply_scaler(op, X, is_fit, params, cid)

        # --- Distribution transforms ---
        if cid in self._TRANSFORM_MAP:
            return self._apply_distribution_transform(op, X, is_fit, params, cid)

        # --- Feature selection ---
        if cid in self._SELECTOR_MAP:
            return self._apply_selector(op, X, y, is_fit, params, cid)

        # --- Dimensionality reduction ---
        if cid == "pca_transform":
            return self._apply_pca(op, X, is_fit, params)
        if cid == "truncated_svd_transform":
            return self._apply_svd(op, X, is_fit, params)

        # --- Missing indicator (custom) ---
        if cid == "missing_indicator":
            return self._apply_missing_indicator(op, X, is_fit, params)

        # --- Unknown — pass through ---
        logger.debug("trial=%s fold=%d op=%s: unknown capability, passing through",
              trial_id, fold_index, cid)
        return X

    # ------------------------------------------------------------------
    # Imputation
    # ------------------------------------------------------------------

    def _apply_imputer(self, op, X, is_fit, params):
        from sklearn.impute import SimpleImputer
        _, strategy = self._IMPUTER_MAP[op.capability_id]
        target_cols = self._resolve_columns(op, X)
        if not target_cols:
            return X
        imputer_kwargs = {"strategy": strategy}
        if strategy == "constant":
            imputer_kwargs["fill_value"] = params.get("fill_value", 0)
        if is_fit:
            imp = SimpleImputer(**imputer_kwargs)
            X[target_cols] = imp.fit_transform(X[target_cols])
            self.fitted_ops[op.operation_id] = imp
        else:
            imp = self.fitted_ops.get(op.operation_id)
            if imp is None:
                return X
            X[target_cols] = imp.transform(X[target_cols])
        return X

    # ------------------------------------------------------------------
    # Scaling
    # ------------------------------------------------------------------

    def _apply_scaler(self, op, X, is_fit, params, cid):
        scaler_cls = self._get_sklearn_class(self._SCALER_MAP[cid])
        if scaler_cls is None:
            return X
        target_cols = self._resolve_columns(op, X)
        if not target_cols:
            return X
        scaler_kwargs = {}
        if cid == "minmax_scaler":
            fr = params.get("feature_range", (0, 1))
            if isinstance(fr, list):
                fr = tuple(fr)
            scaler_kwargs["feature_range"] = fr
        elif cid == "robust_scaler":
            qr = params.get("quantile_range", (25.0, 75.0))
            if isinstance(qr, list):
                qr = tuple(qr)
            scaler_kwargs["quantile_range"] = qr
        if is_fit:
            scl = scaler_cls(**scaler_kwargs)
            X_arr = scl.fit_transform(X[target_cols])
            X[target_cols] = X_arr
            self.fitted_ops[op.operation_id] = scl
            if target_cols:
                logger.debug("  scaler %s: mean=%.3f std=%.3f (fit on %d samples)",
                      cid, float(np.mean(X_arr)), float(np.std(X_arr)), len(X))
        else:
            scl = self.fitted_ops.get(op.operation_id)
            if scl is None:
                return X
            X[target_cols] = scl.transform(X[target_cols])
        return X

    # ------------------------------------------------------------------
    # Distribution transforms
    # ------------------------------------------------------------------

    def _apply_distribution_transform(self, op, X, is_fit, params, cid):
        transform_type = self._TRANSFORM_MAP[cid]
        target_cols = self._resolve_columns(op, X)
        if not target_cols:
            return X

        if transform_type == "log":
            shift = params.get("shift", 0.0)
            for c in target_cols:
                X[c] = np.log(X[c].clip(lower=-shift + 1e-8) + shift)
        elif transform_type == "log1p":
            for c in target_cols:
                X[c] = np.log1p(X[c].clip(lower=0))
        elif transform_type == "signed_log":
            for c in target_cols:
                X[c] = np.sign(X[c]) * np.log1p(np.abs(X[c]))
        elif transform_type in ("yeo_johnson", "quantile_normal", "quantile_uniform"):
            X = self._apply_sklearn_transform(op, X, is_fit, transform_type, params)
        return X

    def _apply_sklearn_transform(self, op, X, is_fit, transform_type, params):
        from sklearn.preprocessing import PowerTransformer, QuantileTransformer
        target_cols = self._resolve_columns(op, X)
        if not target_cols:
            return X
        if is_fit:
            if transform_type == "yeo_johnson":
                tf = PowerTransformer(method="yeo-johnson")
            elif transform_type == "quantile_normal":
                n_q = min(params.get("n_quantiles", 1000), len(X))
                tf = QuantileTransformer(output_distribution="normal", n_quantiles=n_q)
            elif transform_type == "quantile_uniform":
                n_q = min(params.get("n_quantiles", 1000), len(X))
                tf = QuantileTransformer(output_distribution="uniform", n_quantiles=n_q)
            else:
                return X
            X[target_cols] = tf.fit_transform(X[target_cols])
            self.fitted_ops[op.operation_id] = tf
        else:
            tf = self.fitted_ops.get(op.operation_id)
            if tf is None:
                return X
            X[target_cols] = tf.transform(X[target_cols])
        return X

    # ------------------------------------------------------------------
    # Feature selection
    # ------------------------------------------------------------------

    def _apply_selector(self, op, X, y, is_fit, params, cid):
        from sklearn.feature_selection import SelectKBest, mutual_info_regression, f_regression, f_classif
        from sklearn.feature_selection import SelectFromModel
        from sklearn.linear_model import Lasso
        selector_type = self._SELECTOR_MAP[cid]
        target_cols = self._resolve_columns(op, X)
        if not target_cols:
            return X
        if y is None:
            return X
        k = params.get("k", min(50, len(target_cols)))
        if is_fit:
            score_func = {
                "mutual_info": mutual_info_regression,
                "f_regression": f_regression,
                "f_classif": f_classif,
            }.get(selector_type)
            if selector_type == "lasso":
                alpha = params.get("alpha", 0.01)
                sel = SelectFromModel(Lasso(alpha=alpha, random_state=self.spec.random_seed),
                                      max_features=k)
            elif score_func is not None:
                sel = SelectKBest(score_func=score_func, k=min(k, len(target_cols)))
            else:
                return X
            sel.fit(X[target_cols].fillna(0), y.fillna(y.median() if y.dtype in ('float64', 'int64') else 0))
            self.fitted_ops[op.operation_id] = (sel, target_cols)
            mask = sel.get_support()
            selected_cols = [c for c, m in zip(target_cols, mask) if m]
            logger.debug("  selector %s: %d -> %d features", cid, len(target_cols), len(selected_cols))
            # Drop unselected columns
            removed = [c for c in target_cols if c not in selected_cols]
            if removed:
                X.drop(columns=removed, inplace=True)
                # Keep the column list for transform
                self.fitted_ops[op.operation_id] = (sel, selected_cols, removed)
        else:
            fitted = self.fitted_ops.get(op.operation_id)
            if fitted is None:
                return X
            if len(fitted) == 3:
                sel, selected_cols, removed = fitted
                drop_cols = [c for c in removed if c in X.columns]
                if drop_cols:
                    X.drop(columns=drop_cols, inplace=True)
        return X

    # ------------------------------------------------------------------
    # Dimensionality reduction
    # ------------------------------------------------------------------

    def _apply_pca(self, op, X, is_fit, params):
        from sklearn.decomposition import PCA
        target_cols = self._resolve_columns(op, X)
        if not target_cols or len(target_cols) < 2:
            return X
        n_components = min(params.get("n_components", 10), len(X), len(target_cols))
        if is_fit:
            pca = PCA(n_components=n_components, random_state=self.spec.random_seed)
            reduced = pca.fit_transform(X[target_cols].fillna(0))
            comp_names = [f"pca_{i+1}" for i in range(n_components)]
            X.drop(columns=target_cols, inplace=True)
            for i, name in enumerate(comp_names):
                X[name] = reduced[:, i]
            self.fitted_ops[op.operation_id] = (pca, target_cols, comp_names)
            logger.debug("  pca: %d cols -> %d components (var=%.3f)",
                  len(target_cols), n_components, float(sum(pca.explained_variance_ratio_)))
        else:
            fitted = self.fitted_ops.get(op.operation_id)
            if fitted is None:
                return X
            pca, orig_cols, comp_names = fitted
            for c in orig_cols:
                if c in X.columns:
                    X.drop(columns=[c], inplace=True)
            reduced = pca.transform(X[orig_cols].fillna(0))
            for i, name in enumerate(comp_names):
                X[name] = reduced[:, i]
        return X

    def _apply_svd(self, op, X, is_fit, params):
        from sklearn.decomposition import TruncatedSVD
        target_cols = self._resolve_columns(op, X)
        if not target_cols or len(target_cols) < 2:
            return X
        n_components = min(params.get("n_components", 10), len(X), len(target_cols))
        if is_fit:
            svd = TruncatedSVD(n_components=n_components, random_state=self.spec.random_seed)
            reduced = svd.fit_transform(X[target_cols].fillna(0))
            comp_names = [f"svd_{i+1}" for i in range(n_components)]
            X.drop(columns=target_cols, inplace=True)
            for i, name in enumerate(comp_names):
                X[name] = reduced[:, i]
            self.fitted_ops[op.operation_id] = (svd, target_cols, comp_names)
            logger.debug("  svd: %d cols -> %d components (var=%.3f)",
                  len(target_cols), n_components, float(sum(svd.explained_variance_ratio_)))
        else:
            fitted = self.fitted_ops.get(op.operation_id)
            if fitted is None:
                return X
            svd, orig_cols, comp_names = fitted
            for c in orig_cols:
                if c in X.columns:
                    X.drop(columns=[c], inplace=True)
            reduced = svd.transform(X[orig_cols].fillna(0))
            for i, name in enumerate(comp_names):
                X[name] = reduced[:, i]
        return X

    # ------------------------------------------------------------------
    # Missing indicator
    # ------------------------------------------------------------------

    def _apply_missing_indicator(self, op, X, is_fit, params):
        target_cols = self._resolve_columns(op, X)
        if not target_cols:
            return X
        if is_fit:
            new_cols = []
            for c in target_cols:
                if c in X.columns:
                    ind_name = f"{c}_missing"
                    X[ind_name] = X[c].isnull().astype(int)
                    new_cols.append(ind_name)
            self.fitted_ops[op.operation_id] = new_cols
        else:
            new_cols = self.fitted_ops.get(op.operation_id, [])
            for c in target_cols:
                if c in X.columns:
                    ind_name = f"{c}_missing"
                    if ind_name not in X.columns:
                        X[ind_name] = X[c].isnull().astype(int)
        return X

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_columns(self, op, X: pd.DataFrame) -> list:
        """Determine which columns to operate on, from explicit list or feature groups."""
        if op.target_columns:
            return [c for c in op.target_columns if c in X.columns]
        if op.target_feature_groups:
            # Without group→column mapping, operate on all numeric columns
            pass
        # Default: all numeric columns in X
        return [c for c in X.columns if X[c].dtype in ('int64', 'float64', 'int32', 'float32')]

    @staticmethod
    def _get_sklearn_class(name: str):
        from sklearn.preprocessing import (
            StandardScaler, MinMaxScaler, RobustScaler, MaxAbsScaler,
        )
        mapping = {
            "StandardScaler": StandardScaler,
            "MinMaxScaler": MinMaxScaler,
            "RobustScaler": RobustScaler,
            "MaxAbsScaler": MaxAbsScaler,
        }
        return mapping.get(name)
