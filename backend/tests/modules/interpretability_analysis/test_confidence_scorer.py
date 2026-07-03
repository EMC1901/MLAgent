"""Tests for the confidence_scorer module.

Covers compute_confidence, score_all_hypotheses, _compute_model_perf_reliability,
_compute_sample_support, and _apply_confidence_label.

Uses conftest fixtures and plain pytest functions (no classes).
"""

import math
import pytest
import numpy as np
from types import SimpleNamespace

from app.modules.interpretability_analysis.confidence_scorer import (
    compute_confidence,
    score_all_hypotheses,
    _compute_model_perf_reliability,
    _compute_sample_support,
    _apply_confidence_label,
    W_CROSS_METHOD,
    W_MODEL_PERF,
    W_SAMPLE_SUPPORT,
    W_DIRECTION_CONSISTENCY,
    W_CORRELATION_SUPPORT,
    W_PHYSICS_CONSISTENCY,
    W_CONTRADICTION_PENALTY,
)
from app.modules.interpretability_analysis.schemas import (
    ScientificHypothesis,
    ConfidenceBreakdown,
    EvidenceUnit,
    FeatureEvidenceProfile,
)
from app.modules.interpretability_analysis.enums import (
    EvidenceType,
    HypothesisClaimType,
    ConfidenceTier,
)
from app.modules.interpretability_analysis.evidence_normalizer import (
    build_evidence_units,
    build_feature_evidence_profiles,
)


# ---------------------------------------------------------------------------
# local fixtures / helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_hypothesis():
    """A minimal hypothesis for confidence scoring tests."""
    return ScientificHypothesis(
        hypothesis_id="hyp_test_001",
        claim="Feature feat_0 is strongly associated with the target.",
        claim_type=HypothesisClaimType.ASSOCIATION,
        supporting_evidence_ids=["ev_001", "ev_002"],
        contradicting_evidence_ids=[],
        confidence_score=0.7,
        confidence_label="high",
        hypothesis_pattern="test_pattern",
    )


@pytest.fixture
def sample_evidence_units():
    """Evidence units covering SHAP, permutation, PDP, and correlation for feat_0."""
    return [
        EvidenceUnit(
            evidence_id="ev_001",
            evidence_type=EvidenceType.SHAP_IMPORTANCE,
            feature_names=["feat_0"],
            direction="positive",
            strength=0.8,
            method_name="shap",
            quantitative_summary={
                "importance_rank": 1,
                "importance_value": 0.9,
                "total_features_evaluated": 10,
            },
        ),
        EvidenceUnit(
            evidence_id="ev_002",
            evidence_type=EvidenceType.PERMUTATION_IMPORTANCE,
            feature_names=["feat_0"],
            direction="positive",
            strength=0.75,
            method_name="permutation_importance",
            quantitative_summary={
                "importance_rank": 1,
                "importance_value": 0.08,
                "total_features_evaluated": 10,
                "importance_std": 0.01,
            },
        ),
        EvidenceUnit(
            evidence_id="ev_003",
            evidence_type=EvidenceType.PDP_1D,
            feature_names=["feat_0"],
            direction="positive",
            strength=0.6,
            method_name="partial_dependence",
            quantitative_summary={"trend": "monotonic_increasing"},
        ),
        EvidenceUnit(
            evidence_id="ev_004",
            evidence_type=EvidenceType.CORRELATION_LINEAR,
            feature_names=["feat_0"],
            direction="positive",
            strength=0.7,
            method_name="correlation",
            quantitative_summary={"pearson_r": 0.7, "spearman_rho": 0.65},
        ),
    ]


@pytest.fixture
def sample_feature_profiles(sample_evidence_units):
    """A single FeatureEvidenceProfile for feat_0 with high consensus."""
    return [
        FeatureEvidenceProfile(
            feature_name="feat_0",
            rank_percentile=90.0,
            z_score=0.9,
            top_k_membership={
                "shap": True,
                "permutation_importance": True,
                "coefficient": True,
            },
            consensus_score=1.0,
            direction_consistency=1.0,
            method_agreement={"shap": 0.9, "permutation_importance": 0.8},
            stability_score=0.95,
            redundancy_risk=0.2,
            physical_interpretability_score=0.8,
            evidence_units=sample_evidence_units,
        )
    ]


@pytest.fixture
def sample_model_performance():
    """Standard model performance dict."""
    return {
        "primary_metric": "r2",
        "primary_metric_value": 0.85,
        "r_squared": 0.85,
        "rmse": 0.15,
    }


# ---------------------------------------------------------------------------
# compute_confidence
# ---------------------------------------------------------------------------


def test_compute_confidence_returns_all_components(
    sample_hypothesis,
    sample_evidence_units,
    sample_feature_profiles,
    sample_model_performance,
):
    """Every field in the ConfidenceBreakdown must be populated."""
    breakdown = compute_confidence(
        hypothesis=sample_hypothesis,
        feature_profiles=sample_feature_profiles,
        cross_method_consensus=None,
        model_performance=sample_model_performance,
        sample_size=500,
        physics_consistency_score=1.0,
        evidence_units=sample_evidence_units,
    )

    assert isinstance(breakdown, ConfidenceBreakdown)
    assert breakdown.total_confidence > 0
    assert breakdown.cross_method_agreement is not None
    assert breakdown.model_performance_reliability is not None
    assert breakdown.sample_support is not None
    assert breakdown.pdp_shap_direction_consistency is not None
    assert breakdown.correlation_support is not None
    assert breakdown.physics_consistency is not None
    assert breakdown.contradiction_penalty is not None
    assert breakdown.confidence_label in VALID_CONFIDENCE_TIERS


VALID_CONFIDENCE_TIERS = {
    ConfidenceTier.VERY_LOW,
    ConfidenceTier.LOW,
    ConfidenceTier.MEDIUM,
    ConfidenceTier.HIGH,
    ConfidenceTier.VERY_HIGH,
}


def test_confidence_breakdown_sums_correctly(
    sample_hypothesis,
    sample_evidence_units,
    sample_feature_profiles,
    sample_model_performance,
):
    """The total_confidence must equal the weighted sum of component values
    with the module-level weight constants."""
    breakdown = compute_confidence(
        hypothesis=sample_hypothesis,
        feature_profiles=sample_feature_profiles,
        cross_method_consensus=None,
        model_performance=sample_model_performance,
        sample_size=500,
        physics_consistency_score=1.0,
        evidence_units=sample_evidence_units,
    )

    expected_total = (
        W_CROSS_METHOD * breakdown.cross_method_agreement
        + W_MODEL_PERF * breakdown.model_performance_reliability
        + W_SAMPLE_SUPPORT * breakdown.sample_support
        + W_DIRECTION_CONSISTENCY * breakdown.pdp_shap_direction_consistency
        + W_CORRELATION_SUPPORT * breakdown.correlation_support
        + W_PHYSICS_CONSISTENCY * breakdown.physics_consistency
        - W_CONTRADICTION_PENALTY * breakdown.contradiction_penalty
    )
    expected_total = float(
        np.clip(np.nan_to_num(expected_total, nan=0.5), 0.0, 1.0)
    )

    assert breakdown.total_confidence == pytest.approx(expected_total, abs=1e-4)


def test_confidence_with_high_performance_high_consensus(
    sample_hypothesis,
    sample_evidence_units,
    sample_feature_profiles,
):
    """High R^2 + high cross-method consensus = high total_confidence."""
    breakdown = compute_confidence(
        hypothesis=sample_hypothesis,
        feature_profiles=sample_feature_profiles,
        cross_method_consensus={
            "overall_agreement_score": 0.9,
            "consensus_features": ["feat_0"],
        },
        model_performance={"r_squared": 0.92},
        sample_size=2000,
        physics_consistency_score=1.0,
        evidence_units=sample_evidence_units,
    )

    assert breakdown.total_confidence > 0.6
    assert breakdown.model_performance_reliability > 0.8
    assert breakdown.cross_method_agreement > 0.7
    assert breakdown.confidence_label in (
        ConfidenceTier.HIGH,
        ConfidenceTier.VERY_HIGH,
    )


def test_confidence_with_low_performance(
    sample_hypothesis,
    sample_feature_profiles,
):
    """Low R^2 should drag model_performance_reliability and total down."""
    breakdown = compute_confidence(
        hypothesis=sample_hypothesis,
        feature_profiles=sample_feature_profiles,
        cross_method_consensus=None,
        model_performance={"r_squared": 0.1},
        sample_size=100,
        physics_consistency_score=1.0,
        evidence_units=[],
    )

    assert breakdown.model_performance_reliability < 0.3
    assert breakdown.total_confidence < 0.6


def test_confidence_with_small_sample(
    sample_hypothesis,
    sample_feature_profiles,
):
    """Small sample_size yields low sample_support."""
    breakdown = compute_confidence(
        hypothesis=sample_hypothesis,
        feature_profiles=sample_feature_profiles,
        cross_method_consensus=None,
        model_performance={"r_squared": 0.85},
        sample_size=10,
        physics_consistency_score=1.0,
        evidence_units=[],
    )

    assert breakdown.sample_support < 0.4


def test_confidence_with_large_sample(
    sample_hypothesis,
    sample_feature_profiles,
):
    """Large sample_size yields high sample_support."""
    breakdown = compute_confidence(
        hypothesis=sample_hypothesis,
        feature_profiles=sample_feature_profiles,
        cross_method_consensus=None,
        model_performance={"r_squared": 0.85},
        sample_size=5000,
        physics_consistency_score=1.0,
        evidence_units=[],
    )

    assert breakdown.sample_support > 0.9


# ---------------------------------------------------------------------------
# _compute_model_perf_reliability
# ---------------------------------------------------------------------------


def test_compute_model_perf_reliability_high_r2():
    """R^2 >= 0.8 returns 0.9."""
    assert _compute_model_perf_reliability({"r_squared": 0.85}) == 0.9
    assert _compute_model_perf_reliability({"r_squared": 0.95}) == 0.9
    assert _compute_model_perf_reliability({"r_squared": 0.80}) == 0.9


def test_compute_model_perf_reliability_low_r2():
    """R^2 < 0.2 returns 0.15."""
    assert _compute_model_perf_reliability({"r_squared": 0.1}) == 0.15
    assert _compute_model_perf_reliability({"r_squared": 0.05}) == 0.15
    assert _compute_model_perf_reliability({"r_squared": 0.19}) == 0.15


def test_compute_model_perf_reliability_no_r2():
    """No R^2 key returns neutral 0.5."""
    assert _compute_model_perf_reliability({}) == 0.5
    assert _compute_model_perf_reliability({"primary_metric_value": 0.9}) == 0.5


def test_compute_model_perf_reliability_medium_r2():
    """Verify the intermediate thresholds."""
    assert _compute_model_perf_reliability({"r_squared": 0.7}) == 0.7
    assert _compute_model_perf_reliability({"r_squared": 0.5}) == 0.5
    assert _compute_model_perf_reliability({"r_squared": 0.3}) == 0.3
    assert _compute_model_perf_reliability({"r_squared": 0.2}) == 0.3


# ---------------------------------------------------------------------------
# _compute_sample_support
# ---------------------------------------------------------------------------


def test_compute_sample_support_small():
    """Low sample-to-feature ratio yields low support."""
    score = _compute_sample_support(20, 5)
    assert score < 0.3


def test_compute_sample_support_large():
    """High sample-to-feature ratio yields high support."""
    score = _compute_sample_support(5000, 5)
    assert score > 0.9


def test_compute_sample_support_zero_samples():
    """Zero samples returns 0.0."""
    assert _compute_sample_support(0, 5) == 0.0


def test_compute_sample_support_zero_features():
    """Zero features is treated as 1 feature internally (guard)."""
    score = _compute_sample_support(500, 0)
    assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# contradiction penalty
# ---------------------------------------------------------------------------


def test_contradiction_penalty_zero_when_no_contradictions(
    sample_hypothesis,
    sample_evidence_units,
    sample_feature_profiles,
    sample_model_performance,
):
    """Empty contradicting_evidence_ids produces zero contradiction_penalty."""
    breakdown = compute_confidence(
        hypothesis=sample_hypothesis,
        feature_profiles=sample_feature_profiles,
        cross_method_consensus=None,
        model_performance=sample_model_performance,
        sample_size=500,
        physics_consistency_score=1.0,
        evidence_units=sample_evidence_units,
    )

    assert breakdown.contradiction_penalty == 0.0


def test_contradiction_penalty_with_contradiction(
    sample_evidence_units,
    sample_feature_profiles,
):
    """Contradicting evidence IDs that match real evidence units increase penalty."""
    hyp_with_contra = ScientificHypothesis(
        hypothesis_id="hyp_test_002",
        claim="Test claim with contradictions.",
        claim_type=HypothesisClaimType.ASSOCIATION,
        supporting_evidence_ids=["ev_001"],
        contradicting_evidence_ids=["ev_001", "ev_002"],
        confidence_score=0.5,
    )

    breakdown = compute_confidence(
        hypothesis=hyp_with_contra,
        feature_profiles=sample_feature_profiles,
        cross_method_consensus=None,
        model_performance={"r_squared": 0.85},
        sample_size=500,
        physics_consistency_score=1.0,
        evidence_units=sample_evidence_units,
    )

    assert breakdown.contradiction_penalty > 0
    # 2 valid contradictions * 0.3 = 0.6, capped at 1.0
    assert breakdown.contradiction_penalty == pytest.approx(0.6, abs=0.01)


# ---------------------------------------------------------------------------
# score_all_hypotheses
# ---------------------------------------------------------------------------


def test_score_all_hypotheses_reranks_by_confidence(
    sample_evidence_units,
    sample_feature_profiles,
    sample_model_performance,
):
    """Hypotheses are re-sorted by total_confidence descending after scoring."""
    h1 = ScientificHypothesis(
        hypothesis_id="h1",
        claim="High confidence hypothesis.",
        claim_type=HypothesisClaimType.ASSOCIATION,
        supporting_evidence_ids=["ev_001", "ev_002", "ev_003"],
        contradicting_evidence_ids=[],
    )
    h2 = ScientificHypothesis(
        hypothesis_id="h2",
        claim="Low confidence hypothesis.",
        claim_type=HypothesisClaimType.LIMITATION,
        supporting_evidence_ids=[],
        contradicting_evidence_ids=["ev_001", "ev_002"],
    )

    scored = score_all_hypotheses(
        hypotheses=[h2, h1],
        feature_profiles=sample_feature_profiles,
        cross_method_consensus={
            "overall_agreement_score": 0.85,
        },
        model_performance=sample_model_performance,
        sample_size=500,
        physics_constraints=None,
        evidence_units=sample_evidence_units,
    )

    assert len(scored) == 2
    # h1 has supporting evidence and no contradictions -> higher confidence
    assert scored[0].hypothesis_id == "h1"
    assert scored[0].confidence_score > scored[1].confidence_score
    # Both must have a confidence_breakdown populated
    for h in scored:
        assert h.confidence_breakdown is not None
        assert isinstance(h.confidence_breakdown, ConfidenceBreakdown)


def test_score_all_hypotheses_empty_list():
    """Empty input returns empty list without error."""
    scored = score_all_hypotheses(
        hypotheses=[],
        feature_profiles=[],
        cross_method_consensus=None,
        model_performance={},
        sample_size=100,
        physics_constraints=None,
        evidence_units=[],
    )
    assert scored == []


def test_score_all_hypotheses_populates_breakdowns(
    sample_evidence_units,
    sample_feature_profiles,
    sample_model_performance,
):
    """Every scored hypothesis must have confidence_breakdown and updated
    confidence_score / confidence_label."""
    hypotheses = [
        ScientificHypothesis(
            hypothesis_id=f"h{i}",
            claim=f"Claim {i}",
            claim_type=HypothesisClaimType.ASSOCIATION,
            supporting_evidence_ids=["ev_001"],
            contradicting_evidence_ids=[],
        )
        for i in range(5)
    ]

    scored = score_all_hypotheses(
        hypotheses=hypotheses,
        feature_profiles=sample_feature_profiles,
        cross_method_consensus={
            "overall_agreement_score": 0.7,
        },
        model_performance=sample_model_performance,
        sample_size=200,
        physics_constraints=None,
        evidence_units=sample_evidence_units,
    )

    assert len(scored) == 5
    for h in scored:
        assert h.confidence_score > 0
        assert h.confidence_breakdown is not None
        assert h.confidence_label in VALID_CONFIDENCE_TIERS


# ---------------------------------------------------------------------------
# _apply_confidence_label
# ---------------------------------------------------------------------------


def test_apply_confidence_label_very_high():
    """total >= 0.8 maps to VERY_HIGH."""
    assert _apply_confidence_label(0.80) == ConfidenceTier.VERY_HIGH
    assert _apply_confidence_label(0.85) == ConfidenceTier.VERY_HIGH
    assert _apply_confidence_label(1.0) == ConfidenceTier.VERY_HIGH


def test_apply_confidence_label_very_low():
    """total < 0.2 maps to VERY_LOW."""
    assert _apply_confidence_label(0.0) == ConfidenceTier.VERY_LOW
    assert _apply_confidence_label(0.1) == ConfidenceTier.VERY_LOW
    assert _apply_confidence_label(0.19) == ConfidenceTier.VERY_LOW


def test_apply_confidence_label_boundaries():
    """Verify threshold boundaries for all tiers."""
    assert _apply_confidence_label(0.0) == ConfidenceTier.VERY_LOW
    assert _apply_confidence_label(0.2) == ConfidenceTier.LOW
    assert _apply_confidence_label(0.4) == ConfidenceTier.MEDIUM
    assert _apply_confidence_label(0.6) == ConfidenceTier.HIGH
    assert _apply_confidence_label(0.8) == ConfidenceTier.VERY_HIGH


def test_apply_confidence_label_nan():
    """NaN input defaults to MEDIUM."""
    assert _apply_confidence_label(float("nan")) == ConfidenceTier.MEDIUM
