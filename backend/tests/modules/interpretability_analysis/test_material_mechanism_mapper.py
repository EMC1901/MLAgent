"""Tests for the Phase 4 material_mechanism_mapper module.

Covers:
- Failed pattern exclusion (all non-boundary types)
- Weak interaction exclusion without 2D PDP
- peak_value=0 detection for 2D PDP
- Lineage family inference priority over registry
- Boundary patterns excluded from mechanisms
- Mechanism statement quality and grounding levels
- Merging of related mechanisms
"""

import pytest
import numpy as np
from app.modules.interpretability_analysis.schemas import (
    MaterialPatternCandidate,
    PatternCondition,
    PatternEffect,
    PatternSampleSupport,
    PatternScientificScore,
    PatternValidationResult,
    MaterialMechanismCandidate,
    EvidenceUnit,
)
from app.modules.interpretability_analysis.material_mechanism_mapper import (
    map_patterns_to_mechanisms,
    _pattern_has_2d_pdp,
    _infer_mechanism_family,
    _ground_feature,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pattern(pattern_type, validation_status, pattern_id=None, conditions=None,
                  confidence_score=0.5, confidence_label="medium",
                  scientific_score_total=0.5, supporting_evidence_ids=None):
    """Build a minimal MaterialPatternCandidate for testing."""
    return MaterialPatternCandidate(
        pattern_id=pattern_id or f"mp_{pattern_type}_{validation_status}",
        pattern_type=pattern_type,
        statement=f"Test {pattern_type} pattern.",
        conditions=conditions or [
            PatternCondition(
                feature_name="feat_x",
                material_concept="test concept",
                operator="between",
                value_range={"min": 0.0, "max": 1.0},
                source="pdp",
            )
        ],
        predicted_effect=PatternEffect(
            target_direction="increases",
            effect_size=0.5,
            effect_unit="pdp_delta",
            evidence_basis="pdp_delta",
        ),
        supporting_evidence_ids=supporting_evidence_ids or ["ev_001"],
        confidence_score=confidence_score,
        confidence_label=confidence_label,
        validation_status=validation_status,
        sample_support=PatternSampleSupport(in_scope_count=30, out_scope_count=20, coverage=0.6),
        validation_results=[
            PatternValidationResult(
                validation_id="val_001", pattern_id=pattern_id or "test",
                validation_type="bootstrap", status=validation_status,
                metrics={}, interpretation="Test validation.",
            )
        ],
        scientific_score=PatternScientificScore(total=scientific_score_total),
        limitations=["Test limitation."],
        validation_suggestions=["Test suggestion."],
    )


# ---------------------------------------------------------------------------
# Test: Failed pattern exclusion (P1)
# ---------------------------------------------------------------------------

class TestFailedPatternExclusion:
    """Failed non-boundary patterns must not become mechanisms."""

    @pytest.mark.parametrize("pattern_type", ["monotonic", "threshold", "window", "interaction"])
    def test_failed_pattern_excluded(self, pattern_type):
        p = _make_pattern(pattern_type, "fail")
        mechanisms = map_patterns_to_mechanisms([p], {}, [], [], None)
        assert len(mechanisms) == 0, f"Failed {pattern_type} should be excluded"

    def test_failed_boundary_still_excluded(self):
        """Boundary patterns are excluded regardless of validation status."""
        p = _make_pattern("boundary", "pass")
        mechanisms = map_patterns_to_mechanisms([p], {}, [], [], None)
        assert len(mechanisms) == 0


# ---------------------------------------------------------------------------
# Test: Weak interaction exclusion (P1)
# ---------------------------------------------------------------------------

class TestWeakInteractionExclusion:
    """Weak interactions without 2D PDP must not become mechanisms."""

    def test_weak_interaction_no_2d_pdp_excluded(self):
        p = _make_pattern(
            "interaction", "weak",
            conditions=[
                PatternCondition(feature_name="f1", material_concept="c1",
                               operator="", value_range={}, source="interaction"),
                PatternCondition(feature_name="f2", material_concept="c2",
                               operator="", value_range={}, source="interaction"),
            ],
            confidence_score=0.35, confidence_label="low",
        )
        mechanisms = map_patterns_to_mechanisms([p], {}, [], [], None)
        assert len(mechanisms) == 0

    def test_pass_interaction_with_2d_pdp_included(self):
        p = _make_pattern(
            "interaction", "pass",
            conditions=[
                PatternCondition(feature_name="f1", material_concept="c1",
                               operator="between", value_range={"peak_value": 0.5}, source="interaction"),
                PatternCondition(feature_name="f2", material_concept="c2",
                               operator="between", value_range={"peak_value": 0.5}, source="interaction"),
            ],
            confidence_score=0.65, confidence_label="medium",
        )
        mechanisms = map_patterns_to_mechanisms([p], {}, [], [], None)
        assert len(mechanisms) == 1


# ---------------------------------------------------------------------------
# Test: peak_value=0 detection (P2)
# ---------------------------------------------------------------------------

class TestPeakValueZeroDetection:
    """peak_value of 0 is falsy but valid — must be detected."""

    def test_peak_value_zero_detected(self):
        p = _make_pattern(
            "interaction", "pass",
            conditions=[
                PatternCondition(feature_name="f1", material_concept="c1",
                               operator="between", value_range={"peak_value": 0.0}, source="interaction"),
                PatternCondition(feature_name="f2", material_concept="c2",
                               operator="between", value_range={"peak_value": 0.0}, source="interaction"),
            ],
        )
        assert _pattern_has_2d_pdp(p, []) is True

    def test_no_peak_value_not_detected(self):
        p = _make_pattern(
            "interaction", "pass",
            conditions=[
                PatternCondition(feature_name="f1", material_concept="c1",
                               operator="", value_range={}, source="interaction"),
            ],
        )
        assert _pattern_has_2d_pdp(p, []) is False


# ---------------------------------------------------------------------------
# Test: Lineage priority over registry (P2)
# ---------------------------------------------------------------------------

class TestLineagePriority:
    """Lineage category must be checked before semantics registry."""

    def test_lineage_wins_over_registry(self):
        from app.modules.interpretability_analysis.material_semantics_registry import get_semantics_registry
        reg = get_semantics_registry()
        # 'atomic_radius_mean' matches lattice_distortion in registry,
        # but lineage says 'electronic'
        lineage = {"atomic_radius_mean": {"category": "electronic"}}
        family = _infer_mechanism_family(None, ["atomic_radius_mean"], lineage, reg)
        assert family == "electronic_structure", f"Expected electronic_structure, got {family}"

    def test_registry_used_when_lineage_absent(self):
        from app.modules.interpretability_analysis.material_semantics_registry import get_semantics_registry
        reg = get_semantics_registry()
        family = _infer_mechanism_family(None, ["electronegativity_diff"], {}, reg)
        assert family == "bonding_strength", f"Expected bonding_strength, got {family}"

    def test_pattern_type_fallback(self):
        # Must pass a real pattern so _pattern_type_to_family can read .pattern_type
        p = _make_pattern("subgroup", "pass",
                          conditions=[PatternCondition(
                              feature_name="unknown_xyz", material_concept="test",
                              operator="", value_range={}, source="pdp")])
        family = _infer_mechanism_family(p, ["unknown_xyz"], {}, None)
        assert family == "composition_complexity"


# ---------------------------------------------------------------------------
# Test: Mechanism grounding levels
# ---------------------------------------------------------------------------

class TestGroundingLevels:
    """Grounding levels must be correctly assigned."""

    def test_lineage_grounded(self):
        lineage = {"feat_x": {"description": "Electronic band gap in eV"}}
        p = _make_pattern("monotonic", "pass")
        mechanisms = map_patterns_to_mechanisms([p], lineage, [], [], None)
        assert len(mechanisms) == 1
        assert mechanisms[0].grounding_level == "lineage_grounded"

    def test_physics_prior_grounded(self):
        p = _make_pattern(
            "monotonic", "pass",
            conditions=[PatternCondition(feature_name="electronegativity_diff",
                          material_concept="contrast", operator="increasing",
                          value_range={"min": 0.0, "max": 1.0}, source="pdp")],
        )
        mechanisms = map_patterns_to_mechanisms([p], {}, [], [], None)
        assert len(mechanisms) == 1
        assert mechanisms[0].grounding_level == "physics_prior_grounded"

    def test_descriptor_grounded(self):
        # Use a feature name guaranteed to match nothing in any registry
        p = _make_pattern("monotonic", "pass",
                          conditions=[PatternCondition(
                              feature_name="completely_opaque_xyz_987654321",
                              material_concept="test", operator="increasing",
                              value_range={"min": 0.0, "max": 1.0}, source="pdp")])
        mechanisms = map_patterns_to_mechanisms([p], {}, [], [], None)
        assert len(mechanisms) == 1
        assert mechanisms[0].grounding_level == "descriptor_grounded"

    def test_descriptor_grounded_limitation_added(self):
        p = _make_pattern("monotonic", "pass",
                          conditions=[PatternCondition(
                              feature_name="completely_opaque_xyz_987654321",
                              material_concept="test", operator="increasing",
                              value_range={"min": 0.0, "max": 1.0}, source="pdp")])
        mechanisms = map_patterns_to_mechanisms([p], {}, [], [], None)
        assert len(mechanisms) == 1
        has_grounding_limitation = any(
            "descriptor-grounded" in lim.lower() or "descriptor-name" in lim.lower()
            for lim in mechanisms[0].limitations
        )
        assert has_grounding_limitation, (
            "Should add limitation about descriptor-only grounding"
        )


# ---------------------------------------------------------------------------
# Test: Mechanism statements
# ---------------------------------------------------------------------------

class TestMechanismStatements:
    """Mechanism statements must reflect pattern type and grounding."""

    def test_monotonic_statement(self):
        p = _make_pattern("monotonic", "pass")
        mechanisms = map_patterns_to_mechanisms([p], {}, [], [], None)
        assert len(mechanisms) == 1
        assert "monotonic" in mechanisms[0].mechanism_statement.lower()

    def test_window_statement_says_model_supported(self):
        p = _make_pattern("window", "pass")
        mechanisms = map_patterns_to_mechanisms([p], {}, [], [], None)
        assert len(mechanisms) == 1
        assert "model-supported" in mechanisms[0].mechanism_statement.lower()

    def test_threshold_statement(self):
        p = _make_pattern("threshold", "pass")
        mechanisms = map_patterns_to_mechanisms([p], {}, [], [], None)
        assert len(mechanisms) == 1
        assert "regime" in mechanisms[0].mechanism_statement.lower() or "transition" in mechanisms[0].mechanism_statement.lower()


# ---------------------------------------------------------------------------
# Test: Evidence and pattern ID traceability
# ---------------------------------------------------------------------------

class TestEvidenceTraceability:
    """Mechanisms must retain source pattern IDs and evidence IDs."""

    def test_source_pattern_ids_preserved(self):
        p = _make_pattern("monotonic", "pass", pattern_id="mp_trace_test",
                         supporting_evidence_ids=["ev_a", "ev_b"])
        mechanisms = map_patterns_to_mechanisms([p], {}, [], [], None)
        assert len(mechanisms) == 1
        assert "mp_trace_test" in mechanisms[0].source_pattern_ids
        assert "ev_a" in mechanisms[0].supporting_evidence_ids
        assert "ev_b" in mechanisms[0].supporting_evidence_ids

    def test_validation_results_attached(self):
        p = _make_pattern("monotonic", "pass")
        mechanisms = map_patterns_to_mechanisms([p], {}, [], [], None)
        assert len(mechanisms) == 1
        assert len(mechanisms[0].supporting_pattern_validation) > 0
        assert mechanisms[0].supporting_pattern_validation[0]["validation_type"] == "bootstrap"


# ---------------------------------------------------------------------------
# Test: No patterns / empty input
# ---------------------------------------------------------------------------

class TestEmptyInput:
    """Edge cases for empty or None inputs."""

    def test_empty_patterns(self):
        mechanisms = map_patterns_to_mechanisms([], {}, [], [], None)
        assert mechanisms == []
