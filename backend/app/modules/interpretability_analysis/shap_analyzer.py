import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from app.modules.interpretability_analysis.schemas import (
    ShapSummary, TopShapFeature, ShapArtifactPaths,
    GlobalFeatureImportanceItem,
)
from app.modules.interpretability_analysis.enums import ImportanceMethod, ImportanceDirection
from app.modules.interpretability_analysis.exceptions import ShapCalculationException
from app.modules.feature_engineering.feature_matrix_builder import _normalize_bool_columns

logger = logging.getLogger(__name__)


def _get_model_training_features(model: Any) -> Optional[List[str]]:
    """Extract the ordered feature list the model was trained on.

    Supports LightGBM (feature_name_), sklearn (feature_names_in_), and
    XGBoost (feature_names_ / feature_names_in_).
    """
    for attr in ("feature_name_", "feature_names_in_"):
        names = getattr(model, attr, None)
        if names is not None:
            return list(names)
    return None


def compute_shap(
    model: Any,
    X: pd.DataFrame,
    feature_columns: List[str],
    explainer_type: str = "tree",
    background_sample_size: int = 100,
    max_samples: int = 200,
) -> Tuple[ShapSummary, Optional[np.ndarray], List[str]]:
    warnings_list: list = []

    try:
        import shap
    except ImportError:
        msg = "SHAP library is not installed. Falling back to permutation importance."
        logger.warning(msg)
        return _fallback_shap_summary(), None, [msg]

    logger.info("SHAP: X_shape=%s n_features=%d max_samples=%d explainer=%s",
                X.shape, len(feature_columns), max_samples, explainer_type)

    # ── Resolve the feature list the model was actually trained on ──
    train_features = _get_model_training_features(model)

    n_samples = min(len(X), max_samples)
    X_sample = X.head(n_samples) if len(X) > n_samples else X

    # ── 1. Convert boolean-like columns to float64 ─────────────────────
    _normalize_bool_columns(X)
    _normalize_bool_columns(X_sample)

    # ── 2. Check for remaining non-numeric columns ─────────────────────
    remaining_non_numeric = X.select_dtypes(exclude=["number"]).columns.tolist()
    if remaining_non_numeric:
        if train_features is not None:
            critical = [c for c in remaining_non_numeric if c in train_features]
        else:
            # Without train_features we fall back to the metadata list
            critical = [c for c in remaining_non_numeric if c in feature_columns]

        if critical:
            msg = (
                f"SHAP aborted: {len(critical)} training feature(s) are non-numeric "
                f"and could not be converted: {critical}. "
                f"SHAP input must match model training input exactly."
            )
            logger.error(msg)
            return ShapSummary(
                shap_available=False,
                explainer_type="",
                n_samples_explained=0,
                top_shap_features=[],
                shap_artifact_paths=None,
                warnings=[msg],
            ), None, [msg]

        # Non-critical non-numeric columns (not in training features) —
        # safe to drop.
        logger.warning(
            "Dropping non-numeric columns not in training features: %s",
            remaining_non_numeric,
        )
        X = X.drop(columns=remaining_non_numeric)
        X_sample = X_sample.drop(columns=remaining_non_numeric)
        feature_columns = [c for c in feature_columns if c not in remaining_non_numeric]

    X = X.astype(float)
    X_sample = X_sample.astype(float)

    # ── 2.5  Normalise column names to match LightGBM convention ──────
    # LightGBM internally replaces spaces with underscores in feature_name_.
    # Normalise X.columns the same way so alignment succeeds for columns
    # whose names contain spaces (e.g. matminer "compound possible").
    X.columns = [c.replace(" ", "_") for c in X.columns]
    X_sample.columns = [c.replace(" ", "_") for c in X_sample.columns]
    feature_columns = [c.replace(" ", "_") for c in feature_columns]

    # ── 3. Align X columns with model training features ────────────────
    if train_features is not None:
        # Normalise to the same convention (defensive — LightGBM already does this)
        train_features = [c.replace(" ", "_") for c in train_features]
        # Keep only columns the model knows about, in training order
        available = [c for c in train_features if c in X.columns]
        missing = [c for c in train_features if c not in X.columns]
        extra = [c for c in X.columns if c not in train_features]

        if missing:
            msg = (
                f"SHAP aborted: X is missing {len(missing)} feature(s) "
                f"that the model was trained on: {missing[:15]}"
            )
            logger.error(msg)
            return ShapSummary(
                shap_available=False,
                explainer_type="",
                n_samples_explained=0,
                top_shap_features=[],
                shap_artifact_paths=None,
                warnings=[msg],
            ), None, [msg]

        if extra:
            logger.info(
                "Dropping %d extra columns not seen during training: %s",
                len(extra), extra[:10],
            )
            warnings_list.append(
                f"Dropped {len(extra)} extra column(s) not in training features: "
                f"{', '.join(extra[:10])}"
            )

        X = X[available]
        X_sample = X_sample[available]
        feature_columns = available

        if list(X.columns) != train_features:
            msg = (
                f"SHAP aborted: X.columns do not match model training features "
                f"after alignment. X has {len(X.columns)} cols, "
                f"model expects {len(train_features)}."
            )
            logger.error(msg)
            return ShapSummary(
                shap_available=False,
                explainer_type="",
                n_samples_explained=0,
                top_shap_features=[],
                shap_artifact_paths=None,
                warnings=[msg],
            ), None, [msg]

    # ── 4. Compute SHAP ────────────────────────────────────────────────
    try:
        explainer = _create_explainer(model, X, explainer_type, background_sample_size)
        try:
            shap_values = explainer(X_sample, check_additivity=False)
        except (TypeError, KeyError):
            shap_values = explainer(X_sample)

        if isinstance(shap_values, list):
            shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        shap_array = np.asarray(shap_values.values if hasattr(shap_values, "values") else shap_values)

        if shap_array.ndim == 3:
            shap_array = shap_array[:, :, 0] if shap_array.shape[2] == 1 else shap_array.mean(axis=-1)

    except Exception as e:
        msg = f"SHAP computation failed: {str(e)}"
        logger.error(msg)
        return _fallback_shap_summary(), None, [msg]

    mean_abs_shap = np.abs(shap_array).mean(axis=0)

    n_features = min(len(mean_abs_shap), len(feature_columns))
    top_features = []
    pairs = list(zip(feature_columns[:n_features], mean_abs_shap[:n_features]))
    pairs.sort(key=lambda x: x[1], reverse=True)
    top_n = min(30, len(pairs))
    for rank, (name, val) in enumerate(pairs[:top_n], start=1):
        direction = "positive_contribution" if val > 0 else "neutral"
        top_features.append(TopShapFeature(
            feature_name=name,
            mean_abs_shap=float(val),
            rank=rank,
            direction_summary=f"mean(|SHAP|) = {val:.4f}, {direction}",
        ))

    summary = ShapSummary(
        shap_available=True,
        explainer_type=explainer_type,
        n_samples_explained=len(X_sample),
        top_shap_features=top_features,
        shap_artifact_paths=None,
        warnings=warnings_list,
    )

    logger.info("SHAP computed for %d samples, %d features.", len(X_sample), len(top_features))
    return summary, shap_array, warnings_list


def build_global_importance_from_shap(
    shap_summary: ShapSummary,
) -> List[GlobalFeatureImportanceItem]:
    items = []
    for tf in shap_summary.top_shap_features:
        items.append(GlobalFeatureImportanceItem(
            feature_name=tf.feature_name,
            importance_value=tf.mean_abs_shap,
            importance_rank=tf.rank,
            importance_method=ImportanceMethod.SHAP,
            direction=ImportanceDirection.NON_MONOTONIC,
            feature_group="other",
            interpretation_hint="Mean absolute SHAP value measures feature impact magnitude.",
        ))
    return items


def _create_explainer(model, X, explainer_type, background_size):
    import shap

    n_bg = min(background_size, len(X))
    bg = X.sample(n=n_bg, random_state=42) if len(X) > n_bg else X

    if explainer_type in ("tree", "tree_explainer"):
        try:
            return shap.TreeExplainer(model, bg, check_additivity=False)
        except TypeError:
            return shap.TreeExplainer(model, bg)
    elif explainer_type in ("linear", "linear_explainer"):
        return shap.LinearExplainer(model, bg)
    else:
        return shap.KernelExplainer(
            model.predict, bg[:min(50, len(bg))]
        )


def _fallback_shap_summary() -> ShapSummary:
    return ShapSummary(
        shap_available=False,
        explainer_type="",
        n_samples_explained=0,
        top_shap_features=[],
        shap_artifact_paths=None,
        warnings=["SHAP unavailable; fallback to permutation importance."],
    )


def compute_shap_interactions(
    shap_values: np.ndarray,
    feature_columns: List[str],
    top_n: int = 10,
) -> List[Dict[str, Any]]:
    """
    Compute SHAP interaction values for top feature pairs.

    SHAP interaction values are approximated via covariance of SHAP values
    across samples: interaction(f_i, f_j) ≈ cov(SHAP_i, SHAP_j) across samples.

    Returns list of top interaction pairs with interaction_strength.
    """
    if shap_values is None or len(feature_columns) < 2:
        return []

    n_features = min(shap_values.shape[1], len(feature_columns))
    names = feature_columns[:n_features]

    interactions = []
    for i in range(n_features):
        for j in range(i + 1, n_features):
            cov = np.cov(shap_values[:, i], shap_values[:, j])[0, 1]
            interaction_strength = float(abs(cov))
            if interaction_strength > 0:
                interactions.append({
                    "feature_1": names[i],
                    "feature_2": names[j],
                    "interaction_strength": round(interaction_strength, 8),
                    "direction": "positive" if cov > 0 else "negative",
                })

    interactions.sort(key=lambda x: x["interaction_strength"], reverse=True)
    logger.info("SHAP interactions computed: %d pairs, returning top %d.", len(interactions), min(top_n, len(interactions)))
    return interactions[:top_n]


def compute_shap_dependence(
    shap_values: np.ndarray,
    X: "pd.DataFrame",
    feature_columns: List[str],
    top_n: int = 10,
) -> List[Dict[str, Any]]:
    """
    Compute SHAP dependence data for top features.

    For each top feature, returns the feature values and corresponding SHAP values,
    plus the most-interacting feature's values for coloring.

    Returns list of {feature_name, feature_values, shap_values, interaction_feature,
    interaction_values}.
    """
    if shap_values is None or X is None or not feature_columns:
        return []

    n_features = min(shap_values.shape[1], len(feature_columns))
    # Select top features by mean abs SHAP
    mean_abs = np.abs(shap_values).mean(axis=0)
    top_indices = np.argsort(mean_abs)[::-1][:min(top_n, n_features)]

    dependence_data = []
    for idx in top_indices:
        name = feature_columns[idx] if idx < len(feature_columns) else f"feature_{idx}"
        feature_vals = X.iloc[:, idx].values if idx < X.shape[1] else np.zeros(shap_values.shape[0])
        shap_vals = shap_values[:, idx]

        # Find most interacting feature
        interaction_scores = []
        for j in range(n_features):
            if j == idx:
                continue
            cov = abs(np.cov(shap_values[:, idx], shap_values[:, j])[0, 1])
            interaction_scores.append((j, cov))
        interaction_scores.sort(key=lambda x: x[1], reverse=True)

        interaction_feature = None
        interaction_values = None
        if interaction_scores:
            j_idx = interaction_scores[0][0]
            if j_idx < X.shape[1]:
                interaction_feature = feature_columns[j_idx] if j_idx < len(feature_columns) else f"feature_{j_idx}"
                interaction_values = X.iloc[:, j_idx].values.tolist()

        dependence_data.append({
            "feature_name": name,
            "feature_values": feature_vals.tolist(),
            "shap_values": shap_vals.tolist(),
            "interaction_feature": interaction_feature,
            "interaction_values": interaction_values,
        })

    logger.info("SHAP dependence data computed for %d features.", len(dependence_data))
    return dependence_data
