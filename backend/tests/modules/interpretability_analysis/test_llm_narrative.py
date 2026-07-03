"""Tests for the LLM narrative layer: prompt builder, parser, and validator."""
import json
import pytest

from app.modules.interpretability_analysis.schemas import (
    ScientificInsightReport,
    ScientificHypothesis,
    ConfidenceBreakdown,
    ModelApplicabilityBoundary,
    AnomalyPattern,
    EvidenceUnit,
    FeatureEvidenceProfile,
    LLMNarrativeOutput,
)
from app.modules.interpretability_analysis.llm_narrative_prompt_builder import (
    build_llm_narrative_prompt,
    NARRATIVE_SYSTEM_PROMPT,
)
from app.modules.interpretability_analysis.llm_narrative_parser import (
    parse_llm_narrative,
)
from app.modules.interpretability_analysis.llm_narrative_validator import (
    validate_llm_narrative,
)
from app.modules.interpretability_analysis.exceptions import LLMNarrativeException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_evidence_unit(evidence_id, feature_name, evidence_type="shap_importance"):
    return EvidenceUnit(
        evidence_id=evidence_id,
        evidence_type=evidence_type,
        feature_names=[feature_name],
        quantitative_summary={"importance_value": 0.75, "importance_rank": 1, "total_features_evaluated": 10},
        direction="positive",
        strength=0.8,
        reliability=0.7,
        limitations=[],
        method_name=evidence_type.replace("_importance", ""),
    )


def _make_hypothesis(hypothesis_id, evidence_ids, confidence=0.7, claim_type="association"):
    return ScientificHypothesis(
        hypothesis_id=hypothesis_id,
        claim=f"Feature 'feat_0' is strongly associated with the target property (hypothesis {hypothesis_id}).",
        claim_type=claim_type,
        supporting_evidence_ids=evidence_ids,
        contradicting_evidence_ids=[],
        confidence_score=confidence,
        confidence_breakdown=ConfidenceBreakdown(
            cross_method_agreement=0.8,
            model_performance_reliability=0.75,
            sample_support=0.7,
            pdp_shap_direction_consistency=0.8,
            correlation_support=0.6,
            physics_consistency=1.0,
            contradiction_penalty=0.0,
            total_confidence=confidence,
            confidence_label="high" if confidence >= 0.7 else "medium",
        ),
        confidence_label="high" if confidence >= 0.7 else "medium",
        scope_conditions=["Applies within the training data distribution."],
        validation_suggestions=["Verify with held-out data."],
        hypothesis_pattern="shap_permutation_consensus",
    )


def _make_boundary(boundary_id, severity="warning"):
    return ModelApplicabilityBoundary(
        boundary_id=boundary_id,
        description=f"Model performance degrades in region {boundary_id}.",
        feature_conditions={"prediction_range": "low"},
        error_ratio=1.5,
        supporting_evidence_ids=[f"ev_{boundary_id}"],
        severity=severity,
    )


def _make_anomaly(anomaly_id):
    return AnomalyPattern(
        pattern_id=anomaly_id,
        description=f"High-error pattern in region {anomaly_id}.",
        sample_count=5,
        feature_signature={"affected_features": ["feat_0"]},
        supporting_evidence_ids=[],
    )


def _minimal_scientific_report(num_hypotheses=3, num_boundaries=1, num_anomalies=1):
    """Build a minimal ScientificInsightReport for prompt building."""
    evidence_ids = [f"ev_{i:04d}" for i in range(10)]
    hypotheses = [_make_hypothesis(f"hyp_{i}", evidence_ids[:3], 0.80 - i * 0.1) for i in range(num_hypotheses)]
    boundaries = [_make_boundary(f"bnd_{i}") for i in range(num_boundaries)]
    anomalies = [_make_anomaly(f"anm_{i}") for i in range(num_anomalies)]

    # Feature profiles with embedded evidence units
    profiles = []
    for feat_name in ["feat_0", "feat_1", "feat_2"]:
        eus = [_make_evidence_unit(f"ev_{j:04d}", feat_name) for j in range(3)]
        profiles.append(FeatureEvidenceProfile(
            feature_name=feat_name,
            rank_percentile=90.0,
            z_score=0.85,
            top_k_membership={"shap": True, "permutation_importance": True},
            consensus_score=0.75,
            direction_consistency=0.8,
            method_agreement={"shap": 0.9, "permutation_importance": 0.85},
            stability_score=0.8,
            redundancy_risk=0.2,
            physical_interpretability_score=0.7,
            evidence_units=eus,
        ))

    return ScientificInsightReport(
        executive_insights=hypotheses[:2],
        ranked_hypotheses=hypotheses,
        mechanism_candidates=[h for h in hypotheses if h.claim_type == "mechanism_hypothesis"],
        model_applicability_boundaries=boundaries,
        anomaly_or_counterexample_patterns=anomalies,
        physics_consistency_summary={"all_passed": True, "violation_count": 0},
        evidence_graph={"feat_0": evidence_ids[:3], "feat_1": evidence_ids[3:6]},
        limitations=["Limited sample diversity in extreme regions."],
        feature_profiles=profiles,
    )


# ---------------------------------------------------------------------------
# Tests: build_llm_narrative_prompt
# ---------------------------------------------------------------------------

class TestBuildNarrativePrompt:

    def test_build_narrative_prompt_includes_evidence_ids(self):
        """The user_message JSON must contain evidence_index entries."""
        report = _minimal_scientific_report()
        task = {"task_type": "regression", "target_column": "band_gap"}
        model = {"final_model_id": "model_1", "final_model_family": "RandomForest"}
        metrics = {"r_squared": 0.85, "rmse": 0.15}

        result = build_llm_narrative_prompt(
            scientific_report=report,
            task_summary=task,
            final_model_summary=model,
            final_metric_summary=metrics,
        )

        user_msg = json.loads(result["user_message"])
        evidence_index = user_msg.get("evidence_index", {})
        assert len(evidence_index) > 0, "Evidence index should not be empty"
        # Every key is a valid evidence_id string
        assert all(isinstance(k, str) and k.startswith("ev_") for k in evidence_index.keys())

    def test_build_narrative_prompt_includes_hypotheses(self):
        """The user_message JSON must include ranked_hypotheses."""
        report = _minimal_scientific_report(num_hypotheses=3)
        task = {"task_type": "regression"}
        model = {"final_model_id": "model_1"}
        metrics = {"r_squared": 0.85}

        result = build_llm_narrative_prompt(
            scientific_report=report,
            task_summary=task,
            final_model_summary=model,
            final_metric_summary=metrics,
        )

        user_msg = json.loads(result["user_message"])
        hypotheses = user_msg["scientific_report"]["ranked_hypotheses"]
        assert len(hypotheses) == 3
        assert hypotheses[0]["hypothesis_id"] is not None
        assert "claim" in hypotheses[0]
        assert "supporting_evidence_ids" in hypotheses[0]

    def test_build_narrative_prompt_includes_boundaries(self):
        """The user_message JSON must include model_applicability_boundaries."""
        report = _minimal_scientific_report(num_boundaries=2)
        task = {"task_type": "regression"}
        model = {"final_model_id": "model_1"}
        metrics = {"r_squared": 0.85}

        result = build_llm_narrative_prompt(
            scientific_report=report,
            task_summary=task,
            final_model_summary=model,
            final_metric_summary=metrics,
        )

        user_msg = json.loads(result["user_message"])
        boundaries = user_msg["scientific_report"]["model_applicability_boundaries"]
        assert len(boundaries) == 2
        assert "boundary_id" in boundaries[0]
        assert "severity" in boundaries[0]

    def test_build_narrative_prompt_returns_system_and_user_messages(self):
        """Return dict has system_prompt, user_message, and narrative_context keys."""
        report = _minimal_scientific_report()
        task = {"task_type": "regression"}
        model = {}
        metrics = {}

        result = build_llm_narrative_prompt(
            scientific_report=report,
            task_summary=task,
            final_model_summary=model,
            final_metric_summary=metrics,
        )

        assert result["system_prompt"] == NARRATIVE_SYSTEM_PROMPT
        assert isinstance(result["user_message"], str)
        assert len(result["user_message"]) > 0
        assert isinstance(result["narrative_context"], dict)
        assert "instructions" in result["narrative_context"]


# ---------------------------------------------------------------------------
# Tests: parse_llm_narrative
# ---------------------------------------------------------------------------

class TestParseNarrative:

    def test_parse_valid_narrative_json(self):
        """Straightforward JSON string parses into LLMNarrativeOutput."""
        valid_ids = ["ev_001", "ev_002", "ev_003"]
        raw = json.dumps({
            "narrative_title": "Test Report",
            "executive_summary": "This is a summary.",
            "insights": [
                {
                    "hypothesis_id": "hyp_1",
                    "claim": "Feature A is important.",
                    "evidence_references": ["ev_001", "ev_002"],
                    "confidence_rationale": "High agreement.",
                    "caveats": "Limited data.",
                    "suggested_validation": "Experimental validation.",
                }
            ],
            "limitations_section": [{"category": "data", "description": "Small dataset."}],
            "validation_suggestions": [{"hypothesis_id": "hyp_1", "suggestion": "Run experiment."}],
        })

        output = parse_llm_narrative(raw, valid_ids)
        assert output.narrative_title == "Test Report"
        assert output.executive_summary == "This is a summary."
        assert len(output.insights) == 1
        assert output.insights[0]["hypothesis_id"] == "hyp_1"
        assert output.insights[0]["evidence_references"] == ["ev_001", "ev_002"]
        assert len(output.limitations_section) == 1
        assert len(output.validation_suggestions) == 1

    def test_parse_narrative_with_invalid_evidence_refs(self):
        """Parser preserves ALL evidence refs (valid + invalid). Validator catches invalid ones."""
        valid_ids = ["ev_001"]
        raw = json.dumps({
            "narrative_title": "Test",
            "executive_summary": "Summary.",
            "insights": [
                {
                    "hypothesis_id": "hyp_1",
                    "claim": "Important.",
                    "evidence_references": ["ev_001", "ev_999", "ev_bad"],
                }
            ],
            "limitations_section": [],
            "validation_suggestions": [],
        })

        output = parse_llm_narrative(raw, valid_ids)
        # Parser preserves ALL refs; validator checks validity
        assert sorted(output.insights[0]["evidence_references"]) == sorted(["ev_001", "ev_999", "ev_bad"])

    def test_parse_narrative_malformed_json_returns_fallback(self):
        """Malformed JSON returns a fallback LLMNarrativeOutput, not an exception."""
        valid_ids = ["ev_001"]
        raw = "This is not JSON at all, just some prose."

        output = parse_llm_narrative(raw, valid_ids)
        # Fallback is returned, not raised
        assert output.narrative_title is not None
        assert len(output.limitations_section) > 0
        assert output.limitations_section[0]["category"] == "parse_error"
        assert output.insights == []

    def test_parse_narrative_empty_response_raises_exception(self):
        """Empty string raises LLMNarrativeException."""
        with pytest.raises(LLMNarrativeException, match="empty"):
            parse_llm_narrative("", ["ev_001"])

    def test_extract_json_from_code_fence(self):
        """JSON wrapped in a markdown code fence should be extracted and parsed."""
        valid_ids = ["ev_001"]
        raw = '```json\n{\n  "narrative_title": "Fenced",\n  "executive_summary": "Works.",\n  "insights": [],\n  "limitations_section": [],\n  "validation_suggestions": []\n}\n```'

        output = parse_llm_narrative(raw, valid_ids)
        assert output.narrative_title == "Fenced"
        assert output.executive_summary == "Works."


# ---------------------------------------------------------------------------
# Tests: validate_llm_narrative
# ---------------------------------------------------------------------------

class TestValidateNarrative:

    def _make_narrative(self, title="T", summary="S", insights=None,
                        limitations=None, validations=None):
        return parse_llm_narrative(
            json.dumps({
                "narrative_title": title,
                "executive_summary": summary,
                "insights": insights or [],
                "limitations_section": limitations or [],
                "validation_suggestions": validations or [],
            }),
            valid_evidence_ids=["ev_001", "ev_002"],
        )

    def test_validate_narrative_no_issues(self):
        """Clean narrative with valid evidence refs passes validation."""
        narrative = self._make_narrative(
            title="Good Report",
            summary="A comprehensive summary of findings.",
            insights=[{
                "hypothesis_id": "hyp_1",
                "claim": "Feature is important.",
                "evidence_references": ["ev_001"],
            }],
            limitations=[{"category": "data", "description": "Small sample."}],
            validations=[{"hypothesis_id": "hyp_1", "suggestion": "Test."}],
        )

        result = validate_llm_narrative(
            narrative=narrative,
            raw_response="Safe text.",
            valid_evidence_ids={"ev_001", "ev_002"},
        )

        assert result["is_valid"] is True
        assert result["issues"] == []

    def test_validate_narrative_with_dangerous_patterns(self):
        """Raw response containing eval() or subprocess should produce issues."""
        narrative = self._make_narrative()
        raw = "I will run eval(some_code) and use os.system to execute commands."

        result = validate_llm_narrative(
            narrative=narrative,
            raw_response=raw,
            valid_evidence_ids={"ev_001"},
        )

        assert result["is_valid"] is False
        assert len(result["issues"]) > 0
        assert any("dangerous" in issue.lower() for issue in result["issues"])

    def test_validate_narrative_with_invalid_evidence_refs(self):
        """Insights referencing evidence IDs not in the valid set produce issues.

        Build the LLMNarrativeOutput directly (bypass the parser, which would
        filter invalid refs) to verify the validator catches them.
        """
        narrative = LLMNarrativeOutput(
            narrative_title="Test",
            executive_summary="A summary.",
            insights=[{
                "hypothesis_id": "hyp_1",
                "claim": "Claim.",
                "evidence_references": ["ev_ghost"],
            }],
            limitations_section=[{"category": "data", "description": "Small."}],
            validation_suggestions=[],
        )

        result = validate_llm_narrative(
            narrative=narrative,
            raw_response="Clean text.",
            valid_evidence_ids={"ev_001"},
        )

        assert result["is_valid"] is False
        assert any("invalid evidence" in issue.lower() for issue in result["issues"])

    def test_validate_narrative_empty_insights_warning(self):
        """Empty insights list should produce a warning."""
        narrative = self._make_narrative(insights=[])

        result = validate_llm_narrative(
            narrative=narrative,
            raw_response="OK.",
            valid_evidence_ids={"ev_001"},
        )

        assert any("no insights" in w.lower() for w in result["warnings"])
