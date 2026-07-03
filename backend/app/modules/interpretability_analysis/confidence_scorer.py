import logging
import numpy as np
from typing import List, Dict, Any, Optional

from app.modules.interpretability_analysis.schemas import (
    ScientificHypothesis,
    FeatureEvidenceProfile,
    ConfidenceBreakdown,
    EvidenceUnit,
)
from app.modules.interpretability_analysis.enums import (
    EvidenceType,
    ConfidenceTier,
    CONFIDENCE_TIER_THRESHOLDS,
)

logger = logging.getLogger(__name__)

# Weights for the composite confidence score
W_CROSS_METHOD = 0.25
W_MODEL_PERF = 0.20
W_SAMPLE_SUPPORT = 0.15
W_DIRECTION_CONSISTENCY = 0.15
W_CORRELATION_SUPPORT = 0.10
W_PHYSICS_CONSISTENCY = 0.10
W_CONTRADICTION_PENALTY = 0.15  # Subtracted


def compute_confidence(
    hypothesis: ScientificHypothesis,
    feature_profiles: List[FeatureEvidenceProfile],
    cross_method_consensus: Optional[Dict[str, Any]],
    model_performance: Dict[str, Any],
    sample_size: int,
    physics_consistency_score: float,
    evidence_units: List[EvidenceUnit],
) -> ConfidenceBreakdown:
    """Compute a transparent, evidence-based confidence score for a hypothesis.

    Args:
        hypothesis: The hypothesis to score.
        feature_profiles: All feature evidence profiles.
        cross_method_consensus: Cross-method consensus dict.
        model_performance: Dict with primary_metric, primary_metric_value, r_squared, rmse.
        sample_size: Number of samples in the dataset.
        physics_consistency_score: [0, 1] pre-computed physics consistency.
        evidence_units: All evidence units.

    Returns:
        ConfidenceBreakdown with all components and total_confidence.
    """
    # Extract features relevant to this hypothesis from evidence
    relevant_feature_names: List[str] = []
    for eid in hypothesis.supporting_evidence_ids:
        for eu in evidence_units:
            if eu.evidence_id == eid:
                relevant_feature_names.extend(eu.feature_names)
    relevant_feature_names = list(set(relevant_feature_names))

    relevant_profiles = [fp for fp in feature_profiles
                         if fp.feature_name in relevant_feature_names]

    # Component 1: Cross-method agreement (weight: 0.25)
    cross_method = _compute_cross_method_agreement(
        relevant_profiles, cross_method_consensus)
    if cross_method is None:
        cross_method = 0.5
    cross_method = float(np.clip(cross_method, 0.0, 1.0))

    # Component 2: Model performance reliability (weight: 0.20)
    model_perf = _compute_model_perf_reliability(model_performance)
    if model_perf is None:
        model_perf = 0.5
    model_perf = float(np.clip(model_perf, 0.0, 1.0))

    # Component 3: Sample support (weight: 0.15)
    n_features = len(relevant_feature_names) if relevant_feature_names else 1
    sample_support = _compute_sample_support(sample_size, n_features)
    if sample_support is None:
        sample_support = 0.5
    sample_support = float(np.clip(sample_support, 0.0, 1.0))

    # Component 4: PDP-SHAP direction consistency (weight: 0.15)
    dir_consistency = _compute_pdp_shap_dir_consistency(
        relevant_feature_names, evidence_units)
    if dir_consistency is None:
        dir_consistency = 0.5
    dir_consistency = float(np.clip(dir_consistency, 0.0, 1.0))

    # Component 5: Correlation support (weight: 0.10)
    corr_support = _compute_correlation_support(
        relevant_feature_names, evidence_units)
    if corr_support is None:
        corr_support = 0.5
    corr_support = float(np.clip(corr_support, 0.0, 1.0))

    # Component 6: Physics consistency (weight: 0.10)
    phys_consistency = physics_consistency_score if physics_consistency_score is not None else 1.0
    phys_consistency = float(np.clip(phys_consistency, 0.0, 1.0))

    # Component 7: Contradiction penalty (weight: 0.15, subtracted)
    contradiction = _contradiction_penalty(
        hypothesis.contradicting_evidence_ids, evidence_units)
    if contradiction is None:
        contradiction = 0.0
    contradiction = float(np.clip(contradiction, 0.0, 1.0))

    # Composite score
    total = (
        W_CROSS_METHOD * cross_method +
        W_MODEL_PERF * model_perf +
        W_SAMPLE_SUPPORT * sample_support +
        W_DIRECTION_CONSISTENCY * dir_consistency +
        W_CORRELATION_SUPPORT * corr_support +
        W_PHYSICS_CONSISTENCY * phys_consistency -
        W_CONTRADICTION_PENALTY * contradiction
    )

    # Clamp to [0, 1] and handle NaN
    total = float(np.clip(np.nan_to_num(total, nan=0.5), 0.0, 1.0))

    # Determine confidence label
    label = _apply_confidence_label(total)

    return ConfidenceBreakdown(
        cross_method_agreement=round(cross_method, 4),
        model_performance_reliability=round(model_perf, 4),
        sample_support=round(sample_support, 4),
        pdp_shap_direction_consistency=round(dir_consistency, 4),
        correlation_support=round(corr_support, 4),
        physics_consistency=round(phys_consistency, 4),
        contradiction_penalty=round(contradiction, 4),
        total_confidence=round(total, 4),
        confidence_label=label,
    )


def score_all_hypotheses(
    hypotheses: List[ScientificHypothesis],
    feature_profiles: List[FeatureEvidenceProfile],
    cross_method_consensus: Optional[Dict[str, Any]],
    model_performance: Dict[str, Any],
    sample_size: int,
    physics_constraints: Optional[Dict[str, Any]],
    evidence_units: List[EvidenceUnit],
) -> List[ScientificHypothesis]:
    """Compute confidence for each hypothesis, returns re-ranked list.

    Each hypothesis is scored using the composite confidence formula,
    and the list is re-sorted by total_confidence descending.
    Hypotheses get their confidence_breakdown populated for transparency.
    """
    if not hypotheses:
        logger.info("No hypotheses to score.")
        return hypotheses

    # Pre-compute physics consistency score once
    physics_consistency = 1.0
    if physics_constraints:
        try:
            from app.modules.interpretability_analysis.physics_rule_registry import get_registry
            physics_consistency = get_registry().compute_physics_consistency_score(
                physics_constraints)
        except Exception:
            physics_consistency = 1.0
            logger.warning("Failed to compute physics consistency score, defaulting to 1.0")

    scored: List[ScientificHypothesis] = []
    for h in hypotheses:
        try:
            breakdown = compute_confidence(
                hypothesis=h,
                feature_profiles=feature_profiles,
                cross_method_consensus=cross_method_consensus,
                model_performance=model_performance,
                sample_size=sample_size,
                physics_consistency_score=physics_consistency,
                evidence_units=evidence_units,
            )
            h.confidence_score = breakdown.total_confidence
            h.confidence_breakdown = breakdown
            h.confidence_label = breakdown.confidence_label
        except Exception as e:
            logger.warning("Confidence scoring failed for hypothesis '%s': %s",
                           h.hypothesis_id, str(e))
            # Keep the initial heuristic score
        scored.append(h)

    scored.sort(key=lambda h: h.confidence_score, reverse=True)
    logger.info("Scored %d hypotheses; top confidence=%.4f",
                len(scored),
                scored[0].confidence_score if scored else 0.0)
    return scored


def _compute_cross_method_agreement(
    relevant_profiles: List[FeatureEvidenceProfile],
    cross_method_consensus: Optional[Dict[str, Any]],
) -> float:
    """How well do importance methods agree on these features? [0, 1]"""
    if not relevant_profiles:
        return 0.5  # Neutral
    avg_consensus = float(np.mean([fp.consensus_score for fp in relevant_profiles]))
    # Boost if overall cross-method agreement is high
    if cross_method_consensus:
        overall = cross_method_consensus.get("overall_agreement_score", 0.0)
        if overall > 0:
            return 0.5 * avg_consensus + 0.5 * overall
    return avg_consensus


def _compute_model_perf_reliability(
    model_performance: Dict[str, Any],
) -> float:
    """Based on R^2 and primary metric value. [0, 1]"""
    r2 = model_performance.get("r_squared")
    if r2 is not None and not np.isnan(float(r2)):
        r2_val = float(r2)
        if r2_val >= 0.8:
            return 0.9
        elif r2_val >= 0.6:
            return 0.7
        elif r2_val >= 0.4:
            return 0.5
        elif r2_val >= 0.2:
            return 0.3
        else:
            return 0.15

    # Fallback: use primary metric if available
    primary_val = model_performance.get("primary_metric_value")
    if primary_val is not None:
        return 0.5  # Can't judge without context of what "good" means

    return 0.5  # Neutral default


def _compute_sample_support(
    sample_size: int,
    n_features: int,
) -> float:
    """Sample size adequacy for the number of features. [0, 1]

    Uses a logistic curve: the ratio of samples to features determines adequacy.
    """
    if sample_size <= 0:
        return 0.0
    if n_features <= 0:
        n_features = 1
    ratio = sample_size / n_features
    # Logistic: 10:1 -> 0.3, 50:1 -> 0.7, 200:1 -> 0.95
    return float(1.0 / (1.0 + np.exp(-(ratio - 30) / 20)))


def _compute_pdp_shap_dir_consistency(
    feature_names: List[str],
    evidence_units: List[EvidenceUnit],
) -> float:
    """Fraction of features where SHAP direction aligns with PDP trend. [0, 1]"""
    if not feature_names:
        return 0.5

    scores: List[float] = []
    for feat in feature_names:
        feat_units = [eu for eu in evidence_units if feat in eu.feature_names]
        pdp_dir = None
        shap_dir = None
        for eu in feat_units:
            if eu.evidence_type == EvidenceType.PDP_1D:
                pdp_dir = eu.direction
            elif eu.evidence_type == EvidenceType.SHAP_IMPORTANCE:
                shap_dir = eu.direction
        if pdp_dir and shap_dir:
            if pdp_dir == shap_dir:
                scores.append(1.0)
            elif pdp_dir == "non_monotonic" or shap_dir == "non_monotonic":
                scores.append(0.5)  # Partial agreement
            else:
                scores.append(0.0)

    if not scores:
        return 0.5
    return float(np.mean(scores))


def _compute_correlation_support(
    feature_names: List[str],
    evidence_units: List[EvidenceUnit],
) -> float:
    """How strongly do target correlations support importance ranking. [0, 1]"""
    if not feature_names:
        return 0.5

    corr_strengths: List[float] = []
    for feat in feature_names:
        for eu in evidence_units:
            if (eu.evidence_type == EvidenceType.CORRELATION_LINEAR
                    and feat in eu.feature_names):
                corr_strengths.append(eu.strength)

    if not corr_strengths:
        return 0.5
    return float(np.mean(corr_strengths))


def _contradiction_penalty(
    contradicting_evidence_ids: List[str],
    evidence_units: List[EvidenceUnit],
) -> float:
    """Penalty proportional to number and strength of contradicting evidence. [0, 1]"""
    if not contradicting_evidence_ids:
        return 0.0

    penalty = 0.0
    valid_ids = {eu.evidence_id for eu in evidence_units}
    for cid in contradicting_evidence_ids:
        if cid in valid_ids:
            penalty += 0.3  # Each contradiction adds penalty
    return min(penalty, 1.0)


def _apply_confidence_label(total: float) -> str:
    """Map total_confidence to a label."""
    if total is None or np.isnan(total):
        return ConfidenceTier.MEDIUM
    if total < 0.2:
        return ConfidenceTier.VERY_LOW
    if total < 0.4:
        return ConfidenceTier.LOW
    if total < 0.6:
        return ConfidenceTier.MEDIUM
    if total < 0.8:
        return ConfidenceTier.HIGH
    return ConfidenceTier.VERY_HIGH
