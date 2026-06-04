import logging
import numpy as np
from typing import List, Dict, Any
from scipy.stats import spearmanr

logger = logging.getLogger(__name__)


def compute_cross_method_consensus(
    per_method_importance: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Compute rank correlation between importance methods and identify consensus/divergent features.

    Args:
        per_method_importance: Dict mapping method name -> list of {feature_name, importance_value, importance_rank}

    Returns:
        Dict with rank_correlation_matrix, consensus_features, divergent_features, overall_agreement_score
    """
    methods = list(per_method_importance.keys())
    if len(methods) < 2:
        logger.info("Cross-method consensus requires at least 2 methods; got %d.", len(methods))
        return {
            "rank_correlation_matrix": {},
            "consensus_features": [],
            "divergent_features": [],
            "overall_agreement_score": 0.0,
        }

    # Build rank dicts per method: {feature_name: rank}
    method_ranks: Dict[str, Dict[str, int]] = {}
    all_features: set = set()
    for method, items in per_method_importance.items():
        method_ranks[method] = {}
        for item in items:
            name = item.get("feature_name", "")
            rank = item.get("importance_rank", 0)
            if name and rank:
                method_ranks[method][name] = int(rank)
                all_features.add(name)

    if not all_features:
        logger.warning("No features with valid names and ranks found across methods.")
        return {
            "rank_correlation_matrix": {},
            "consensus_features": [],
            "divergent_features": [],
            "overall_agreement_score": 0.0,
        }

    # Compute pairwise Spearman correlation
    corr_matrix: Dict[str, Dict[str, float]] = {}
    spearman_values: List[float] = []
    for m1 in methods:
        corr_matrix[m1] = {}
        for m2 in methods:
            if m1 == m2:
                corr_matrix[m1][m2] = 1.0
                continue
            common = [f for f in all_features if f in method_ranks[m1] and f in method_ranks[m2]]
            if len(common) < 5:
                corr_matrix[m1][m2] = 0.0
                logger.debug("Insufficient common features (%d) between %s and %s; setting correlation to 0.", len(common), m1, m2)
                continue
            ranks1 = [method_ranks[m1][f] for f in common]
            ranks2 = [method_ranks[m2][f] for f in common]
            try:
                rho, _ = spearmanr(ranks1, ranks2)
                corr_matrix[m1][m2] = round(float(rho), 4) if not np.isnan(rho) else 0.0
                if m1 < m2:
                    spearman_values.append(corr_matrix[m1][m2])
            except Exception as e:
                logger.warning("Spearman correlation between %s and %s failed: %s", m1, m2, str(e))
                corr_matrix[m1][m2] = 0.0

    overall_agreement = round(float(np.mean(spearman_values)), 4) if spearman_values else 0.0

    # Identify consensus features: top-10 in ALL methods
    top_n = 10
    top_sets = []
    for method in methods:
        sorted_features = sorted(
            method_ranks[method].keys(),
            key=lambda f: method_ranks[method][f],
        )
        top_sets.append(set(sorted_features[:top_n]))
    consensus_features = sorted(list(set.intersection(*top_sets))) if top_sets else []

    # Identify divergent features: stddev of ranks across methods > threshold
    n_features = len(all_features)
    rank_std_threshold = max(n_features * 0.1, 5.0)
    divergent_features: List[Dict[str, Any]] = []
    for feature in sorted(all_features):
        ranks = []
        for method in methods:
            if feature in method_ranks[method]:
                ranks.append(method_ranks[method][feature])
        if len(ranks) >= 2:
            rank_std = float(np.std(ranks))
            if rank_std > rank_std_threshold:
                divergent_features.append({
                    "feature_name": feature,
                    "method_ranks": {m: method_ranks[m].get(feature, None) for m in methods},
                    "rank_std": round(rank_std, 1),
                })

    divergent_features.sort(key=lambda x: x["rank_std"], reverse=True)
    divergent_features = divergent_features[:10]

    logger.info(
        "Cross-method consensus computed: overall_agreement=%.4f, consensus_features=%d, divergent_features=%d.",
        overall_agreement, len(consensus_features), len(divergent_features),
    )
    return {
        "rank_correlation_matrix": corr_matrix,
        "consensus_features": consensus_features,
        "divergent_features": divergent_features,
        "overall_agreement_score": overall_agreement,
    }
