"""Tests for evidence_normalizer module."""
import pytest
from app.modules.interpretability_analysis.evidence_normalizer import (
    build_evidence_units,
    build_feature_evidence_profiles,
    _detect_pdp_monotonicity,
    _compute_pdp_strength,
    _compute_direction_consistency,
    _compute_stability_score,
    _compute_redundancy_risk,
    _compute_physical_interpretability,
)
from app.modules.interpretability_analysis.enums import EvidenceType
from app.modules.interpretability_analysis.schemas import EvidenceUnit


# ---------------------------------------------------------------------------
# Helper: minimal EvidenceUnit builder for lower-level function tests
# ---------------------------------------------------------------------------
def _make_unit(evidence_type, direction="unknown", strength=0.5,
               feature_names=None, quantitative_summary=None, method_name="test",
               ):
    return EvidenceUnit(
        evidence_type=evidence_type,
        direction=direction,
        strength=strength,
        feature_names=feature_names or [],
        quantitative_summary=quantitative_summary or {},
        method_name=method_name,
    )


# ===========================================================================
# build_evidence_units  (7 tests)
# ===========================================================================

class TestBuildEvidenceUnits:

    def test_build_evidence_units_creates_units_for_each_method(
        self, sample_per_method_importance,
    ):
        units = build_evidence_units(
            per_method_importance=sample_per_method_importance,
            correlation_analysis=None,
            partial_dependence=None,
            residual_analysis=None,
            systematic_errors=None,
            physics_constraints=None,
            shap_summary=None,
            cross_method_consensus=None,
        )
        assert len(units) == 30  # 10 features * 3 methods
        evidence_types = {u.evidence_type for u in units}
        assert EvidenceType.SHAP_IMPORTANCE in evidence_types
        assert EvidenceType.PERMUTATION_IMPORTANCE in evidence_types
        assert EvidenceType.COEFFICIENT_IMPORTANCE in evidence_types
        method_names = {u.method_name for u in units}
        assert "shap" in method_names
        assert "permutation_importance" in method_names
        assert "coefficient" in method_names

    def test_build_evidence_units_with_empty_input_returns_empty(self):
        units = build_evidence_units(
            per_method_importance={},
            correlation_analysis=None,
            partial_dependence=None,
            residual_analysis=None,
            systematic_errors=None,
            physics_constraints=None,
            shap_summary=None,
            cross_method_consensus=None,
        )
        assert units == []

    def test_build_evidence_units_with_pdp_evidence(
        self, sample_per_method_importance, sample_partial_dependence,
    ):
        units = build_evidence_units(
            per_method_importance=sample_per_method_importance,
            correlation_analysis=None,
            partial_dependence=sample_partial_dependence,
            residual_analysis=None,
            systematic_errors=None,
            physics_constraints=None,
            shap_summary=None,
            cross_method_consensus=None,
        )
        pdp_units = [u for u in units if u.evidence_type == EvidenceType.PDP_1D]
        assert len(pdp_units) == 3
        assert all(u.method_name == "partial_dependence" for u in pdp_units)
        assert all("trend" in u.quantitative_summary for u in pdp_units)

    def test_build_evidence_units_with_correlation_evidence(
        self, sample_correlation_analysis,
    ):
        units = build_evidence_units(
            per_method_importance={},
            correlation_analysis=sample_correlation_analysis,
            partial_dependence=None,
            residual_analysis=None,
            systematic_errors=None,
            physics_constraints=None,
            shap_summary=None,
            cross_method_consensus=None,
        )
        linear_units = [u for u in units
                        if u.evidence_type == EvidenceType.CORRELATION_LINEAR]
        rank_units = [u for u in units
                      if u.evidence_type == EvidenceType.CORRELATION_RANK]
        assert len(linear_units) == 10
        assert len(rank_units) == 2
        assert all("pearson_r" in u.quantitative_summary for u in linear_units)
        assert all("correlation" in u.quantitative_summary for u in rank_units)

    def test_build_evidence_units_with_residual_evidence(
        self, sample_residual_analysis,
    ):
        units = build_evidence_units(
            per_method_importance={},
            correlation_analysis=None,
            partial_dependence=None,
            residual_analysis=sample_residual_analysis,
            systematic_errors=None,
            physics_constraints=None,
            shap_summary=None,
            cross_method_consensus=None,
        )
        residual_units = [u for u in units
                          if u.evidence_type == EvidenceType.RESIDUAL_SEGMENT]
        assert len(residual_units) == 2
        assert all(u.method_name == "residual_analysis" for u in residual_units)
        assert all("segment_description" in u.quantitative_summary
                   for u in residual_units)

    def test_build_evidence_units_with_systematic_error_evidence(
        self, sample_systematic_errors,
    ):
        units = build_evidence_units(
            per_method_importance={},
            correlation_analysis=None,
            partial_dependence=None,
            residual_analysis=None,
            systematic_errors=sample_systematic_errors,
            physics_constraints=None,
            shap_summary=None,
            cross_method_consensus=None,
        )
        error_units = [u for u in units
                       if u.evidence_type == EvidenceType.ERROR_CONCENTRATION]
        assert len(error_units) == 2
        assert all(u.method_name == "systematic_error" for u in error_units)
        assert all("error_ratio_to_overall" in u.quantitative_summary
                   for u in error_units)

    def test_build_evidence_units_with_physics_constraints(
        self, sample_physics_constraints,
    ):
        units = build_evidence_units(
            per_method_importance={},
            correlation_analysis=None,
            partial_dependence=None,
            residual_analysis=None,
            systematic_errors=None,
            physics_constraints=sample_physics_constraints,
            shap_summary=None,
            cross_method_consensus=None,
        )
        physics_units = [u for u in units
                         if u.evidence_type == EvidenceType.PHYSICS_CONSTRAINT]
        assert len(physics_units) == 1
        assert physics_units[0].strength == 1.0
        assert physics_units[0].reliability == 1.0


# ===========================================================================
# build_feature_evidence_profiles  (4 tests)
# ===========================================================================

class TestBuildFeatureEvidenceProfiles:

    def test_build_feature_evidence_profiles_returns_correct_count(
        self, sample_per_method_importance, sample_feature_columns,
    ):
        units = build_evidence_units(
            per_method_importance=sample_per_method_importance,
            correlation_analysis=None,
            partial_dependence=None,
            residual_analysis=None,
            systematic_errors=None,
            physics_constraints=None,
            shap_summary=None,
            cross_method_consensus=None,
        )
        profiles = build_feature_evidence_profiles(
            evidence_units=units,
            feature_columns=sample_feature_columns,
            correlation_analysis=None,
            cross_method_consensus=None,
            feature_lineage=None,
        )
        assert len(profiles) == 10

    def test_build_feature_evidence_profiles_empty_evidence_returns_empty(
        self, sample_feature_columns,
    ):
        profiles = build_feature_evidence_profiles(
            evidence_units=[],
            feature_columns=sample_feature_columns,
            correlation_analysis=None,
            cross_method_consensus=None,
            feature_lineage=None,
        )
        assert profiles == []

    def test_build_feature_evidence_profiles_consensus_score(
        self, sample_per_method_importance, sample_feature_columns,
    ):
        units = build_evidence_units(
            per_method_importance=sample_per_method_importance,
            correlation_analysis=None,
            partial_dependence=None,
            residual_analysis=None,
            systematic_errors=None,
            physics_constraints=None,
            shap_summary=None,
            cross_method_consensus=None,
        )
        profiles = build_feature_evidence_profiles(
            evidence_units=units,
            feature_columns=sample_feature_columns,
            correlation_analysis=None,
            cross_method_consensus=None,
            feature_lineage=None,
        )
        # feat_0 has rank 1 in all 3 methods -> consensus = 3/3 = 1.0
        feat_0 = next(p for p in profiles if p.feature_name == "feat_0")
        assert feat_0.consensus_score == 1.0

    def test_build_feature_evidence_profiles_top_k_membership(
        self, sample_per_method_importance, sample_feature_columns,
    ):
        units = build_evidence_units(
            per_method_importance=sample_per_method_importance,
            correlation_analysis=None,
            partial_dependence=None,
            residual_analysis=None,
            systematic_errors=None,
            physics_constraints=None,
            shap_summary=None,
            cross_method_consensus=None,
        )
        profiles = build_feature_evidence_profiles(
            evidence_units=units,
            feature_columns=sample_feature_columns,
            correlation_analysis=None,
            cross_method_consensus=None,
            feature_lineage=None,
        )
        # feat_0 has rank 1 (<= 10) in all methods -> all True
        feat_0 = next(p for p in profiles if p.feature_name == "feat_0")
        assert feat_0.top_k_membership.get("shap") is True
        assert feat_0.top_k_membership.get("permutation_importance") is True
        assert feat_0.top_k_membership.get("coefficient") is True


# ===========================================================================
# _detect_pdp_monotonicity  (4 tests)
# ===========================================================================

class TestDetectPdpMonotonicity:

    def test_detect_pdp_monotonicity_increasing(self):
        pdp_item = {
            "feature_name": "test_feat",
            "grid_values": [0, 1, 2, 3, 4],
            "pdp_values": [0.0, 0.25, 0.5, 0.75, 1.0],
        }
        result = _detect_pdp_monotonicity(pdp_item)
        assert result == "monotonic_increasing"

    def test_detect_pdp_monotonicity_non_monotonic(self):
        pdp_item = {
            "feature_name": "test_feat",
            "grid_values": [0, 1, 2, 3, 4],
            "pdp_values": [0.0, 0.8, 0.3, 0.9, 0.2],
        }
        result = _detect_pdp_monotonicity(pdp_item)
        assert "non_monotonic" in result

    def test_detect_pdp_monotonicity_flat(self):
        pdp_item = {
            "feature_name": "test_feat",
            "grid_values": [0, 1, 2, 3, 4],
            "pdp_values": [0.5, 0.5, 0.5, 0.5, 0.5],
        }
        result = _detect_pdp_monotonicity(pdp_item)
        assert result == "flat"

    def test_detect_pdp_monotonicity_insufficient_data(self):
        pdp_item = {
            "feature_name": "test_feat",
            "grid_values": [0, 1],
            "pdp_values": [0.0, 0.5],
        }
        result = _detect_pdp_monotonicity(pdp_item)
        assert result == "insufficient_data"


# ===========================================================================
# _compute_pdp_strength
# ===========================================================================

class TestComputePdpStrength:

    def test_strong_signal_returns_positive(self):
        pdp_item = {
            "feature_name": "test_feat",
            "grid_values": [0, 1, 2, 3, 4],
            "pdp_values": [0.1, 0.3, 0.7, 1.0, 1.2],
        }
        result = _compute_pdp_strength(pdp_item)
        assert 0.0 < result <= 1.0

    def test_flat_signal_returns_zero(self):
        pdp_item = {
            "feature_name": "test_feat",
            "grid_values": [0, 1, 2, 3, 4],
            "pdp_values": [0.5, 0.5, 0.5, 0.5, 0.5],
        }
        result = _compute_pdp_strength(pdp_item)
        assert result == 0.0


# ===========================================================================
# _compute_direction_consistency
# ===========================================================================

class TestComputeDirectionConsistency:

    def test_mixed_directions(self):
        units = [
            _make_unit("pdp_1d", direction="positive"),
            _make_unit("shap_importance", direction="positive"),
            _make_unit("permutation_importance", direction="negative"),
        ]
        result = _compute_direction_consistency("feat_0", units)
        # 2 positive, 1 negative -> majority fraction = 2/3
        assert result == pytest.approx(2.0 / 3.0)

    def test_all_agree_returns_one(self):
        units = [
            _make_unit("pdp_1d", direction="positive"),
            _make_unit("shap_importance", direction="positive"),
        ]
        result = _compute_direction_consistency("feat_0", units)
        assert result == 1.0

    def test_insufficient_data_returns_neutral(self):
        units = [
            _make_unit("pdp_1d", direction="positive"),
        ]
        result = _compute_direction_consistency("feat_0", units)
        assert result == 0.5


# ===========================================================================
# _compute_stability_score
# ===========================================================================

class TestComputeStabilityScore:

    def test_from_permutation_importance(self):
        units = [
            EvidenceUnit(
                evidence_type=EvidenceType.PERMUTATION_IMPORTANCE,
                quantitative_summary={
                    "importance_value": 0.1,
                    "importance_std": 0.01,
                },
                feature_names=["feat_0"],
                method_name="permutation_importance",
            ),
        ]
        result = _compute_stability_score("feat_0", units)
        # cv = 0.01 / 0.1 = 0.1, stability = 1 - 0.1 = 0.9
        assert result == pytest.approx(0.9)

    def test_no_relevant_evidence_returns_neutral(self):
        units = [
            _make_unit("pdp_1d"),
        ]
        result = _compute_stability_score("feat_0", units)
        assert result == 0.5


# ===========================================================================
# _compute_redundancy_risk  (3 tests)
# ===========================================================================

class TestComputeRedundancyRisk:

    def test_compute_redundancy_risk_with_high_correlation(
        self, sample_correlation_analysis,
    ):
        # feat_0 is paired with feat_1 at correlation=0.92
        risk = _compute_redundancy_risk("feat_0", sample_correlation_analysis)
        assert risk == 0.92

    def test_compute_redundancy_risk_no_correlation(
        self, sample_correlation_analysis,
    ):
        # feat_5 is not in any high_correlation_pairs
        risk = _compute_redundancy_risk("feat_5", sample_correlation_analysis)
        assert risk == 0.0

    def test_none_analysis_returns_zero(self):
        risk = _compute_redundancy_risk("feat_0", None)
        assert risk == 0.0


# ===========================================================================
# _compute_physical_interpretability  (2 tests)
# ===========================================================================

class TestComputePhysicalInterpretability:

    def test_compute_physical_interpretability_with_lineage(
        self, sample_feature_lineage,
    ):
        # feat_0: source + description + transformation + category(composition)
        # = 0.4 + 0.1 + 0.15 + 0.1 + 0.15 = 0.9
        score = _compute_physical_interpretability(
            "feat_0", sample_feature_lineage,
        )
        assert score == 0.9

    def test_compute_physical_interpretability_no_lineage(
        self, sample_feature_lineage,
    ):
        score = _compute_physical_interpretability(
            "feat_unknown", sample_feature_lineage,
        )
        assert score == 0.0
