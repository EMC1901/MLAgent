from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel


# ---- Request schemas ----

class WorkflowRefinementCreateRequest(BaseModel):
    result_diagnosis_id: Optional[str] = None
    force_rerun: bool = False
    use_llm: bool = True
    max_iterations: int = 3
    current_iteration_index: Optional[int] = None
    decision_profile: str = "balanced"
    allow_full_workflow_rerun: bool = True
    allow_partial_rerun: bool = True
    minimum_improvement_threshold: Optional[float] = None
    notes: Optional[str] = None


# ---- Internal DTOs ----

class WorkflowRefinementDecisionDTO(BaseModel):
    decision: str = "iterate_refinement"
    decision_confidence_level: str = "medium"
    primary_reason: str = ""
    should_generate_revised_workflow_plan: bool = True
    recommended_rerun_from_stage: Optional[str] = None
    should_proceed_to_final_selection: bool = False


class DecisionReasoning(BaseModel):
    performance_assessment: str = ""
    baseline_assessment: str = ""
    stability_assessment: str = ""
    diagnosis_assessment: str = ""
    cost_assessment: str = ""
    risk_assessment: str = ""
    final_reasoning_summary: str = ""


class EvidenceUsed(BaseModel):
    evidence_id: str = ""
    source_module: str = ""
    evidence_type: str = ""
    source_field: str = ""
    value: Optional[Any] = None
    interpretation: str = ""
    supports_decision: str = ""


class RefinementMetadata(BaseModel):
    source_workflow_plan_id: Optional[str] = None
    source_result_diagnosis_id: Optional[str] = None
    changed_sections: List[str] = []
    preserved_sections: List[str] = []
    recommended_rerun_from_stage: Optional[str] = None


class RevisedWorkflowPlanResponse(BaseModel):
    workflow_plan_id: Optional[str] = None
    status: str = "planned_by_refinement"
    planning_mode: str = "llm_refinement"
    task_summary: Optional[Dict[str, Any]] = None
    data_strategy: Optional[Dict[str, Any]] = None
    feature_strategy: Optional[Dict[str, Any]] = None
    model_strategy: Optional[Dict[str, Any]] = None
    validation_strategy: Optional[Dict[str, Any]] = None
    evaluation_strategy: Optional[Dict[str, Any]] = None
    hpo_strategy: Optional[Dict[str, Any]] = None
    interpretability_strategy: Optional[Dict[str, Any]] = None
    pipeline_generation_input: Optional[Dict[str, Any]] = None
    planning_warnings: List[str] = []
    planning_assumptions: List[str] = []
    llm_reasoning_summary: str = ""
    confidence_score: float = 0.0
    refinement_metadata: Optional[RefinementMetadata] = None


class WorkflowPlanDelta(BaseModel):
    changed_sections: List[str] = []
    preserved_sections: List[str] = []
    feature_strategy_delta: Optional[Dict[str, Any]] = None
    model_strategy_delta: Optional[Dict[str, Any]] = None
    hpo_strategy_delta: Optional[Dict[str, Any]] = None
    validation_strategy_delta: Optional[Dict[str, Any]] = None
    evaluation_strategy_delta: Optional[Dict[str, Any]] = None
    change_reason_map: Dict[str, str] = {}
    diagnosis_to_change_map: Dict[str, str] = {}
    rejected_or_unsafe_changes: List[str] = []


class IterationRerunPlan(BaseModel):
    next_iteration_index: int = 1
    recommended_rerun_from_stage: Optional[str] = None
    rerun_stages: List[str] = []
    reuse_artifacts: List[str] = []
    invalidate_artifacts: List[str] = []
    expected_improvement_targets: List[str] = []
    minimum_improvement_threshold: Optional[float] = None
    stop_after_next_iteration_if_no_gain: bool = True
    reasoning: str = ""


class ExperimentHistorySummary(BaseModel):
    n_iterations_completed: int = 0
    best_metric_so_far: Optional[Any] = None
    best_model_so_far: Optional[str] = None
    metric_trend: str = "unknown"
    previous_decisions: List[str] = []
    repeated_diagnosis_types: List[str] = []
    tried_model_families: List[str] = []
    tried_feature_strategies: List[str] = []
    runtime_cost_summary: Optional[str] = None
    failed_trial_summary: Optional[str] = None


class WorkflowRefinementValidationResult(BaseModel):
    is_valid: bool = True
    decision_valid: bool = True
    reasoning_valid: bool = True
    revised_plan_valid: Optional[bool] = None
    rerun_plan_valid: Optional[bool] = None
    safety_scan_passed: bool = True
    issues: List[str] = []
    warnings: List[str] = []


class LLMWorkflowRefinementResult(BaseModel):
    workflow_refinement_decision: Optional[WorkflowRefinementDecisionDTO] = None
    decision_reasoning: Optional[DecisionReasoning] = None
    evidence_used: List[EvidenceUsed] = []
    revised_workflow_plan: Optional[Dict[str, Any]] = None
    iteration_rerun_plan: Optional[Dict[str, Any]] = None
    confidence_level: str = "medium"


class ArtifactManifest(BaseModel):
    manifest_path: Optional[str] = None
    workflow_refinement_result_path: Optional[str] = None
    llm_refinement_context_path: Optional[str] = None
    llm_request_path: Optional[str] = None
    llm_response_path: Optional[str] = None
    revised_workflow_plan_path: Optional[str] = None
    workflow_plan_delta_path: Optional[str] = None
    iteration_rerun_plan_path: Optional[str] = None
    validation_result_path: Optional[str] = None


# ---- Response schemas ----

class WorkflowRefinementResponse(BaseModel):
    workflow_refinement_id: Optional[str] = None
    task_id: Optional[str] = None
    result_diagnosis_id: Optional[str] = None
    metric_evaluation_id: Optional[str] = None
    iteration_index: int = 0
    status: str = "deciding"
    decision: Optional[str] = None
    decision_confidence_level: Optional[str] = None
    decision_reasoning: Optional[DecisionReasoning] = None
    evidence_used: List[EvidenceUsed] = []
    recommended_rerun_from_stage: Optional[str] = None
    revised_workflow_plan: Optional[RevisedWorkflowPlanResponse] = None
    workflow_plan_delta: Optional[WorkflowPlanDelta] = None
    iteration_rerun_plan: Optional[IterationRerunPlan] = None
    llm_workflow_refinement: Optional[LLMWorkflowRefinementResult] = None
    workflow_refinement_validation_result: Optional[WorkflowRefinementValidationResult] = None
    artifact_manifest: Optional[ArtifactManifest] = None
    ready_for_iteration: bool = False
    warnings: List[str] = []
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
