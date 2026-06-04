import logging
from typing import Any, List
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance

from app.modules.interpretability_analysis.schemas import GlobalFeatureImportanceItem, PermutationImportanceResult
from app.modules.interpretability_analysis.enums import ImportanceMethod, ImportanceDirection

logger = logging.getLogger(__name__)


def compute_permutation_importance(
    model: Any,
    X: pd.DataFrame,
    y: pd.Series,
    feature_columns: List[str],
    n_repeats: int = 10,
    scoring: str = "neg_mean_squared_error",
) -> List[PermutationImportanceResult]:
    import time
    logger.info("Permutation importance — %d features, %d repeats, scoring=%s",
                 len(feature_columns), n_repeats, scoring)
    t0 = time.time()
    try:
        result = permutation_importance(
            model, X, y,
            n_repeats=n_repeats,
            random_state=42,
            scoring=scoring,
            n_jobs=-1,
        )
    except Exception as e:
        logger.error("Permutation importance computation failed: %s", str(e))
        raise

    items = []
    n_features = min(len(result.importances_mean), len(feature_columns))
    for i in range(n_features):
        items.append(PermutationImportanceResult(
            feature_name=feature_columns[i],
            importance_mean=float(result.importances_mean[i]),
            importance_std=float(result.importances_std[i]),
            rank=0,
            n_repeats=n_repeats,
        ))

    items.sort(key=lambda x: x.importance_mean, reverse=True)
    for rank, item in enumerate(items, start=1):
        item.rank = rank

    logger.info("Permutation importance done — %d features in %.1fs", len(items), time.time() - t0)
    return items


def build_global_importance_from_permutation(
    perm_results: List[PermutationImportanceResult],
) -> List[GlobalFeatureImportanceItem]:
    items = []
    for pr in perm_results:
        direction = ImportanceDirection.POSITIVE if pr.importance_mean > 0 else ImportanceDirection.UNKNOWN
        items.append(GlobalFeatureImportanceItem(
            feature_name=pr.feature_name,
            importance_value=pr.importance_mean,
            importance_rank=pr.rank,
            importance_method=ImportanceMethod.PERMUTATION,
            direction=direction,
            feature_group="other",
            interpretation_hint="Permutation importance measures performance drop when feature is shuffled.",
        ))
    return items
