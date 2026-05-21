from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ---- Request schemas ----

class PipelineGenerationCreateRequest(BaseModel):
    force_rerun: bool = False
    use_llm_reviewer: bool = True
    include_baselines: bool = True
    include_hpo_candidates: bool = True
    pipeline_profile: str = "standard"
    max_pipeline_specs_override: Optional[int] = None
    notes: Optional[str] = None


# ---- Internal DTOs ----

class ArtifactManifest(BaseModel):
    model_ready_matrix_path: Optional[str] = None
    preprocessor_artifact_path: Optional[str] = None
    metadata_path: Optional[str] = None
    model_ready_exists: bool = False
    preprocessor_exists: bool = False
    feature_columns: List[str] = []
    n_features: int = 0
    target_column: Optional[str] = None
    is_complete: bool = False


class ComponentBinding(BaseModel):
    model_id: str
    model_family: Optional[str] = None
    model_registry_valid: bool = False
    hpo_method: Optional[str] = None
    hpo_registry_valid: bool = False
    validation_strategy: Optional[str] = None
    validation_strategy_valid: bool = False
    primary_metric: Optional[str] = None
    metric_valid: bool = False
    preprocessor_artifact_bound: bool = False
    model_ready_matrix_bound: bool = False


class ComponentBindingResult(BaseModel):
    bindings: List[ComponentBinding] = []
    all_valid: bool = False
    errors: List[str] = []


class SafetyConstraints(BaseModel):
    max_runtime_seconds: int = 3600
    max_memory_mb: int = 4096
    allow_unregistered_components: bool = False
    allow_dynamic_code: bool = False
    allow_network_access: bool = False


class PipelineSpec(BaseModel):
    pipeline_spec_id: str
    pipeline_role: str = "candidate"
    model_id: str
    model_family: Optional[str] = None
    model_display_name: Optional[str] = None
    priority: str = "medium"
    hpo_enabled: bool = False
    search_space_ref: Optional[str] = None
    fixed_params: dict = {}
    search_space: Optional[dict] = None
    validation_plan_ref: str = "default_validation"
    evaluation_plan_ref: str = "default_evaluation"
    input_artifact_ref: Optional[str] = None
    preprocessor_artifact_ref: Optional[str] = None
    component_bindings: dict = {}
    safety_constraints: Optional[SafetyConstraints] = None
    execution_ready: bool = False
    warnings: List[str] = []


class TrialAllocationItem(BaseModel):
    model_id: str
    pipeline_spec_id: Optional[str] = None
    max_trials: int
    role: str = "candidate"


class BaselineTrialPolicy(BaseModel):
    single_run: bool = True
    description: str = "Baseline models run once without HPO."


class CandidateTrialPolicy(BaseModel):
    expand_by_search_space: bool = True
    description: str = "Candidate models expand trials according to HPO search method."


class EarlyStoppingPolicy(BaseModel):
    enabled: bool = False
    patience: int = 10
    min_delta: float = 0.001


class FallbackPolicy(BaseModel):
    enabled: bool = True
    fallback_model_id: Optional[str] = "dummy_mean"
    description: str = "If HPO fails, fallback to fixed-parameter model."


class TrialPlan(BaseModel):
    trial_plan_id: str
    hpo_enabled: bool = False
    search_method: Optional[str] = None
    max_total_trials: int = 0
    max_parallel_trials: int = 1
    trial_allocation: List[TrialAllocationItem] = []
    baseline_trial_policy: Optional[BaselineTrialPolicy] = None
    candidate_trial_policy: Optional[CandidateTrialPolicy] = None
    early_stopping_policy: Optional[EarlyStoppingPolicy] = None
    fallback_policy: Optional[FallbackPolicy] = None


class ExecutionConstraints(BaseModel):
    max_runtime_seconds: int = 3600
    max_memory_mb: int = 4096
    allow_unregistered_components: bool = False
    allow_dynamic_code: bool = False


class ExecutionInput(BaseModel):
    pipeline_generation_id: str
    pipeline_bundle_id: str
    task_id: str
    task_type: Optional[str] = None
    model_ready_matrix_path: Optional[str] = None
    preprocessor_artifact_path: Optional[str] = None
    target_column: Optional[str] = None
    feature_columns: List[str] = []
    pipeline_specs: List[PipelineSpec] = []
    trial_plan: Optional[TrialPlan] = None
    validation_plan: dict = {}
    evaluation_plan: dict = {}
    execution_constraints: Optional[ExecutionConstraints] = None
    ready_for_execution: bool = False


class PipelineBundle(BaseModel):
    bundle_id: str
    task_id: str
    model_search_context_id: str
    task_type: Optional[str] = None
    target_column: Optional[str] = None
    feature_columns: List[str] = []
    primary_metric: Optional[str] = None
    metric_direction: str = "minimize"
    model_ready_matrix_path: Optional[str] = None
    preprocessor_artifact_path: Optional[str] = None
    pipeline_specs: List[PipelineSpec] = []
    validation_plan: dict = {}
    evaluation_plan: dict = {}
    hpo_plan: dict = {}
    execution_policy: dict = {}
    created_by: str = "pipeline_generation_module"


class PipelineValidationResult(BaseModel):
    is_valid: bool = False
    structure_valid: bool = False
    registry_valid: bool = False
    artifact_valid: bool = False
    task_type_compatible: bool = False
    search_space_valid: bool = False
    trial_valid: bool = False
    data_fields_valid: bool = False
    execution_input_valid: bool = False
    errors: List[str] = []
    warnings: List[str] = []


class SafetyCheckResult(BaseModel):
    is_safe: bool = False
    checks: dict = {}
    errors: List[str] = []
    warnings: List[str] = []


class LLMAdvisoryChecklistItem(BaseModel):
    dimension: str = ""
    status: str = "pass"  # pass / warning / not_applicable
    comment: str = ""


class LLMAdvisoryRisk(BaseModel):
    category: str = ""
    severity: str = "low"  # low / medium / high
    message: str = ""
    suggested_action: str = ""


class LLMAdvisoryReview(BaseModel):
    enabled: bool = True
    review_status: str = "advisory_completed"  # advisory_completed / advisory_failed / advisory_unavailable
    execution_impact: str = "non_blocking"  # non_blocking / potentially_blocking
    risk_level: str = "none"  # none / low / medium / high
    confidence_level: str = "medium"  # low / medium / high
    checklist: List[LLMAdvisoryChecklistItem] = []
    blocking_issues: List[LLMAdvisoryRisk] = []
    non_blocking_risks: List[LLMAdvisoryRisk] = []
    resource_warnings: List[str] = []
    future_improvement_suggestions: List[str] = []
    normalization_notes: List[str] = []
    raw_llm_summary: dict = {}


# ---- Response schemas ----

class PipelineGenerationResponse(BaseModel):
    pipeline_generation_id: Optional[str] = None
    task_id: Optional[str] = None
    model_search_context_id: Optional[str] = None
    feature_preprocessing_id: Optional[str] = None
    status: str = "pending"
    generation_mode: Optional[str] = None
    n_pipeline_specs: int = 0
    n_baseline_specs: int = 0
    n_hpo_specs: int = 0
    pipeline_bundle: Optional[PipelineBundle] = None
    pipeline_specs: List[PipelineSpec] = []
    trial_plan: Optional[TrialPlan] = None
    component_binding_result: Optional[ComponentBindingResult] = None
    artifact_manifest: Optional[ArtifactManifest] = None
    pipeline_validation_result: Optional[PipelineValidationResult] = None
    safety_check_result: Optional[SafetyCheckResult] = None
    llm_advisory_review: Optional[LLMAdvisoryReview] = None
    execution_input: Optional[ExecutionInput] = None
    ready_for_execution: bool = False
    warnings: List[str] = []
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PipelineGenerationSummaryResponse(BaseModel):
    pipeline_generation_id: str
    task_id: str
    status: str
    n_pipeline_specs: int = 0
    n_baseline_specs: int = 0
    n_hpo_specs: int = 0
    hpo_enabled: bool = False
    ready_for_execution: bool = False
    warnings: List[str] = []
    created_at: Optional[datetime] = None
