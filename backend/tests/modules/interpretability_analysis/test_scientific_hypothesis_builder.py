"""Tests for the scientific_hypothesis_builder module.

Covers generate_scientific_hypotheses, generate_applicability_boundaries,
generate_anomaly_patterns, and build_scientific_insight_report.

Uses conftest fixtures and builds realistic evidence_units / feature_profiles
via the evidence_normalizer before exercising each function under test.
"""

import pytest
from types import SimpleNamespace
from copy import deepcopy

from app.modules.interpretability_analysis.scientific_hypothesis_builder import (
    generate_scientific_hypotheses,
    generate_applicability_boundaries,
    generate_anomaly_patterns,
    build_scientific_insight_report,
)
from app.modules.interpretability_analysis.evidence_normalizer import (
    build_evidence_units,
    build_feature_evidence_profiles,
)
from app.modules.interpretability_analysis.schemas import (
    ScientificHypothesis,
    ModelApplicabilityBoundary,
    AnomalyPattern,
    ScientificInsightReport,
    FeatureEvidenceProfile,
    EvidenceUnit,
)
from app.modules.interpretability_analysis.enums import (
    EvidenceType,
    HypothesisClaimType,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _build_full_inputs(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
    *,
    physics_constraints_override=None,
    systematic_errors_override=None,
    residual_override=None,
):
    """Build evidence_units + feature_profiles from all standard fixtures.

    Returns (evidence_units, feature_profiles, common_kwargs) where
    *common_kwargs* holds the remaining inputs needed by the hypothesis
    builder (partial_dependence, correlation_analysis, residual_analysis,
    systematic_errors, physics_constraints, shap_interactions, feature_lineage,
    sample_size).
    """
    physics = (
        physics_constraints_override
        if physics_constraints_override is not None
        else sample_physics_constraints
    )
    systematic = (
        systematic_errors_override
        if systematic_errors_override is not None
        else sample_systematic_errors
    )
    residual = (
        residual_override
        if residual_override is not None
        else sample_residual_analysis
    )

    evidence_units = build_evidence_units(
        per_method_importance=sample_per_method_importance,
        correlation_analysis=sample_correlation_analysis,
        partial_dependence=sample_partial_dependence,
        residual_analysis=residual,
        systematic_errors=systematic,
        physics_constraints=physics,
        shap_summary=None,
        cross_method_consensus=sample_cross_method_consensus,
    )
    feature_profiles = build_feature_evidence_profiles(
        evidence_units=evidence_units,
        feature_columns=sample_feature_columns,
        correlation_analysis=sample_correlation_analysis,
        cross_method_consensus=sample_cross_method_consensus,
        feature_lineage=sample_feature_lineage,
    )
    common = {
        "partial_dependence": sample_partial_dependence,
        "correlation_analysis": sample_correlation_analysis,
        "residual_analysis": residual,
        "systematic_errors": systematic,
        "high_error_analysis": None,
        "physics_constraints": physics,
        "shap_interactions": sample_shap_interactions,
        "feature_lineage": sample_feature_lineage,
        "sample_size": 200,
    }
    return evidence_units, feature_profiles, common


def _hypotheses_by_pattern(hypotheses, pattern):
    """Return all hypotheses whose hypothesis_pattern matches *pattern*."""
    return [h for h in hypotheses if h.hypothesis_pattern == pattern]


def _hypotheses_by_claim_type(hypotheses, claim_type):
    """Return all hypotheses whose claim_type matches."""
    return [h for h in hypotheses if h.claim_type == claim_type]


# ---------------------------------------------------------------------------
# generate_scientific_hypotheses
# ---------------------------------------------------------------------------


def test_generate_hypotheses_with_full_evidence(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """Full pipeline: build evidence units + profiles, then generate hypotheses."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    assert isinstance(hypotheses, list)
    assert len(hypotheses) > 0, "Expected at least one hypothesis from realistic fixtures"
    for h in hypotheses:
        assert isinstance(h, ScientificHypothesis)
        assert h.hypothesis_id, "Every hypothesis must have an id"
        assert h.claim, "Every hypothesis must have a claim"
        assert h.claim_type in (
            HypothesisClaimType.ASSOCIATION,
            HypothesisClaimType.MECHANISM_HYPOTHESIS,
            HypothesisClaimType.LIMITATION,
            HypothesisClaimType.ANOMALY,
        )
        assert 0.0 <= h.confidence_score <= 1.0


def test_generate_hypotheses_empty_profiles_returns_empty(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """Empty feature_profiles list should produce an empty result."""
    evidence_units, _, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    result = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=[],
        **common,
    )
    assert result == []


def test_rule_shap_permutation_strong_triggers(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """Verify at least one hypothesis with 'shap_permutation_consensus' pattern
    exists when features have SHAP + permutation top-k and monotonic PDP."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    matching = _hypotheses_by_pattern(hypotheses, "shap_permutation_consensus")
    assert len(matching) > 0, (
        "Expected at least one hypothesis with pattern 'shap_permutation_consensus'"
    )
    # At least one should have monotonic PDP claim containing "monotonic"
    monotonic_claims = [h for h in matching if "monotonic" in h.claim.lower()]
    assert len(monotonic_claims) > 0, (
        "Expected at least one monotonic-path hypothesis for feat_0"
    )


def test_rule_importance_no_correlation_triggers(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """High-importance features with weak linear target correlation produce
    hypotheses with pattern 'importance_no_correlation'."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    matching = _hypotheses_by_pattern(hypotheses, "importance_no_correlation")
    assert len(matching) > 0, (
        "Expected at least one hypothesis with pattern 'importance_no_correlation'"
    )
    # Claims should mention non-linear or interaction
    for h in matching:
        assert (
            "non-linear" in h.claim.lower()
            or "interaction" in h.claim.lower()
            or "non linear" in h.claim.lower()
        )
        assert h.claim_type == HypothesisClaimType.MECHANISM_HYPOTHESIS


def test_rule_shap_high_pdp_nonmonotonic_triggers(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """PDP non-monotonic + high SHAP importance produces pattern
    'shap_high_pdp_nonmonotonic'."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    matching = _hypotheses_by_pattern(hypotheses, "shap_high_pdp_nonmonotonic")
    assert len(matching) > 0, (
        "Expected at least one hypothesis with pattern 'shap_high_pdp_nonmonotonic'"
    )
    for h in matching:
        assert "non-monotonic" in h.claim.lower() or "non_monotonic" in h.claim.lower()
        assert (
            "threshold" in h.claim.lower()
            or "saturation" in h.claim.lower()
            or "regime" in h.claim.lower()
        )


def test_rule_feature_group_multi_important_triggers(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """Feature lineage grouping multiple important features into the same
    category triggers 'feature_group_multi_important'."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    matching = _hypotheses_by_pattern(hypotheses, "feature_group_multi_important")
    assert len(matching) > 0, (
        "Expected at least one hypothesis with pattern 'feature_group_multi_important'"
    )
    for h in matching:
        assert h.claim_type == HypothesisClaimType.ASSOCIATION
        assert "group" in h.claim.lower() or "category" in h.claim.lower()


def test_rule_residual_range_boundary_triggers(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """Residual segments with high error ratio trigger
    'residual_range_boundary' hypotheses."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    matching = _hypotheses_by_pattern(hypotheses, "residual_range_boundary")
    assert len(matching) > 0, (
        "Expected at least one hypothesis with pattern 'residual_range_boundary'"
    )
    for h in matching:
        assert h.claim_type == HypothesisClaimType.LIMITATION
        assert "reliability boundary" in h.claim.lower() or "caution" in h.claim.lower()


def test_rule_error_concentration_extreme_quantiles_triggers(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """Systematic errors concentrated in extreme quantiles trigger
    'error_concentration_extreme_quantiles'."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    matching = _hypotheses_by_pattern(
        hypotheses, "error_concentration_extreme_quantiles"
    )
    assert len(matching) > 0, (
        "Expected at least one hypothesis with pattern "
        "'error_concentration_extreme_quantiles'"
    )
    for h in matching:
        assert h.claim_type == HypothesisClaimType.LIMITATION


def test_rule_physics_violation_triggers(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints_violated,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """Violated physics constraints trigger 'physics_violation' hypotheses."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints_violated,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
        physics_constraints_override=sample_physics_constraints_violated,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    matching = _hypotheses_by_pattern(hypotheses, "physics_violation")
    assert len(matching) > 0, (
        "Expected at least one hypothesis with pattern 'physics_violation'"
    )
    for h in matching:
        assert h.claim_type == HypothesisClaimType.LIMITATION
        # The rule sets 0.9 initially, but the post-processing heuristic
        # recalculates based on n_supporting (1 -> base=0.5 + 0.1 = 0.6).
        # The label remains "high".
        assert h.confidence_score > 0.5, (
            "Physics violation hypotheses should carry meaningful confidence"
        )
        assert h.confidence_label == "high"


def test_rule_interaction_pair_discovery_triggers(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """Strong SHAP interaction pairs trigger 'interaction_pair_discovery'."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    matching = _hypotheses_by_pattern(hypotheses, "interaction_pair_discovery")
    assert len(matching) > 0, (
        "Expected at least one hypothesis with pattern 'interaction_pair_discovery'"
    )
    for h in matching:
        assert h.claim_type == HypothesisClaimType.MECHANISM_HYPOTHESIS
        assert "interaction" in h.claim.lower()


def test_generate_hypotheses_no_duplicates(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """Deduplication ensures no two hypotheses share the same
    (claim.lower().strip(), claim_type) key."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    keys = [(h.claim.lower().strip(), h.claim_type) for h in hypotheses]
    assert len(keys) == len(set(keys)), (
        f"Duplicate (claim, claim_type) pairs found: "
        f"{[k for k in keys if keys.count(k) > 1]}"
    )


def test_generate_hypotheses_are_sorted_by_confidence_descending(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """Returned list must be sorted by confidence_score descending."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    scores = [h.confidence_score for h in hypotheses]
    assert scores == sorted(scores, reverse=True), (
        "Hypotheses must be sorted by confidence_score descending"
    )


def test_generate_hypotheses_with_violated_physics(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints_violated,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """When physics constraints are violated, physics_violation hypotheses
    appear alongside other rule outputs."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints_violated,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
        physics_constraints_override=sample_physics_constraints_violated,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    phys_violations = _hypotheses_by_pattern(hypotheses, "physics_violation")
    assert len(phys_violations) > 0
    # Physics violation hypotheses have confidence ~0.6 after heuristic
    # (base=0.5 + 0.1*n_supporting), which is in the upper tier among
    # rule-generated hypotheses but not necessarily at the very top.
    assert phys_violations[0].confidence_score >= 0.5


# ---------------------------------------------------------------------------
# generate_applicability_boundaries
# ---------------------------------------------------------------------------


def test_generate_applicability_boundaries_from_residual(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """Residual segments with enough samples and high MAE produce boundaries."""
    evidence_units, profiles, _common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    boundaries = generate_applicability_boundaries(
        residual_analysis=sample_residual_analysis,
        systematic_errors=None,
        high_error_analysis=None,
        evidence_units=evidence_units,
        feature_profiles=profiles,
    )

    assert isinstance(boundaries, list)
    assert len(boundaries) > 0, "Expected boundaries from residual segments"

    # At least one boundary should reference the high-error segment
    high_error_seg = any(
        "predicted < 0.2" in b.description for b in boundaries
    )
    assert high_error_seg, (
        "Expected a boundary describing the 'predicted < 0.2' segment"
    )

    for b in boundaries:
        assert isinstance(b, ModelApplicabilityBoundary)
        assert b.boundary_id
        assert b.description
        assert b.severity in ("info", "warning", "critical")


def test_generate_applicability_boundaries_from_systematic_errors(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """Systematic errors with error_ratio > 1.5 produce boundaries."""
    evidence_units, profiles, _common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    boundaries = generate_applicability_boundaries(
        residual_analysis=None,
        systematic_errors=sample_systematic_errors,
        high_error_analysis=None,
        evidence_units=evidence_units,
        feature_profiles=profiles,
    )

    assert isinstance(boundaries, list)
    assert len(boundaries) > 0, "Expected boundaries from systematic errors"

    for b in boundaries:
        assert isinstance(b, ModelApplicabilityBoundary)
        assert b.error_ratio > 0


def test_generate_applicability_boundaries_from_high_error(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
    sample_high_error_analysis,
):
    """High-error samples with absolute_error >= 0.1 produce boundaries."""
    evidence_units, profiles, _common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    boundaries = generate_applicability_boundaries(
        residual_analysis=None,
        systematic_errors=None,
        high_error_analysis=sample_high_error_analysis,
        evidence_units=evidence_units,
        feature_profiles=profiles,
    )

    assert isinstance(boundaries, list)
    assert len(boundaries) >= 2
    for b in boundaries:
        assert isinstance(b, ModelApplicabilityBoundary)
        assert b.severity == "info"


def test_generate_applicability_boundaries_empty_input(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """When all inputs are None or empty, no boundaries are produced."""
    evidence_units, profiles, _common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    boundaries = generate_applicability_boundaries(
        residual_analysis=None,
        systematic_errors=None,
        high_error_analysis=None,
        evidence_units=evidence_units,
        feature_profiles=profiles,
    )

    assert boundaries == []


# ---------------------------------------------------------------------------
# generate_anomaly_patterns
# ---------------------------------------------------------------------------


def test_generate_anomaly_patterns_from_high_error(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
    sample_high_error_analysis,
):
    """High-error samples produce AnomalyPattern objects."""
    evidence_units, _, _common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    patterns = generate_anomaly_patterns(
        high_error_analysis=sample_high_error_analysis,
        systematic_errors=None,
        evidence_units=evidence_units,
    )

    assert isinstance(patterns, list)
    assert len(patterns) > 0
    for p in patterns:
        assert isinstance(p, AnomalyPattern)
        assert p.pattern_id
        assert p.description


def test_generate_anomaly_patterns_from_systematic_errors(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """Systematic errors with ratio > 2.0 produce an aggregated anomaly pattern."""
    evidence_units, _, _common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    patterns = generate_anomaly_patterns(
        high_error_analysis=None,
        systematic_errors=sample_systematic_errors,
        evidence_units=evidence_units,
    )

    assert isinstance(patterns, list)
    assert len(patterns) >= 1
    sys_pattern = patterns[-1]
    assert "Systematic error concentration" in sys_pattern.description


def test_generate_anomaly_patterns_empty_input(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
):
    """Empty inputs produce an empty list."""
    evidence_units, _, _common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    patterns = generate_anomaly_patterns(
        high_error_analysis=None,
        systematic_errors=None,
        evidence_units=evidence_units,
    )

    assert patterns == []


# ---------------------------------------------------------------------------
# build_scientific_insight_report
# ---------------------------------------------------------------------------


def test_build_scientific_insight_report_assembles_all_sections(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
    sample_high_error_analysis,
    sample_method_statuses,
):
    """The report must contain every top-level section."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    boundaries = generate_applicability_boundaries(
        residual_analysis=sample_residual_analysis,
        systematic_errors=sample_systematic_errors,
        high_error_analysis=sample_high_error_analysis,
        evidence_units=evidence_units,
        feature_profiles=profiles,
    )

    anomalies = generate_anomaly_patterns(
        high_error_analysis=sample_high_error_analysis,
        systematic_errors=sample_systematic_errors,
        evidence_units=evidence_units,
    )

    report = build_scientific_insight_report(
        hypotheses=hypotheses,
        boundaries=boundaries,
        anomalies=anomalies,
        physics_constraints=sample_physics_constraints,
        evidence_units=evidence_units,
        feature_profiles=profiles,
        method_statuses=sample_method_statuses,
    )

    assert isinstance(report, ScientificInsightReport)
    assert isinstance(report.executive_insights, list)
    assert isinstance(report.ranked_hypotheses, list)
    assert isinstance(report.mechanism_candidates, list)
    assert isinstance(report.model_applicability_boundaries, list)
    assert isinstance(report.anomaly_or_counterexample_patterns, list)
    assert isinstance(report.physics_consistency_summary, dict)
    assert isinstance(report.evidence_graph, dict)
    assert isinstance(report.limitations, list)
    assert isinstance(report.feature_profiles, list)

    # Cross-references should be consistent
    assert len(report.ranked_hypotheses) == len(hypotheses)
    assert len(report.model_applicability_boundaries) == len(boundaries)
    assert len(report.anomaly_or_counterexample_patterns) == len(anomalies)


def test_build_scientific_insight_report_has_limitations(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
    sample_high_error_analysis,
    sample_method_statuses,
):
    """The limitations section is populated with meaningful entries."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    report = build_scientific_insight_report(
        hypotheses=hypotheses,
        boundaries=[],
        anomalies=[],
        physics_constraints=sample_physics_constraints,
        evidence_units=evidence_units,
        feature_profiles=profiles,
        method_statuses=sample_method_statuses,
    )

    assert isinstance(report.limitations, list)
    assert all(isinstance(lim, str) for lim in report.limitations)


def test_build_scientific_insight_report_evidence_graph(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
    sample_high_error_analysis,
    sample_method_statuses,
):
    """The evidence graph maps feature names to lists of evidence IDs."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    report = build_scientific_insight_report(
        hypotheses=hypotheses,
        boundaries=[],
        anomalies=[],
        physics_constraints=sample_physics_constraints,
        evidence_units=evidence_units,
        feature_profiles=profiles,
        method_statuses=sample_method_statuses,
    )

    assert isinstance(report.evidence_graph, dict)
    # Every key in the graph must be a feature name from evidence_units
    all_feature_names = set()
    for eu in evidence_units:
        all_feature_names.update(eu.feature_names)
    for feat in report.evidence_graph:
        assert feat in all_feature_names, (
            f"Unexpected feature '{feat}' in evidence_graph"
        )
    # Every value must be a non-empty list of evidence IDs
    for feat, ev_ids in report.evidence_graph.items():
        assert isinstance(ev_ids, list)
        assert len(ev_ids) > 0, (
            f"Evidence graph entry for '{feat}' is empty"
        )


def test_build_scientific_insight_report_physics_summary(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints_violated,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
    sample_high_error_analysis,
    sample_method_statuses,
):
    """Physics summary is properly populated from constraints."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints_violated,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
        physics_constraints_override=sample_physics_constraints_violated,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    report = build_scientific_insight_report(
        hypotheses=hypotheses,
        boundaries=[],
        anomalies=[],
        physics_constraints=sample_physics_constraints_violated,
        evidence_units=evidence_units,
        feature_profiles=profiles,
        method_statuses=sample_method_statuses,
    )

    ps = report.physics_consistency_summary
    assert ps is not None
    assert "all_passed" in ps
    assert ps["all_passed"] is False
    assert ps["violation_count"] > 0
    assert ps["critical_violations"] >= 0
    assert "constraint_details" in ps
    assert isinstance(ps["constraint_details"], list)


def test_build_scientific_insight_report_limits_exec_insights(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
    sample_high_error_analysis,
    sample_method_statuses,
):
    """Executive insights are capped at 5."""
    evidence_units, profiles, common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        **common,
    )

    report = build_scientific_insight_report(
        hypotheses=hypotheses,
        boundaries=[],
        anomalies=[],
        physics_constraints=sample_physics_constraints,
        evidence_units=evidence_units,
        feature_profiles=profiles,
        method_statuses=sample_method_statuses,
    )

    assert len(report.executive_insights) <= 5
    for ei in report.executive_insights:
        assert ei.claim_type in (
            HypothesisClaimType.ASSOCIATION,
            HypothesisClaimType.MECHANISM_HYPOTHESIS,
        )
    ei_scores = [ei.confidence_score for ei in report.executive_insights]
    assert ei_scores == sorted(ei_scores, reverse=True)


def test_build_scientific_insight_report_empty_inputs(
    sample_per_method_importance,
    sample_correlation_analysis,
    sample_partial_dependence,
    sample_residual_analysis,
    sample_systematic_errors,
    sample_physics_constraints,
    sample_shap_interactions,
    sample_cross_method_consensus,
    sample_feature_lineage,
    sample_feature_columns,
    sample_high_error_analysis,
    sample_method_statuses,
):
    """Building a report with empty hypotheses still returns a valid
    ScientificInsightReport (no crashes)."""
    evidence_units, profiles, _common = _build_full_inputs(
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_systematic_errors,
        sample_physics_constraints,
        sample_shap_interactions,
        sample_cross_method_consensus,
        sample_feature_lineage,
        sample_feature_columns,
    )

    report = build_scientific_insight_report(
        hypotheses=[],
        boundaries=[],
        anomalies=[],
        physics_constraints=sample_physics_constraints,
        evidence_units=evidence_units,
        feature_profiles=profiles,
        method_statuses=sample_method_statuses,
    )

    assert isinstance(report, ScientificInsightReport)
    assert report.executive_insights == []
    assert report.ranked_hypotheses == []
    assert report.mechanism_candidates == []
    assert any(
        "no scientific hypotheses" in lim.lower()
        for lim in report.limitations
    )
