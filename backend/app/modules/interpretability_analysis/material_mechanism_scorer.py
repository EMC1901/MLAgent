"""Phase 4: Material Mechanism Scorer.

Scores MaterialMechanismCandidates using the formula from Phase4.md:

  mechanism_score =
      0.30 * source_pattern_scientific_score
    + 0.20 * validation_strength
    + 0.20 * material_semantic_grounding
    + 0.15 * cross_pattern_support
    + 0.10 * physical_prior_consistency
    + 0.05 * actionability
    - counterexample_penalty

Also sets grounding_level based on the quality of material-domain grounding.
"""

import logging
from typing import List, Optional

from app.modules.interpretability_analysis.schemas import (
    MaterialMechanismCandidate,
    MaterialPatternCandidate,
)

logger = logging.getLogger(__name__)

# Weights
W_SOURCE_PATTERN = 0.30
W_VALIDATION = 0.20
W_SEMANTIC_GROUNDING = 0.20
W_CROSS_PATTERN = 0.15
W_PHYSICS_PRIOR = 0.10
W_ACTIONABILITY = 0.05


def score_material_mechanisms(
    mechanisms: List[MaterialMechanismCandidate],
    source_patterns: List[MaterialPatternCandidate],
) -> List[MaterialMechanismCandidate]:
    """Score all material mechanism candidates in-place.

    Args:
        mechanisms: MaterialMechanismCandidates to score.
        source_patterns: Original MaterialPatternCandidates (for cross-referencing).

    Returns:
        The same list with confidence_score and confidence_label updated.
    """
    if not mechanisms:
        return mechanisms

    # Build lookup: pattern_id -> MaterialPatternCandidate
    pattern_map = {p.pattern_id: p for p in source_patterns}

    for mech in mechanisms:
        _score_single_mechanism(mech, pattern_map, mechanisms)

    # Sort by confidence_score descending
    mechanisms.sort(key=lambda m: m.confidence_score, reverse=True)
    return mechanisms


def _score_single_mechanism(
    mechanism: MaterialMechanismCandidate,
    pattern_map: dict,
    all_mechanisms: List[MaterialMechanismCandidate],
) -> None:
    """Score a single MaterialMechanismCandidate in-place."""

    # 1. Source pattern scientific score (0.30)
    source_scores = []
    for pid in mechanism.source_pattern_ids:
        pat = pattern_map.get(pid)
        if pat and pat.scientific_score:
            source_scores.append(pat.scientific_score.total)
        elif pat:
            source_scores.append(pat.confidence_score)
    src_score = _safe_mean(source_scores, 0.3)

    # 2. Validation strength (0.20)
    vs_map = {"pass": 1.0, "weak": 0.6, "fail": 0.2, "not_applicable": 0.5}
    validation_scores = []
    for pv in mechanism.supporting_pattern_validation:
        validation_scores.append(vs_map.get(pv.get("status", ""), 0.3))
    val_score = _safe_mean(validation_scores, 0.3)

    # 3. Material semantic grounding (0.20)
    grounding_order = {
        "externally_validated": 1.0,
        "physics_prior_grounded": 0.7,
        "lineage_grounded": 0.5,
        "descriptor_grounded": 0.25,
    }
    sem_score = grounding_order.get(mechanism.grounding_level, 0.25)

    # 4. Cross-pattern support (0.15)
    cross_score = _compute_cross_pattern_support(mechanism, all_mechanisms)

    # 5. Physical prior consistency (0.10)
    phys_score = _compute_physical_prior_consistency(mechanism)

    # 6. Actionability (0.05)
    actionability_map = {
        "electronic_structure": 0.8,
        "lattice_distortion": 0.7,
        "bonding_strength": 0.7,
        "composition_complexity": 0.6,
        "thermodynamic_stability": 0.9,
        "processing_structure": 0.85,
    }
    actionability = actionability_map.get(mechanism.mechanism_family, 0.5)

    # 7. Counterexample penalty
    counterexample_penalty = min(len(mechanism.counterexamples) * 0.1, 0.3)

    total = (
        W_SOURCE_PATTERN * src_score
        + W_VALIDATION * val_score
        + W_SEMANTIC_GROUNDING * sem_score
        + W_CROSS_PATTERN * cross_score
        + W_PHYSICS_PRIOR * phys_score
        + W_ACTIONABILITY * actionability
        - counterexample_penalty
    )
    total = max(0.0, min(total, 1.0))

    mechanism.confidence_score = round(total, 4)
    mechanism.confidence_label = _label_from_score(total)


def _compute_cross_pattern_support(
    mechanism: MaterialMechanismCandidate,
    all_mechanisms: List[MaterialMechanismCandidate],
) -> float:
    """Measure how many other mechanisms support similar concepts."""
    if len(all_mechanisms) <= 1:
        return 0.3

    my_descriptors = set(mechanism.descriptor_variables)
    my_materials = set(mechanism.material_variables)

    support_count = 0
    for other in all_mechanisms:
        if other.mechanism_id == mechanism.mechanism_id:
            continue
        other_descriptors = set(other.descriptor_variables)
        other_materials = set(other.material_variables)
        if (my_descriptors & other_descriptors) or (my_materials & other_materials):
            support_count += 1

    # Logistic-like saturation
    return min(support_count / 3.0, 1.0)


def _compute_physical_prior_consistency(
    mechanism: MaterialMechanismCandidate,
) -> float:
    """Estimate consistency with known physical priors.

    Currently based on grounding level and mechanism_family coherence.
    """
    if mechanism.grounding_level == "physics_prior_grounded":
        return 0.8
    elif mechanism.grounding_level == "lineage_grounded":
        return 0.6
    elif mechanism.causal_chain and len(mechanism.causal_chain) >= 2:
        return 0.4
    return 0.2


def _safe_mean(values: list, default: float) -> float:
    if not values:
        return default
    return sum(values) / len(values)


def _label_from_score(score: float) -> str:
    if score >= 0.7:
        return "high"
    elif score >= 0.35:
        return "medium"
    return "low"
