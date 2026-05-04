from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ---- Request schemas ----

class ModelSearchPlanCreateRequest(BaseModel):
    force_rerun: bool = False
    use_llm_advisor: bool = True
    max_total_trials_override: Optional[int] = None
    preferred_search_method: Optional[str] = None
    include_models: List[str] = []
    exclude_models: List[str] = []


# ---- Internal DTOs ----

class DatasetContext(BaseModel):
    model_ready_matrix_path: Optional[str] = None
    preprocessing_pipeline_artifact_id: Optional[str] = None
    n_samples: int = 0
    n_features: int = 0
    target_column: Optional[str] = None
    task_type: Optional[str] = None
    primary_metric: Optional[str] = None


class BaselineModelPlan(BaseModel):
    model_id: str
    role: str = "baseline"
    hpo_enabled: bool = False


class CandidateModelPlan(BaseModel):
    model_id: str
    model_family: str
    priority: str = "medium"
    hpo_enabled: bool = True
    reason: Optional[str] = None


class ExcludedModelPlan(BaseModel):
    model_id: str
    reason: Optional[str] = None


class CandidateModelPlanGroup(BaseModel):
    baseline_models: List[BaselineModelPlan] = []
    candidate_models: List[CandidateModelPlan] = []
    excluded_models: List[ExcludedModelPlan] = []


class TrialAllocationItem(BaseModel):
    model_id: str
    max_trials: int


class HPOPlan(BaseModel):
    enabled: bool = True
    search_method: Optional[str] = None
    budget_level: str = "moderate"
    max_total_trials: int = 30
    max_parallel_trials: int = 1
    trial_allocation: List[TrialAllocationItem] = []
    early_stopping: bool = False
    fallback_method: Optional[str] = None


class SearchSpaceParameter(BaseModel):
    name: str
    param_type: str = "float"
    low: Optional[float] = None
    high: Optional[float] = None
    choices: List[str] = []
    sampling: str = "uniform"
    default_value: Optional[str] = None


class SearchSpaceItem(BaseModel):
    model_id: str
    search_space_id: str
    parameters: List[SearchSpaceParameter] = []


class SearchSpacePlan(BaseModel):
    spaces: List[SearchSpaceItem] = []


class ValidationPlan(BaseModel):
    split_strategy: str = "k_fold_cross_validation"
    n_splits: int = 5
    random_state: int = 42
    shuffle: bool = True
    stratification_required: bool = False
    benchmark_split: bool = False


class EvaluationPlan(BaseModel):
    primary_metric: Optional[str] = None
    metric_direction: str = "minimize"
    secondary_metrics: List[str] = []
    scorer_id: Optional[str] = None


class LLMModelSearchAdvice(BaseModel):
    used: bool = False
    confidence_score: float = 0.0
    summary: Optional[str] = None


class SystemValidationResult(BaseModel):
    is_valid: bool = True
    rejected_models: List[str] = []
    rejected_hpo_methods: List[str] = []
    fallback_applied: bool = False
    warnings: List[str] = []


class PipelineGenerationInput(BaseModel):
    model_ready_matrix_path: Optional[str] = None
    preprocessing_pipeline_artifact_id: Optional[str] = None
    target_column: Optional[str] = None
    feature_columns: List[str] = []
    candidate_model_plan: dict = {}
    hpo_plan: dict = {}
    search_space_plan: dict = {}
    validation_plan: dict = {}
    evaluation_plan: dict = {}
    ready_for_pipeline_generation: bool = False


# ---- LLM input/output DTOs ----

class LLMModelSearchContext(BaseModel):
    task_type: Optional[str] = None
    primary_metric: Optional[str] = None
    n_samples: int = 0
    n_features: int = 0
    feature_group_summary: dict = {}
    preprocessing_summary: dict = {}
    updated_model_strategy: dict = {}
    updated_hpo_strategy: dict = {}
    allowed_model_families: List[str] = []
    allowed_hpo_methods: List[str] = []


class LLMModelPriorityNote(BaseModel):
    model_id: str
    priority: str
    reason: Optional[str] = None


class LLMModelSearchSuggestion(BaseModel):
    recommended_model_ids: List[str] = []
    baseline_model_ids: List[str] = []
    excluded_model_ids: List[dict] = []
    hpo_recommendation: dict = {}
    search_space_profile: dict = {}
    model_priority_notes: List[LLMModelPriorityNote] = []
    risk_notes: List[str] = []
    confidence_score: float = 0.0


# ---- Response schema ----

class ModelSearchPlanResponse(BaseModel):
    model_search_plan_id: Optional[str] = None
    task_id: Optional[str] = None
    model_search_context_id: Optional[str] = None
    feature_preprocessing_id: Optional[str] = None
    workflow_plan_id: Optional[str] = None
    status: str = "pending"
    planning_mode: Optional[str] = None
    dataset_context: Optional[DatasetContext] = None
    candidate_model_plan: Optional[CandidateModelPlanGroup] = None
    hpo_plan: Optional[HPOPlan] = None
    search_space_plan: Optional[SearchSpacePlan] = None
    validation_plan: Optional[ValidationPlan] = None
    evaluation_plan: Optional[EvaluationPlan] = None
    llm_model_search_advice: Optional[LLMModelSearchAdvice] = None
    system_validation_result: Optional[SystemValidationResult] = None
    pipeline_generation_input: Optional[PipelineGenerationInput] = None
    warnings: List[str] = []
    errors: List[str] = []
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ModelSearchPlanSummaryResponse(BaseModel):
    model_search_plan_id: str
    task_id: str
    status: str
    task_type: Optional[str] = None
    primary_metric: Optional[str] = None
    n_candidate_models: int = 0
    hpo_enabled: bool = False
    hpo_method: Optional[str] = None
    max_total_trials: int = 0
    ready_for_pipeline_generation: bool = False
    n_warnings: int = 0
    n_errors: int = 0
