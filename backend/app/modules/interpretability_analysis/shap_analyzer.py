import logging
from typing import Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from app.modules.interpretability_analysis.schemas import (
    ShapSummary, TopShapFeature, ShapArtifactPaths,
    GlobalFeatureImportanceItem,
)
from app.modules.interpretability_analysis.enums import ImportanceMethod, ImportanceDirection
from app.modules.interpretability_analysis.exceptions import ShapCalculationException

logger = logging.getLogger(__name__)


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

    n_samples = min(len(X), max_samples)
    X_sample = X.head(n_samples) if len(X) > n_samples else X

    try:
        explainer = _create_explainer(model, X, explainer_type, background_sample_size)
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
