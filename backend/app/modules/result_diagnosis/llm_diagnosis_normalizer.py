import copy
from typing import Dict, Any, List
from app.modules.result_diagnosis.schemas import (
    LLMDiagnosisResult,
    OverallAssessment,
    DiagnosticFinding,
    EvidenceItem,
    RootCauseHypothesis,
    RefinementRecommendation,
    SystemActionHint,
)
from app.modules.result_diagnosis.enums import canonical_diagnosis_type


def normalize_llm_diagnosis(raw_diagnosis: Dict[str, Any]) -> LLMDiagnosisResult:
    data = copy.deepcopy(raw_diagnosis)

    # Normalize overall_assessment
    oa_data = data.get("overall_assessment") or {}
    oa = OverallAssessment(
        performance_level=oa_data.get("performance_level", "weak"),
        baseline_improvement_level=oa_data.get("baseline_improvement_level", "unknown"),
        stability_level=oa_data.get("stability_level", "moderately_unstable"),
        main_issue_category=oa_data.get("main_issue_category", ""),
        should_refine=oa_data.get("should_refine", False),
        summary=oa_data.get("summary", ""),
        confidence_level=oa_data.get("confidence_level", "medium"),
    )

    # Normalize findings
    findings = []
    for i, f_data in enumerate(data.get("diagnostic_findings") or []):
        if not isinstance(f_data, dict):
            continue
        evidence_items = []
        for e_data in f_data.get("evidence_items") or []:
            if isinstance(e_data, dict):
                evidence_items.append(EvidenceItem(
                    evidence_type=e_data.get("evidence_type", ""),
                    source_module=e_data.get("source_module", ""),
                    source_field=e_data.get("source_field", ""),
                    value=e_data.get("value"),
                    interpretation=e_data.get("interpretation", ""),
                ))
        raw_type = f_data.get("diagnosis_type", "")
        finding = DiagnosticFinding(
            finding_id=f_data.get("finding_id", f"find_{i + 1:03d}"),
            diagnosis_type=canonical_diagnosis_type(raw_type),
            severity=f_data.get("severity", "medium"),
            evidence_strength=f_data.get("evidence_strength", "moderate"),
            description=f_data.get("description", ""),
            evidence_items=evidence_items,
            affected_models=f_data.get("affected_models") or [],
            affected_trials=f_data.get("affected_trials") or [],
            possible_causes=f_data.get("possible_causes") or [],
            recommended_actions=f_data.get("recommended_actions") or [],
            refinement_targets=[t for t in (f_data.get("refinement_targets") or [])],
            confidence_level=f_data.get("confidence_level", "medium"),
        )
        findings.append(finding)

    # Normalize root cause hypotheses
    hypotheses = []
    for i, h_data in enumerate(data.get("root_cause_hypotheses") or []):
        if not isinstance(h_data, dict):
            continue
        hypothesis = RootCauseHypothesis(
            hypothesis_id=h_data.get("hypothesis_id", f"hyp_{i + 1:03d}"),
            root_cause_type=h_data.get("root_cause_type", ""),
            description=h_data.get("description", ""),
            supporting_findings=[str(s) for s in (h_data.get("supporting_findings") or [])],
            likelihood=h_data.get("likelihood", "medium"),
            actionability=h_data.get("actionability", "medium"),
        )
        hypotheses.append(hypothesis)

    # Normalize refinement recommendations
    recommendations = []
    for i, r_data in enumerate(data.get("refinement_recommendations") or []):
        if not isinstance(r_data, dict):
            continue
        hint_data = r_data.get("system_action_hint") or {}
        hint = SystemActionHint(
            suggested_feature_strategy=hint_data.get("suggested_feature_strategy"),
            suggested_model_family=hint_data.get("suggested_model_family"),
            suggested_hpo_budget=hint_data.get("suggested_hpo_budget"),
            suggested_validation_strategy=hint_data.get("suggested_validation_strategy"),
        )
        rec = RefinementRecommendation(
            recommendation_id=r_data.get("recommendation_id", f"rec_{i + 1:03d}"),
            target_stage=r_data.get("target_stage", ""),
            recommendation_type=r_data.get("recommendation_type", ""),
            priority=r_data.get("priority", "medium"),
            description=r_data.get("description", ""),
            expected_benefit=r_data.get("expected_benefit", ""),
            risk=r_data.get("risk", ""),
            system_action_hint=hint,
            requires_human_review=r_data.get("requires_human_review", False),
        )
        recommendations.append(rec)

    return LLMDiagnosisResult(
        overall_assessment=oa,
        diagnostic_findings=findings,
        root_cause_hypotheses=hypotheses,
        refinement_recommendations=recommendations,
        confidence_level=data.get("confidence_level", "medium"),
    )
