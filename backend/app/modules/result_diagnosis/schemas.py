from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel


# ---- Request schemas ----

class ResultDiagnosisCreateRequest(BaseModel):
    metric_evaluation_id: Optional[str] = None
    force_rerun: bool = False
    use_llm: bool = True
    include_dataset_context: bool = True
    include_pipeline_context: bool = True
    include_feature_context: bool = True
    diagnosis_profile: str = "standard"
    notes: Optional[str] = None


# ---- Internal DTOs ----

class EvidenceItem(BaseModel):
    evidence_type: str
    source_module: str
    source_field: str
    value: Optional[Any] = None
    interpretation: str = ""


class DiagnosticFinding(BaseModel):
    finding_id: str = ""
    diagnosis_type: str
    severity: str = "medium"
    evidence_strength: str = "moderate"
    description: str = ""
    evidence_items: List[EvidenceItem] = []
    affected_models: List[str] = []
    affected_trials: List[str] = []
    possible_causes: List[str] = []
    recommended_actions: List[str] = []
    refinement_targets: List[str] = []
    confidence_level: str = "medium"


class RootCauseHypothesis(BaseModel):
    hypothesis_id: str = ""
    root_cause_type: str = ""
    description: str = ""
    supporting_findings: List[str] = []
    likelihood: str = "medium"
    actionability: str = "medium"


class SystemActionHint(BaseModel):
    suggested_feature_strategy: Optional[str] = None
    suggested_model_family: Optional[str] = None
    suggested_hpo_budget: Optional[str] = None
    suggested_validation_strategy: Optional[str] = None


class RefinementRecommendation(BaseModel):
    recommendation_id: str = ""
    target_stage: str
    recommendation_type: str
    priority: str = "medium"
    description: str = ""
    expected_benefit: str = ""
    risk: str = ""
    system_action_hint: SystemActionHint = SystemActionHint()
    requires_human_review: bool = False


class OverallAssessment(BaseModel):
    performance_level: str = "weak"
    baseline_improvement_level: str = "unknown"
    stability_level: str = "moderately_unstable"
    main_issue_category: str = ""
    should_refine: bool = False
    summary: str = ""
    confidence_level: str = "medium"


class EvidenceSummary(BaseModel):
    metric_evidence: List[EvidenceItem] = []
    baseline_evidence: List[EvidenceItem] = []
    fold_stability_evidence: List[EvidenceItem] = []
    dataset_evidence: List[EvidenceItem] = []
    feature_evidence: List[EvidenceItem] = []
    pipeline_evidence: List[EvidenceItem] = []


class SystemDiagnosticChecks(BaseModel):
    weak_baseline_improvement: bool = False
    high_fold_variance: bool = False
    all_models_weak: bool = False
    hpo_budget_limited: bool = False
    small_sample_warning: bool = False
    feature_count_low: bool = False
    many_features_dropped: bool = False
    candidate_underperforms_baseline: bool = False
    unstable_best_model: bool = False
    additional_checks: Dict[str, Any] = {}
    warnings: List[str] = []


class LLMDiagnosisResult(BaseModel):
    overall_assessment: Optional[OverallAssessment] = None
    diagnostic_findings: List[DiagnosticFinding] = []
    root_cause_hypotheses: List[RootCauseHypothesis] = []
    refinement_recommendations: List[RefinementRecommendation] = []
    confidence_level: str = "medium"


class SuggestedNextIterationProfile(BaseModel):
    model_search_budget: str = "moderate"
    hpo_trials: str = "increase_if_runtime_allows"
    feature_strategy: str = "keep_current"


class ClosedLoopRefinementInput(BaseModel):
    result_diagnosis_id: str = ""
    metric_evaluation_id: str = ""
    task_id: str = ""
    should_refine: bool = False
    refinement_focus: List[str] = []
    priority_recommendations: List[RefinementRecommendation] = []
    diagnostic_findings_summary: List[Dict[str, Any]] = []
    constraints_to_preserve: List[str] = []
    avoid_actions: List[str] = []
    suggested_next_iteration_profile: SuggestedNextIterationProfile = SuggestedNextIterationProfile()
    ready_for_closed_loop_refinement: bool = False


class DiagnosisArtifactManifest(BaseModel):
    manifest_path: Optional[str] = None
    diagnosis_result_path: Optional[str] = None
    diagnostic_context_path: Optional[str] = None
    system_diagnostic_checks_path: Optional[str] = None
    llm_diagnosis_path: Optional[str] = None
    evidence_summary_path: Optional[str] = None
    closed_loop_refinement_input_path: Optional[str] = None


# ---- Response schemas ----

class ResultDiagnosisResponse(BaseModel):
    result_diagnosis_id: Optional[str] = None
    task_id: Optional[str] = None
    metric_evaluation_id: Optional[str] = None
    pipeline_execution_id: Optional[str] = None
    status: str = "diagnosing"
    diagnosis_mode: str = "hybrid"
    overall_assessment: Optional[OverallAssessment] = None
    diagnostic_findings: List[DiagnosticFinding] = []
    evidence_summary: Optional[EvidenceSummary] = None
    root_cause_hypotheses: List[RootCauseHypothesis] = []
    refinement_recommendations: List[RefinementRecommendation] = []
    closed_loop_refinement_input: Optional[ClosedLoopRefinementInput] = None
    ready_for_closed_loop_refinement: bool = False
    llm_diagnosis: Optional[LLMDiagnosisResult] = None
    system_diagnostic_checks: Optional[SystemDiagnosticChecks] = None
    diagnosis_artifact_manifest: Optional[DiagnosisArtifactManifest] = None
    warnings: List[str] = []
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ResultDiagnosisSummaryResponse(BaseModel):
    result_diagnosis_id: str
    task_id: str
    status: str
    main_issue_category: Optional[str] = None
    performance_level: Optional[str] = None
    should_refine: bool = False
    ready_for_closed_loop_refinement: bool = False
    top_findings: List[Dict[str, Any]] = []
    top_recommendations: List[Dict[str, Any]] = []
    created_at: Optional[datetime] = None
