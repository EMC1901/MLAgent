import json

from app.modules.interpretability_analysis.llm_scientific_insight_parser import (
    parse_llm_scientific_insights,
)
from app.modules.interpretability_analysis.llm_scientific_insight_validator import (
    validate_llm_scientific_insights,
)


def _base_payload(insight):
    return {
        "narrative_title": "Evidence-grounded insight",
        "executive_summary": "The claim is model-supported and requires validation.",
        "academic_insights": [insight],
        "rejected_claims": [],
        "missing_evidence": [],
        "human_review_notes": [],
        "limitations_section": [],
        "validation_suggestions": [],
    }


def test_parse_and_validate_evidence_grounded_academic_insight():
    raw = json.dumps(_base_payload({
        "claim_id": "claim_001",
        "claim_type": "candidate_hypothesis",
        "claim": "Within the sampled domain, lower descriptor A may be associated with higher stability.",
        "material_meaning": "Descriptor A maps to a plausible material variable in the input evidence.",
        "supporting_evidence_ids": ["shap_001"],
        "evidence_chain": [
            {"step": "model_evidence", "summary": "SHAP evidence supports the association."},
            {"step": "hypothesis", "summary": "The association is testable on holdout data."},
        ],
        "evidence_strength": "moderate",
        "confidence": "medium",
        "validation_status": "model_supported_only",
        "falsifiable_prediction": "External samples with lower descriptor A should rank higher in predicted stability.",
        "suggested_validation": ["external holdout test"],
        "counterexamples_or_risks": ["Feature correlation may inflate attribution."],
        "scope_conditions": ["sampled domain only"],
        "allowed_wording": "model-supported candidate hypothesis",
    }))

    parsed = parse_llm_scientific_insights(raw, ["shap_001"])
    validation = validate_llm_scientific_insights(parsed, raw, {"shap_001"})

    assert validation["is_valid"] is True
    assert validation["issues"] == []
    assert len(parsed.academic_insights) == 1


def test_validate_repairs_unsupported_causal_wording_when_evidence_is_valid():
    raw = json.dumps(_base_payload({
        "claim_id": "claim_repair",
        "claim_type": "candidate_hypothesis",
        "claim": "Descriptor A is driven by non-linear threshold behavior in the sampled domain.",
        "material_meaning": "Descriptor A maps to a plausible material variable in the input evidence.",
        "supporting_evidence_ids": ["pdp_001"],
        "evidence_chain": [
            {"step": "model_evidence", "summary": "PDP evidence supports a threshold association."},
        ],
        "evidence_strength": "moderate",
        "confidence": "medium",
        "validation_status": "model_supported_only",
        "falsifiable_prediction": "External samples near the threshold should show a similar predicted response.",
        "suggested_validation": ["external holdout test"],
        "counterexamples_or_risks": [],
        "scope_conditions": ["sampled domain only"],
        "allowed_wording": "model-supported candidate hypothesis",
    }))

    parsed = parse_llm_scientific_insights(raw, ["pdp_001"])
    validation = validate_llm_scientific_insights(parsed, raw, {"pdp_001"})

    assert validation["is_valid"] is True
    assert validation["issues"] == []
    assert validation["repaired_claim_ids"] == ["claim_repair"]
    assert len(parsed.academic_insights) == 1
    assert "driven by" not in parsed.academic_insights[0]["claim"].lower()
    assert "associated with" in parsed.academic_insights[0]["claim"].lower()
    assert parsed.rejected_claims == []


def test_validate_rejects_claim_with_no_valid_evidence():
    raw = json.dumps(_base_payload({
        "claim_id": "claim_bad",
        "claim_type": "validated_conclusion",
        "claim": "Descriptor A causes higher stability.",
        "material_meaning": "",
        "supporting_evidence_ids": ["fake_001"],
        "evidence_chain": [],
        "evidence_strength": "strong",
        "confidence": "high",
        "validation_status": "model_supported_only",
        "falsifiable_prediction": "",
        "suggested_validation": [],
        "counterexamples_or_risks": [],
        "scope_conditions": [],
        "allowed_wording": "validated conclusion",
    }))

    parsed = parse_llm_scientific_insights(raw, ["shap_001"])
    validation = validate_llm_scientific_insights(parsed, raw, {"shap_001"})

    assert validation["is_valid"] is False
    assert any("No acceptable academic insights" in issue for issue in validation["issues"])
    assert parsed.academic_insights == []
    assert len(parsed.rejected_claims) == 1
    assert parsed.rejected_claims[0]["reason"] == "no valid supporting evidence IDs"