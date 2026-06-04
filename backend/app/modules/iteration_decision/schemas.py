from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel


# ---- Request ----

class IterationDecisionCreateRequest(BaseModel):
    metric_evaluation_id: Optional[str] = None
    force_rerun: bool = False
    max_iterations: int = 5
    current_iteration_index: Optional[int] = None
    minimum_improvement_threshold: Optional[float] = None
    notes: Optional[str] = None


# ---- Evidence DTOs ----

class EvidenceItem(BaseModel):
    evidence_type: str
    source_module: str
    source_field: str
    value: Optional[Any] = None
    interpretation: str = ""


class EvidenceBundle(BaseModel):
    ml_performance: List[EvidenceItem] = []
    materials: List[EvidenceItem] = []
    workflow_quality: List[EvidenceItem] = []
    history_trends: List[EvidenceItem] = []


# ---- System Check DTOs ----

class SystemChecks(BaseModel):
    # ML rules
    weak_baseline_improvement: bool = False
    high_fold_variance: bool = False
    all_models_weak: bool = False
    hpo_budget_limited: bool = False
    candidate_underperforms_baseline: bool = False
    unstable_best_model: bool = False
    # Data rules
    small_sample_warning: bool = False
    feature_count_low: bool = False
    many_features_dropped: bool = False
    # Materials rules
    physics_constraint_violated: bool = False
    feature_materials_relevance_low: bool = False
    chemical_space_coverage_low: bool = False
    # Guard rules
    max_iterations_reached: bool = False
    no_improvement_trend: bool = False
    repeated_root_cause: bool = False

    additional_checks: Dict[str, Any] = {}
    warnings: List[str] = []


# ---- LLM output DTOs ----

class TaskCompletionAssessment(BaseModel):
    completion_level: str = "partial"  # "achieved" | "partial" | "not_achieved"
    target_metric: Optional[str] = None
    target_value: Optional[float] = None
    actual_value: Optional[float] = None
    gap_description: str = ""
    physics_constraints_satisfied: bool = True
    physics_violations: List[str] = []


class GapAnalysis(BaseModel):
    primary_gap: str = ""
    gap_magnitude: str = ""  # "small" | "moderate" | "large" | "critical"
    contributing_factors: List[str] = []


class RootCauseAnalysis(BaseModel):
    primary_root_cause: str = ""
    dimension: str = ""  # data_side | feature_side | model_side | evaluation_side
    causal_chain: str = ""
    upstream_stage_at_fault: Optional[str] = None
    supporting_evidence: List[str] = []


class ImprovementPotential(BaseModel):
    estimate: str = ""  # "high" | "moderate" | "low" | "none"
    key_levers: List[str] = []
    estimated_effort: str = ""  # "low" | "moderate" | "high"


class DecisionReasoning(BaseModel):
    task_completion: TaskCompletionAssessment = TaskCompletionAssessment()
    performance_assessment: str = ""
    gap_analysis: GapAnalysis = GapAnalysis()
    root_cause: RootCauseAnalysis = RootCauseAnalysis()
    improvement_potential: ImprovementPotential = ImprovementPotential()
    final_reasoning_summary: str = ""


class StageChange(BaseModel):
    stage: str
    action: str  # "expand" | "replace" | "add" | "remove" | "adjust" | "keep"
    description: str = ""
    rationale: str = ""
    specific_instructions: Optional[Dict[str, Any]] = None


class IterationPlan(BaseModel):
    rerun_from_stage: str
    stage_changes: List[StageChange] = []
    preserved_stages: List[str] = []
    expected_improvement: str = ""
    estimated_remaining_iterations: int = 1
    stop_condition: str = ""


class StopRationale(BaseModel):
    primary_reason: str = ""
    category: str = ""  # "target_achieved" | "converged" | "diminishing_returns" | "resource_limit" | "insoluble"
    supporting_reasons: List[str] = []
    best_result_summary: str = ""


class LLMDecisionOutput(BaseModel):
    decision: str = ""  # "iterate" | "stop"
    reasoning: DecisionReasoning = DecisionReasoning()
    evidence_basis: List[EvidenceItem] = []
    iteration_plan: Optional[IterationPlan] = None
    stop_rationale: Optional[StopRationale] = None
    confidence: str = "medium"


# ---- Plan DTOs (system-built from LLM output) ----

class IterationRerunPlan(BaseModel):
    next_iteration_index: int = 1
    rerun_from_stage: Optional[str] = None
    rerun_stages: List[str] = []
    reuse_artifacts: List[str] = []
    invalidate_artifacts: List[str] = []
    expected_improvement_targets: List[str] = []
    minimum_improvement_threshold: Optional[float] = None
    stop_after_next_iteration_if_no_gain: bool = True
    reasoning: str = ""


class RevisedWorkflowPlan(BaseModel):
    status: str = "planned_by_iteration_decision"
    planning_mode: str = "llm_iteration_decision"
    task_summary: Optional[Dict[str, Any]] = None
    data_strategy: Optional[Dict[str, Any]] = None
    feature_strategy: Optional[Dict[str, Any]] = None
    model_strategy: Optional[Dict[str, Any]] = None
    validation_strategy: Optional[Dict[str, Any]] = None
    evaluation_strategy: Optional[Dict[str, Any]] = None
    hpo_strategy: Optional[Dict[str, Any]] = None
    changed_sections: List[str] = []
    preserved_sections: List[str] = []
    planning_warnings: List[str] = []
    llm_reasoning_summary: str = ""


# ---- Artifact ----

class ArtifactManifest(BaseModel):
    manifest_path: Optional[str] = None
    decision_result_path: Optional[str] = None
    context_path: Optional[str] = None
    evidence_path: Optional[str] = None
    system_checks_path: Optional[str] = None
    llm_request_path: Optional[str] = None
    llm_response_path: Optional[str] = None
    iteration_plan_path: Optional[str] = None
    revised_workflow_plan_path: Optional[str] = None
    stop_output_path: Optional[str] = None


# ---- Response ----

class IterationDecisionResponse(BaseModel):
    iteration_decision_id: Optional[str] = None
    task_id: Optional[str] = None
    metric_evaluation_id: Optional[str] = None
    iteration_index: int = 0
    status: str = "deciding"

    decision: Optional[str] = None
    decision_confidence: Optional[str] = None
    reasoning: Optional[DecisionReasoning] = None
    evidence_basis: List[EvidenceItem] = []

    # ITERATE path
    iteration_plan: Optional[IterationPlan] = None
    revised_workflow_plan: Optional[RevisedWorkflowPlan] = None
    iteration_rerun_plan: Optional[IterationRerunPlan] = None
    ready_for_iteration: bool = False

    # STOP path
    stop_rationale: Optional[StopRationale] = None

    # Diagnostics
    evidence_bundle: Optional[EvidenceBundle] = None
    system_checks: Optional[SystemChecks] = None
    artifact_manifest: Optional[ArtifactManifest] = None

    warnings: List[str] = []
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IterationDecisionSummary(BaseModel):
    iteration_decision_id: str
    task_id: str
    iteration_index: int
    status: str
    decision: Optional[str] = None
    confidence: Optional[str] = None
    primary_root_cause: Optional[str] = None
    rerun_from_stage: Optional[str] = None
    ready_for_iteration: bool = False
    reasoning_summary: str = ""
    created_at: Optional[datetime] = None
