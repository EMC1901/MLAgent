import logging
from typing import Any, List
import numpy as np

from app.modules.interpretability_analysis.schemas import GlobalFeatureImportanceItem
from app.modules.interpretability_analysis.enums import ImportanceMethod, ImportanceDirection

logger = logging.getLogger(__name__)


def compute_native_importance(
    model: Any,
    feature_columns: List[str],
) -> List[GlobalFeatureImportanceItem]:
    items: List[GlobalFeatureImportanceItem] = []
    importances = _extract_native_importance(model)

    if importances is None or len(importances) == 0:
        logger.warning("Could not extract native feature importance from model.")
        return items

    n_features = min(len(importances), len(feature_columns))
    pairs = list(zip(feature_columns[:n_features], importances[:n_features]))
    pairs.sort(key=lambda x: x[1], reverse=True)

    for rank, (name, imp) in enumerate(pairs, start=1):
        items.append(GlobalFeatureImportanceItem(
            feature_name=name,
            importance_value=float(imp),
            importance_rank=rank,
            importance_method=ImportanceMethod.NATIVE,
            direction=ImportanceDirection.UNKNOWN,
            feature_group="other",
            interpretation_hint="Native importance from tree-based model.",
        ))

    logger.info("Computed native importance for %d features.", len(items))
    return items


def _extract_native_importance(model: Any):
    try:
        if hasattr(model, "feature_importances_"):
            return np.asarray(model.feature_importances_).flatten()
        if hasattr(model, "named_steps"):
            for _, step in model.named_steps.items():
                if hasattr(step, "feature_importances_"):
                    return np.asarray(step.feature_importances_).flatten()
    except Exception as e:
        logger.error("Failed to extract native importance: %s", str(e))
    return None
