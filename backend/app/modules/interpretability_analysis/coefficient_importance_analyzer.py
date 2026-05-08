import logging
from typing import Any, List
import numpy as np
import pandas as pd

from app.modules.interpretability_analysis.schemas import GlobalFeatureImportanceItem
from app.modules.interpretability_analysis.enums import ImportanceMethod, ImportanceDirection

logger = logging.getLogger(__name__)


def compute_coefficient_importance(
    model: Any,
    feature_columns: List[str],
) -> List[GlobalFeatureImportanceItem]:
    items: List[GlobalFeatureImportanceItem] = []

    coefs = _extract_coefficients(model, len(feature_columns))

    if coefs is None:
        logger.warning("Could not extract coefficients from model.")
        return items

    pairs = list(zip(feature_columns, coefs))
    pairs.sort(key=lambda x: abs(x[1]), reverse=True)

    for rank, (name, coef) in enumerate(pairs, start=1):
        direction = ImportanceDirection.POSITIVE if coef > 0 else ImportanceDirection.NEGATIVE
        items.append(GlobalFeatureImportanceItem(
            feature_name=name,
            importance_value=float(abs(coef)),
            importance_rank=rank,
            importance_method=ImportanceMethod.COEFFICIENT,
            direction=direction,
            feature_group="other",
            interpretation_hint="Coefficient magnitude reflects feature contribution strength.",
        ))

    logger.info("Computed coefficient importance for %d features.", len(items))
    return items


def _extract_coefficients(model: Any, n_features: int):
    try:
        if hasattr(model, "coef_"):
            coefs = np.asarray(model.coef_).flatten()
            if len(coefs) == n_features:
                return coefs
            return list(coefs[:n_features]) + [0.0] * max(0, n_features - len(coefs))
        if hasattr(model, "feature_importances_"):
            return np.asarray(model.feature_importances_).flatten()
    except Exception as e:
        logger.error("Failed to extract coefficients: %s", str(e))
    return None
