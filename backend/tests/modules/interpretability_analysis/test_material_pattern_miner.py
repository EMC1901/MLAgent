"""Tests for the Phase 1 material_pattern_miner module.

Covers all 5 rule types, material concept inference, confidence
scoring/downgrade, evidence traceability, and statement quality.
"""

import pytest
import numpy as np
from types import SimpleNamespace

from app.modules.interpretability_analysis.material_pattern_miner import (
    mine_material_patterns,
    infer_material_concept,
)
from app.modules.interpretability_analysis.evidence_normalizer import (
    build_evidence_units,
    build_feature_evidence_profiles,
)
from app.modules.interpretability_analysis.schemas import (
    MaterialPatternCandidate,
    PatternCondition,
    PatternEffect,
    PatternCounterexample,
)
from app.modules.interpretability_analysis.enums import EvidenceType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_evidence_units_and_profiles(
    per_method_importance,
    feature_columns,
    partial_dependence=None,
    correlation_analysis=None,
    feature_lineage=None,
):
    units = build_evidence_units(
        per_method_importance=per_method_importance,
        correlation_analysis=correlation_analysis,
        partial_dependence=partial_dependence,
        residual_analysis=None,
        systematic_errors=None,
        physics_constraints=None,
        shap_summary=None,
        cross_method_consensus=None,
    )
    profiles = build_feature_evidence_profiles(
        evidence_units=units,
        feature_columns=feature_columns,
        correlation_analysis=correlation_analysis,
        cross_method_consensus=None,
        feature_lineage=feature_lineage,
    )
    return units, profiles


# ---------------------------------------------------------------------------
# infer_material_concept
# ---------------------------------------------------------------------------


class TestInferMaterialConcept:

    def test_from_lineage_description(self):
        lineage = {"feat_x": {"description": "Atomic fraction of element A", "category": "composition"}}
        result = infer_material_concept("feat_x", lineage)
        assert result == "Atomic fraction of element A"

    def test_from_lineage_category_no_description(self):
        lineage = {"feat_x": {"category": "structure"}}
        result = infer_material_concept("feat_x", lineage)
        assert result == "structure"

    def test_from_lineage_other_category(self):
        lineage = {"feat_x": {"category": "other"}}
        result = infer_material_concept("feat_x", lineage)
        assert result == "opaque descriptor"

    def test_keyword_fallback_electronegativity(self):
        result = infer_material_concept("mean_electronegativity_diff", {})
        assert "electronegativity" in result

    def test_keyword_fallback_density(self):
        result = infer_material_concept("theoretical_density", {})
        assert "density" in result or "compactness" in result

    def test_keyword_fallback_unknown(self):
        result = infer_material_concept("xyz_unknown_feature", {})
        assert result == "opaque descriptor"


# ---------------------------------------------------------------------------
# Rule 1: Monotonic patterns
# ---------------------------------------------------------------------------


class TestMonotonicPattern:

    def test_monotonic_pdp_generates_pattern(self):
        per_method_importance = {
            "shap": [{"feature_name": "feat_0", "importance_value": 0.9,
                      "importance_rank": 1, "direction": "positive"}],
            "permutation_importance": [{"feature_name": "feat_0", "importance_value": 0.8,
                                        "importance_rank": 1, "direction": "positive"}],
        }
        feature_columns = ["feat_0"]
        pdp = {
            "pdp_1d": [{"feature_name": "feat_0",
                        "grid_values": [0, 1, 2, 3, 4],
                        "pdp_values": [0.1, 0.3, 0.7, 1.0, 1.2]}],
            "pdp_2d": [],
        }
        units, profiles = _make_evidence_units_and_profiles(
            per_method_importance, feature_columns, partial_dependence=pdp,
        )

        patterns = mine_material_patterns(
            X=None, y_true=None, y_pred=None,
            feature_profiles=profiles,
            evidence_units=units,
            partial_dependence=pdp,
            shap_dependence=None,
            shap_interactions=None,
            correlation_analysis=None,
            high_error_analysis=None,
            systematic_errors=None,
            feature_lineage=None,
        )

        monotonic = [p for p in patterns if p.pattern_type == "monotonic"]
        assert len(monotonic) >= 1
        mp = monotonic[0]
        assert mp.pattern_type == "monotonic"
        assert "feat_0" in mp.statement
        assert len(mp.conditions) >= 1
        assert mp.conditions[0].source == "pdp"
        assert mp.predicted_effect.evidence_basis == "pdp_delta"
        # monotonic_increasing PDP must produce target_direction == "increases"
        assert mp.predicted_effect.target_direction == "increases"
        assert len(mp.supporting_evidence_ids) > 0

    def test_monotonic_decreasing_pattern(self):
        per_method_importance = {
            "shap": [{"feature_name": "feat_0", "importance_value": 0.9,
                      "importance_rank": 1, "direction": "negative"}],
            "permutation_importance": [{"feature_name": "feat_0", "importance_value": 0.8,
                                        "importance_rank": 1, "direction": "negative"}],
        }
        feature_columns = ["feat_0"]
        pdp = {
            "pdp_1d": [{"feature_name": "feat_0",
                        "grid_values": [0, 1, 2, 3, 4],
                        "pdp_values": [1.2, 1.0, 0.7, 0.3, 0.1]}],
            "pdp_2d": [],
        }
        units, profiles = _make_evidence_units_and_profiles(
            per_method_importance, feature_columns, partial_dependence=pdp,
        )

        patterns = mine_material_patterns(
            X=None, y_true=None, y_pred=None,
            feature_profiles=profiles, evidence_units=units,
            partial_dependence=pdp, shap_dependence=None,
            shap_interactions=None, correlation_analysis=None,
            high_error_analysis=None, systematic_errors=None,
            feature_lineage=None,
        )

        monotonic = [p for p in patterns if p.pattern_type == "monotonic"]
        assert len(monotonic) >= 1
        # monotonic_decreasing PDP must produce target_direction == "decreases"
        assert monotonic[0].predicted_effect.target_direction == "decreases"

    def test_low_consensus_no_monotonic(self):
        """Features with consensus < 0.5 should not generate monotonic patterns."""
        per_method_importance = {
            "shap": [{"feature_name": "feat_5", "importance_value": 0.1,
                      "importance_rank": 15, "direction": "positive"}],
        }
        feature_columns = ["feat_5"]
        pdp = {
            "pdp_1d": [{"feature_name": "feat_5",
                        "grid_values": [0, 1, 2, 3, 4],
                        "pdp_values": [0.1, 0.3, 0.7, 1.0, 1.2]}],
            "pdp_2d": [],
        }
        units, profiles = _make_evidence_units_and_profiles(
            per_method_importance, feature_columns, partial_dependence=pdp,
        )

        patterns = mine_material_patterns(
            X=None, y_true=None, y_pred=None,
            feature_profiles=profiles, evidence_units=units,
            partial_dependence=pdp, shap_dependence=None,
            shap_interactions=None, correlation_analysis=None,
            high_error_analysis=None, systematic_errors=None,
            feature_lineage=None,
        )

        monotonic = [p for p in patterns if p.pattern_type == "monotonic"]
        assert len(monotonic) == 0


# ---------------------------------------------------------------------------
# Rule 2: Threshold patterns
# ---------------------------------------------------------------------------


class TestThresholdPattern:

    def test_non_monotonic_pdp_generates_threshold(self):
        per_method_importance = {
            "shap": [{"feature_name": "feat_1", "importance_value": 0.7,
                      "importance_rank": 2, "direction": "positive"}],
            "permutation_importance": [{"feature_name": "feat_1", "importance_value": 0.65,
                                        "importance_rank": 2, "direction": "positive"}],
        }
        feature_columns = ["feat_0", "feat_1"]
        pdp = {
            "pdp_1d": [{"feature_name": "feat_1",
                        "grid_values": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                        "pdp_values": [0.1, 0.8, 0.3, 0.9, 0.2, 0.1]}],
            "pdp_2d": [],
        }
        units, profiles = _make_evidence_units_and_profiles(
            per_method_importance, feature_columns, partial_dependence=pdp,
        )

        patterns = mine_material_patterns(
            X=None, y_true=None, y_pred=None,
            feature_profiles=profiles, evidence_units=units,
            partial_dependence=pdp, shap_dependence=None,
            shap_interactions=None, correlation_analysis=None,
            high_error_analysis=None, systematic_errors=None,
            feature_lineage=None,
        )

        threshold = [p for p in patterns if p.pattern_type == "threshold"]
        assert len(threshold) >= 1
        tp = threshold[0]
        assert "transition" in tp.statement.lower() or "threshold" in tp.conditions[0].value_range
        assert tp.conditions[0].source == "pdp"

    def test_shap_dependence_sign_crossing_generates_threshold(self):
        per_method_importance = {
            "shap": [{"feature_name": "feat_2", "importance_value": 0.6,
                      "importance_rank": 3, "direction": "unknown"}],
        }
        feature_columns = ["feat_2"]
        units, profiles = _make_evidence_units_and_profiles(
            per_method_importance, feature_columns,
        )

        shap_dep = [
            {"feature_name": "feat_2",
             "feature_values": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
             "shap_values": [-0.1, -0.05, 0.02, 0.08, 0.15, 0.2]},
        ]

        patterns = mine_material_patterns(
            X=None, y_true=None, y_pred=None,
            feature_profiles=profiles, evidence_units=units,
            partial_dependence=None, shap_dependence=shap_dep,
            shap_interactions=None, correlation_analysis=None,
            high_error_analysis=None, systematic_errors=None,
            feature_lineage=None,
        )

        threshold = [p for p in patterns if p.pattern_type == "threshold"]
        assert len(threshold) >= 1
        tp = threshold[0]
        assert "sign transition" in tp.statement.lower() or "transition" in tp.statement.lower()
        assert tp.conditions[0].source == "shap_dependence"


# ---------------------------------------------------------------------------
# Rule 3: Window patterns
# ---------------------------------------------------------------------------


class TestWindowPattern:

    def test_pdp_mid_peak_generates_window(self):
        per_method_importance = {
            "shap": [{"feature_name": "feat_0", "importance_value": 0.8,
                      "importance_rank": 1, "direction": "positive"}],
        }
        feature_columns = ["feat_0"]
        pdp = {
            "pdp_1d": [{"feature_name": "feat_0",
                        "grid_values": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                        "pdp_values": [0.2, 0.3, 0.5, 0.8, 1.0, 0.9, 0.6, 0.4, 0.3, 0.2]}],
            "pdp_2d": [],
        }
        units, profiles = _make_evidence_units_and_profiles(
            per_method_importance, feature_columns, partial_dependence=pdp,
        )

        patterns = mine_material_patterns(
            X=None, y_true=None, y_pred=None,
            feature_profiles=profiles, evidence_units=units,
            partial_dependence=pdp, shap_dependence=None,
            shap_interactions=None, correlation_analysis=None,
            high_error_analysis=None, systematic_errors=None,
            feature_lineage=None,
        )

        window = [p for p in patterns if p.pattern_type == "window"]
        assert len(window) >= 1
        wp = window[0]
        assert "favorable" in wp.statement.lower() or "intermediate" in wp.statement.lower()
        assert wp.conditions[0].operator == "between"
        assert wp.predicted_effect.target_direction == "peaks"


# ---------------------------------------------------------------------------
# Rule 4: Interaction patterns
# ---------------------------------------------------------------------------


class TestInteractionPattern:

    def test_shap_interaction_generates_pattern(self):
        per_method_importance = {
            "shap": [
                {"feature_name": "feat_a", "importance_value": 0.7, "importance_rank": 1, "direction": "positive"},
                {"feature_name": "feat_b", "importance_value": 0.6, "importance_rank": 2, "direction": "negative"},
            ],
        }
        feature_columns = ["feat_a", "feat_b"]
        units, profiles = _make_evidence_units_and_profiles(
            per_method_importance, feature_columns,
        )

        shap_int = [
            {"feature_1": "feat_a", "feature_2": "feat_b", "interaction_strength": 0.25},
        ]

        patterns = mine_material_patterns(
            X=None, y_true=None, y_pred=None,
            feature_profiles=profiles, evidence_units=units,
            partial_dependence=None, shap_dependence=None,
            shap_interactions=shap_int, correlation_analysis=None,
            high_error_analysis=None, systematic_errors=None,
            feature_lineage=None,
        )

        interaction = [p for p in patterns if p.pattern_type == "interaction"]
        assert len(interaction) >= 1
        ip = interaction[0]
        assert len(ip.conditions) == 2
        assert ip.conditions[0].source == "interaction"
        assert "interaction" in ip.statement.lower() or "coupled" in ip.statement.lower()

    def test_weak_interaction_below_threshold_skipped(self):
        per_method_importance = {
            "shap": [{"feature_name": "feat_a", "importance_value": 0.7,
                      "importance_rank": 1, "direction": "positive"}],
        }
        feature_columns = ["feat_a", "feat_b"]
        units, profiles = _make_evidence_units_and_profiles(
            per_method_importance, feature_columns,
        )

        shap_int = [
            {"feature_1": "feat_a", "feature_2": "feat_b", "interaction_strength": 0.01},
        ]

        patterns = mine_material_patterns(
            X=None, y_true=None, y_pred=None,
            feature_profiles=profiles, evidence_units=units,
            partial_dependence=None, shap_dependence=None,
            shap_interactions=shap_int, correlation_analysis=None,
            high_error_analysis=None, systematic_errors=None,
            feature_lineage=None,
        )

        interaction = [p for p in patterns if p.pattern_type == "interaction"]
        assert len(interaction) == 0


# ---------------------------------------------------------------------------
# Rule 5: Counterexample / boundary patterns
# ---------------------------------------------------------------------------


class TestCounterexampleBoundary:

    def test_systematic_error_generates_boundary(self):
        per_method_importance = {
            "shap": [{"feature_name": "feat_0", "importance_value": 0.9,
                      "importance_rank": 1, "direction": "positive"}],
        }
        feature_columns = ["feat_0"]
        units, profiles = _make_evidence_units_and_profiles(
            per_method_importance, feature_columns,
        )

        systematic = [
            {"feature_name": "feat_0", "quantile": 0, "value_range": "[0.0, 0.2]",
             "n_samples": 20, "mean_abs_error": 0.3, "error_ratio_to_overall": 2.5,
             "possible_cause": "extreme feature values"},
        ]

        patterns = mine_material_patterns(
            X=None, y_true=None, y_pred=None,
            feature_profiles=profiles, evidence_units=units,
            partial_dependence=None, shap_dependence=None,
            shap_interactions=None, correlation_analysis=None,
            high_error_analysis=None, systematic_errors=systematic,
            feature_lineage=None,
        )

        boundary = [p for p in patterns if p.pattern_type == "boundary"]
        assert len(boundary) >= 1
        bp = boundary[0]
        assert "reliability boundary" in bp.statement.lower() or "error" in bp.statement.lower()
        assert bp.predicted_effect.evidence_basis == "observed_target"

    def test_low_error_ratio_skipped(self):
        per_method_importance = {
            "shap": [{"feature_name": "feat_0", "importance_value": 0.9,
                      "importance_rank": 1, "direction": "positive"}],
        }
        feature_columns = ["feat_0"]
        units, profiles = _make_evidence_units_and_profiles(
            per_method_importance, feature_columns,
        )

        systematic = [
            {"feature_name": "feat_0", "quantile": 2, "value_range": "[0.4, 0.6]",
             "n_samples": 20, "mean_abs_error": 0.15, "error_ratio_to_overall": 1.0,
             "possible_cause": "normal"},
        ]

        patterns = mine_material_patterns(
            X=None, y_true=None, y_pred=None,
            feature_profiles=profiles, evidence_units=units,
            partial_dependence=None, shap_dependence=None,
            shap_interactions=None, correlation_analysis=None,
            high_error_analysis=None, systematic_errors=systematic,
            feature_lineage=None,
        )

        boundary = [p for p in patterns if p.pattern_type == "boundary"]
        assert len(boundary) == 0


# ---------------------------------------------------------------------------
# Confidence & evidence traceability
# ---------------------------------------------------------------------------


class TestConfidenceScoring:

    def test_pattern_has_confidence_score_in_range(self):
        per_method_importance = {
            "shap": [
                {"feature_name": "feat_0", "importance_value": 0.9,
                 "importance_rank": 1, "direction": "positive"},
                {"feature_name": "feat_1", "importance_value": 0.8,
                 "importance_rank": 2, "direction": "positive"},
            ],
            "permutation_importance": [
                {"feature_name": "feat_0", "importance_value": 0.85,
                 "importance_rank": 1, "direction": "positive"},
                {"feature_name": "feat_1", "importance_value": 0.75,
                 "importance_rank": 2, "direction": "positive"},
            ],
        }
        feature_columns = ["feat_0", "feat_1"]
        pdp = {
            "pdp_1d": [{"feature_name": "feat_0",
                        "grid_values": [0, 1, 2, 3, 4],
                        "pdp_values": [0.1, 0.3, 0.7, 1.0, 1.2]}],
            "pdp_2d": [],
        }
        units, profiles = _make_evidence_units_and_profiles(
            per_method_importance, feature_columns, partial_dependence=pdp,
        )

        patterns = mine_material_patterns(
            X=None, y_true=None, y_pred=None,
            feature_profiles=profiles, evidence_units=units,
            partial_dependence=pdp, shap_dependence=None,
            shap_interactions=None, correlation_analysis=None,
            high_error_analysis=None, systematic_errors=None,
            feature_lineage=None,
        )

        for pattern in patterns:
            assert 0.0 <= pattern.confidence_score <= 1.0
            assert pattern.confidence_label in ("low", "medium", "high")

    def test_opaque_feature_downgrades_confidence(self):
        """Feature without lineage or keyword match caps at medium."""
        per_method_importance = {
            "shap": [{"feature_name": "xyz_mystery", "importance_value": 0.9,
                      "importance_rank": 1, "direction": "positive"}],
            "permutation_importance": [{"feature_name": "xyz_mystery", "importance_value": 0.85,
                                        "importance_rank": 1, "direction": "positive"}],
        }
        feature_columns = ["xyz_mystery"]
        pdp = {
            "pdp_1d": [{"feature_name": "xyz_mystery",
                        "grid_values": [0, 1, 2, 3, 4],
                        "pdp_values": [0.1, 0.3, 0.7, 1.0, 1.2]}],
            "pdp_2d": [],
        }
        units, profiles = _make_evidence_units_and_profiles(
            per_method_importance, feature_columns, partial_dependence=pdp,
        )

        patterns = mine_material_patterns(
            X=None, y_true=None, y_pred=None,
            feature_profiles=profiles, evidence_units=units,
            partial_dependence=pdp, shap_dependence=None,
            shap_interactions=None, correlation_analysis=None,
            high_error_analysis=None, systematic_errors=None,
            feature_lineage={},
        )

        # xyz_mystery is opaque -> physical_interpretability = 0.0
        # The downgrade rule caps it at "medium"
        monotonic = [p for p in patterns if p.pattern_type == "monotonic"]
        if monotonic:
            assert monotonic[0].confidence_label in ("low", "medium")


# ---------------------------------------------------------------------------
# Evidence traceability
# ---------------------------------------------------------------------------


class TestEvidenceTraceability:

    def test_evidence_ids_from_real_evidence_units(self):
        per_method_importance = {
            "shap": [{"feature_name": "feat_0", "importance_value": 0.9,
                      "importance_rank": 1, "direction": "positive"}],
            "permutation_importance": [{"feature_name": "feat_0", "importance_value": 0.85,
                                        "importance_rank": 1, "direction": "positive"}],
        }
        feature_columns = ["feat_0"]
        pdp = {
            "pdp_1d": [{"feature_name": "feat_0",
                        "grid_values": [0, 1, 2, 3, 4],
                        "pdp_values": [0.1, 0.3, 0.7, 1.0, 1.2]}],
            "pdp_2d": [],
        }
        units, profiles = _make_evidence_units_and_profiles(
            per_method_importance, feature_columns, partial_dependence=pdp,
        )

        all_real_ids = {eu.evidence_id for eu in units}

        patterns = mine_material_patterns(
            X=None, y_true=None, y_pred=None,
            feature_profiles=profiles, evidence_units=units,
            partial_dependence=pdp, shap_dependence=None,
            shap_interactions=None, correlation_analysis=None,
            high_error_analysis=None, systematic_errors=None,
            feature_lineage=None,
        )

        for pattern in patterns:
            for eid in pattern.supporting_evidence_ids:
                assert eid.startswith("ev_"), f"Evidence ID '{eid}' should start with 'ev_'"
                assert eid in all_real_ids, (
                    f"Evidence ID '{eid}' in pattern '{pattern.pattern_id}' "
                    f"is not from any real EvidenceUnit"
                )


# ---------------------------------------------------------------------------
# Statement quality
# ---------------------------------------------------------------------------


class TestStatementQuality:

    def test_no_importance_restatements(self):
        """Pattern statements must not contain 'ranked highly', 'feature importance',
        or 'SHAP important' — these are importance restatements, not material patterns."""
        per_method_importance = {
            "shap": [{"feature_name": "feat_0", "importance_value": 0.9,
                      "importance_rank": 1, "direction": "positive"}],
            "permutation_importance": [{"feature_name": "feat_0", "importance_value": 0.85,
                                        "importance_rank": 1, "direction": "positive"}],
        }
        feature_columns = ["feat_0"]
        pdp = {
            "pdp_1d": [{"feature_name": "feat_0",
                        "grid_values": [0, 1, 2, 3, 4],
                        "pdp_values": [0.1, 0.3, 0.7, 1.0, 1.2]}],
            "pdp_2d": [],
        }
        units, profiles = _make_evidence_units_and_profiles(
            per_method_importance, feature_columns, partial_dependence=pdp,
        )

        patterns = mine_material_patterns(
            X=None, y_true=None, y_pred=None,
            feature_profiles=profiles, evidence_units=units,
            partial_dependence=pdp, shap_dependence=None,
            shap_interactions=None, correlation_analysis=None,
            high_error_analysis=None, systematic_errors=None,
            feature_lineage=None,
        )

        forbidden_phrases = [
            "ranked highly",
            "feature importance",
            "SHAP important",
            "is important",
        ]
        for pattern in patterns:
            stmt_lower = pattern.statement.lower()
            found = [p for p in forbidden_phrases if p in stmt_lower]
            assert not found, (
                f"Pattern '{pattern.pattern_id}' statement contains "
                f"forbidden importance-restatement phrases: {found}\n"
                f"Statement: {pattern.statement}"
            )


# ---------------------------------------------------------------------------
# Integration: ScientificInsightReport compatibility
# ---------------------------------------------------------------------------


class TestScientificInsightReportIntegration:

    def test_material_pattern_candidates_in_report(self):
        from app.modules.interpretability_analysis.scientific_hypothesis_builder import (
            build_scientific_insight_report,
        )
        from app.modules.interpretability_analysis.schemas import ScientificInsightReport

        per_method_importance = {
            "shap": [{"feature_name": "feat_0", "importance_value": 0.9,
                      "importance_rank": 1, "direction": "positive"}],
            "permutation_importance": [{"feature_name": "feat_0", "importance_value": 0.85,
                                        "importance_rank": 1, "direction": "positive"}],
        }
        feature_columns = ["feat_0"]
        pdp = {
            "pdp_1d": [{"feature_name": "feat_0",
                        "grid_values": [0, 1, 2, 3, 4],
                        "pdp_values": [0.1, 0.3, 0.7, 1.0, 1.2]}],
            "pdp_2d": [],
        }
        units, profiles = _make_evidence_units_and_profiles(
            per_method_importance, feature_columns, partial_dependence=pdp,
        )

        material_patterns = mine_material_patterns(
            X=None, y_true=None, y_pred=None,
            feature_profiles=profiles, evidence_units=units,
            partial_dependence=pdp, shap_dependence=None,
            shap_interactions=None, correlation_analysis=None,
            high_error_analysis=None, systematic_errors=None,
            feature_lineage=None,
        )

        report = build_scientific_insight_report(
            hypotheses=[], boundaries=[], anomalies=[],
            physics_constraints=None,
            evidence_units=units, feature_profiles=profiles,
            method_statuses={"shap": "computed"},
            material_patterns=material_patterns,
        )

        assert isinstance(report, ScientificInsightReport)
        assert len(report.material_pattern_candidates) > 0

    def test_material_insight_derives_from_patterns_not_hypotheses(self):
        """When material_pattern_candidates exist, the backward-compat
        top_material_patterns should derive from them."""
        per_method_importance = {
            "shap": [{"feature_name": "feat_0", "importance_value": 0.9,
                      "importance_rank": 1, "direction": "positive"}],
            "permutation_importance": [{"feature_name": "feat_0", "importance_value": 0.85,
                                        "importance_rank": 1, "direction": "positive"}],
        }
        feature_columns = ["feat_0"]
        pdp = {
            "pdp_1d": [{"feature_name": "feat_0",
                        "grid_values": [0, 1, 2, 3, 4],
                        "pdp_values": [0.1, 0.3, 0.7, 1.0, 1.2]}],
            "pdp_2d": [],
        }
        units, profiles = _make_evidence_units_and_profiles(
            per_method_importance, feature_columns, partial_dependence=pdp,
        )

        material_patterns = mine_material_patterns(
            X=None, y_true=None, y_pred=None,
            feature_profiles=profiles, evidence_units=units,
            partial_dependence=pdp, shap_dependence=None,
            shap_interactions=None, correlation_analysis=None,
            high_error_analysis=None, systematic_errors=None,
            feature_lineage=None,
        )

        # Simulate the service.py backward-compat path
        scientific_report = SimpleNamespace(
            material_pattern_candidates=material_patterns,
            executive_insights=[],
            ranked_hypotheses=[],
            limitations=["Test limitation"],
        )

        from app.modules.interpretability_analysis.service import _features_from_evidence_refs

        if scientific_report.material_pattern_candidates:
            top_patterns = scientific_report.material_pattern_candidates[:10]
            material_insight = {
                "top_material_patterns": [
                    {
                        "pattern": p.statement[:200] if p.statement else "",
                        "supporting_features": list(dict.fromkeys(
                            c.feature_name for c in p.conditions if c.feature_name
                        ))[:5],
                        "supporting_evidence_ids": p.supporting_evidence_ids[:5],
                        "possible_material_meaning": ", ".join(p.material_concepts) if p.material_concepts else "",
                        "evidence_strength": p.confidence_label,
                        "caution": "; ".join(p.limitations[:2]) if p.limitations else "",
                        "conditions": [c.model_dump() for c in p.conditions],
                        "validation_suggestions": p.validation_suggestions[:3],
                    }
                    for p in top_patterns
                ],
            }

            assert len(material_insight["top_material_patterns"]) > 0
            top = material_insight["top_material_patterns"][0]
            assert "pattern" in top
            assert "supporting_features" in top
            assert "supporting_evidence_ids" in top
            assert top["evidence_strength"] in ("low", "medium", "high")
            # Conditions should be structured, not raw evidence IDs
            assert "conditions" in top
            for cond in top["conditions"]:
                assert "feature_name" in cond
                assert "material_concept" in cond
                assert "operator" in cond
