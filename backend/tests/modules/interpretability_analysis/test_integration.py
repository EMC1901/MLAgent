"""Full-pipeline integration tests for interpretability analysis.

Exercises the evidence -> profiles -> hypotheses -> scoring -> report
pipeline end-to-end, using the fixtures from conftest.py.
"""
import json
import pytest

from app.modules.interpretability_analysis.schemas import (
    EvidenceUnit,
    FeatureEvidenceProfile,
    ScientificHypothesis,
    ScientificInsightReport,
)
from app.modules.interpretability_analysis.evidence_normalizer import (
    build_evidence_units,
    build_feature_evidence_profiles,
)
from app.modules.interpretability_analysis.scientific_hypothesis_builder import (
    generate_scientific_hypotheses,
    generate_applicability_boundaries,
    generate_anomaly_patterns,
    build_scientific_insight_report,
)
from app.modules.interpretability_analysis.confidence_scorer import (
    score_all_hypotheses,
)


# ---------------------------------------------------------------------------
# Helper: run the core pipeline sequence
# ---------------------------------------------------------------------------

def run_pipeline(
    per_method_importance,
    feature_columns,
    correlation_analysis=None,
    partial_dependence=None,
    residual_analysis=None,
    systematic_errors=None,
    physics_constraints=None,
    high_error_analysis=None,
    shap_interactions=None,
    feature_lineage=None,
    cross_method_consensus=None,
    model_performance=None,
    method_statuses=None,
    sample_size=500,
):
    """Execute the core pipeline: evidence -> profiles -> hypotheses -> score -> report."""
    # Step 1: Build evidence units
    evidence_units = build_evidence_units(
        per_method_importance=per_method_importance,
        correlation_analysis=correlation_analysis,
        partial_dependence=partial_dependence,
        residual_analysis=residual_analysis,
        systematic_errors=systematic_errors,
        physics_constraints=physics_constraints,
        shap_summary=None,
        cross_method_consensus=cross_method_consensus,
    )

    # Step 2: Build feature evidence profiles
    profiles = build_feature_evidence_profiles(
        evidence_units=evidence_units,
        feature_columns=feature_columns,
        correlation_analysis=correlation_analysis,
        cross_method_consensus=cross_method_consensus,
        feature_lineage=feature_lineage,
    )

    # Step 3: Generate hypotheses
    hypotheses = generate_scientific_hypotheses(
        evidence_units=evidence_units,
        feature_profiles=profiles,
        partial_dependence=partial_dependence,
        correlation_analysis=correlation_analysis,
        residual_analysis=residual_analysis,
        systematic_errors=systematic_errors,
        high_error_analysis=high_error_analysis,
        physics_constraints=physics_constraints,
        shap_interactions=shap_interactions,
        feature_lineage=feature_lineage,
        sample_size=sample_size,
    )

    # Step 4: Score hypotheses
    scored = score_all_hypotheses(
        hypotheses=hypotheses,
        feature_profiles=profiles,
        cross_method_consensus=cross_method_consensus,
        model_performance=model_performance or {"r_squared": 0.85, "rmse": 0.15},
        sample_size=sample_size,
        physics_constraints=physics_constraints,
        evidence_units=evidence_units,
    )

    # Step 5: Build boundaries and anomalies
    boundaries = generate_applicability_boundaries(
        residual_analysis=residual_analysis,
        systematic_errors=systematic_errors,
        high_error_analysis=high_error_analysis,
        evidence_units=evidence_units,
        feature_profiles=profiles,
    )

    anomalies = generate_anomaly_patterns(
        high_error_analysis=high_error_analysis,
        systematic_errors=systematic_errors,
        evidence_units=evidence_units,
    )

    # Step 6: Assemble ScientificInsightReport
    report = build_scientific_insight_report(
        hypotheses=scored,
        boundaries=boundaries,
        anomalies=anomalies,
        physics_constraints=physics_constraints,
        evidence_units=evidence_units,
        feature_profiles=profiles,
        method_statuses=method_statuses or {k: "computed" for k in per_method_importance},
    )

    return report


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFullPipeline:

    def test_full_pipeline_evidence_to_report(
        self,
        sample_per_method_importance,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_cross_method_consensus,
        sample_feature_columns,
        sample_feature_lineage,
    ):
        """Full pipeline: all 3 importance methods + correlation + pdp + residuals."""
        report = run_pipeline(
            per_method_importance=sample_per_method_importance,
            feature_columns=sample_feature_columns,
            correlation_analysis=sample_correlation_analysis,
            partial_dependence=sample_partial_dependence,
            residual_analysis=sample_residual_analysis,
            feature_lineage=sample_feature_lineage,
            cross_method_consensus=sample_cross_method_consensus,
        )

        assert isinstance(report, ScientificInsightReport)
        # Should have hypotheses generated
        assert len(report.ranked_hypotheses) > 0, "Should produce at least one hypothesis"
        # Should have feature profiles
        assert len(report.feature_profiles) > 0
        # Should have evidence graph populated
        assert len(report.evidence_graph) > 0
        # Top hypothesis should have a confidence breakdown
        top = report.ranked_hypotheses[0]
        assert top.confidence_breakdown is not None
        assert 0.0 <= top.confidence_score <= 1.0
        # Should have boundaries from systematic error segments
        assert len(report.model_applicability_boundaries) > 0

    def test_full_pipeline_with_only_permutation_importance(
        self,
        sample_per_method_importance,
        sample_feature_columns,
        sample_cross_method_consensus,
    ):
        """Pipeline with only permutation_importance (single method)."""
        single_method = {
            "permutation_importance": sample_per_method_importance["permutation_importance"],
        }

        report = run_pipeline(
            per_method_importance=single_method,
            feature_columns=sample_feature_columns,
            cross_method_consensus=sample_cross_method_consensus,
        )

        assert isinstance(report, ScientificInsightReport)
        assert len(report.ranked_hypotheses) > 0
        # All evidence units should come from permutation_importance
        for fp in report.feature_profiles:
            for eu in fp.evidence_units:
                assert eu.method_name == "permutation_importance"

    def test_full_pipeline_no_pdp_no_correlation(
        self,
        sample_per_method_importance,
        sample_feature_columns,
    ):
        """Pipeline with no PDP and no correlation (minimal optional inputs)."""
        report = run_pipeline(
            per_method_importance=sample_per_method_importance,
            feature_columns=sample_feature_columns,
        )

        assert isinstance(report, ScientificInsightReport)
        assert len(report.ranked_hypotheses) > 0
        # No residual segments, so no boundaries from that source
        # (boundaries from high-error samples are not applicable here)

    def test_full_pipeline_with_physics_violations(
        self,
        sample_per_method_importance,
        sample_feature_columns,
        sample_physics_constraints_violated,
        sample_cross_method_consensus,
    ):
        """Pipeline with physics constraint violations produces limitation hypotheses."""
        report = run_pipeline(
            per_method_importance=sample_per_method_importance,
            feature_columns=sample_feature_columns,
            physics_constraints=sample_physics_constraints_violated,
            cross_method_consensus=sample_cross_method_consensus,
        )

        assert isinstance(report, ScientificInsightReport)
        # Physics violation should produce at least one limitation hypothesis
        physics_hypotheses = [
            h for h in report.ranked_hypotheses
            if h.hypothesis_pattern == "physics_violation"
        ]
        assert len(physics_hypotheses) > 0, "Should generate physics violation hypotheses"

        # Physics summary should reflect violations
        assert report.physics_consistency_summary["all_passed"] is False
        assert report.physics_consistency_summary["violation_count"] > 0

    def test_full_pipeline_empty_inputs_handles_gracefully(self):
        """Empty per_method_importance and no feature columns = empty report, not a crash."""
        report = run_pipeline(
            per_method_importance={},
            feature_columns=[],
        )

        assert isinstance(report, ScientificInsightReport)
        assert report.ranked_hypotheses == []
        assert report.feature_profiles == []
        assert report.evidence_graph == {}
        # Limitations should note the absence of data
        assert any("No scientific hypotheses" in lim for lim in report.limitations)

    def test_scientific_report_serializable_to_json(
        self,
        sample_per_method_importance,
        sample_feature_columns,
        sample_correlation_analysis,
        sample_partial_dependence,
        sample_residual_analysis,
        sample_physics_constraints,
        sample_high_error_analysis,
        sample_shap_interactions,
        sample_feature_lineage,
        sample_cross_method_consensus,
    ):
        """The final ScientificInsightReport must be serializable to JSON."""
        report = run_pipeline(
            per_method_importance=sample_per_method_importance,
            feature_columns=sample_feature_columns,
            correlation_analysis=sample_correlation_analysis,
            partial_dependence=sample_partial_dependence,
            residual_analysis=sample_residual_analysis,
            physics_constraints=sample_physics_constraints,
            high_error_analysis=sample_high_error_analysis,
            shap_interactions=sample_shap_interactions,
            feature_lineage=sample_feature_lineage,
            cross_method_consensus=sample_cross_method_consensus,
        )

        # Should serialize without raising
        json_str = report.model_dump_json(indent=2)
        assert isinstance(json_str, str)
        assert len(json_str) > 100

        # Round-trip: deserialize and check key fields
        data = json.loads(json_str)
        assert "ranked_hypotheses" in data
        assert "model_applicability_boundaries" in data
        assert "anomaly_or_counterexample_patterns" in data
        assert "evidence_graph" in data
        assert "limitations" in data


class TestPipelineWithAnomalies:

    def test_full_pipeline_with_high_error_anomalies(
        self,
        sample_per_method_importance,
        sample_feature_columns,
        sample_high_error_analysis,
        sample_systematic_errors,
    ):
        """Pipeline with high-error samples produces anomaly patterns."""
        report = run_pipeline(
            per_method_importance=sample_per_method_importance,
            feature_columns=sample_feature_columns,
            high_error_analysis=sample_high_error_analysis,
            systematic_errors=sample_systematic_errors,
        )

        assert isinstance(report, ScientificInsightReport)
        # High error samples with error > 0.1 should generate anomalies
        assert len(report.anomaly_or_counterexample_patterns) > 0
        for anm in report.anomaly_or_counterexample_patterns:
            assert anm.pattern_id.startswith("anm_")
            assert anm.description != ""

    def test_full_pipeline_with_shap_interactions(
        self,
        sample_per_method_importance,
        sample_feature_columns,
        sample_shap_interactions,
        sample_cross_method_consensus,
    ):
        """Pipeline with SHAP interactions produces interaction-pair hypotheses."""
        report = run_pipeline(
            per_method_importance=sample_per_method_importance,
            feature_columns=sample_feature_columns,
            shap_interactions=sample_shap_interactions,
            cross_method_consensus=sample_cross_method_consensus,
        )

        assert isinstance(report, ScientificInsightReport)
        # At least one interaction-pair hypothesis (strength 0.15 > 0.05 threshold)
        interaction_hypotheses = [
            h for h in report.ranked_hypotheses
            if h.hypothesis_pattern == "interaction_pair_discovery"
        ]
        assert len(interaction_hypotheses) > 0
