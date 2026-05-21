from pydantic import BaseModel
from typing import Any, Optional, List
from datetime import datetime


# ---- Request schemas ----

class ModelSearchContextCreateRequest(BaseModel):
    force_rerun: bool = False
    use_llm_advisor: bool = True
    adjust_model_strategy: bool = True
    adjust_hpo_strategy: bool = True
    adjust_validation_strategy: bool = True
    adjust_evaluation_strategy: bool = False


# ---- Internal DTOs ----

class DatasetEffectiveProfile(BaseModel):
    n_samples: int = 0
    n_raw_features: int = 0
    n_final_features: int = 0
    n_dropped_features: int = 0
    feature_reduction_ratio: float = 0.0
    target_column: Optional[str] = None
    task_type: Optional[str] = None


class FeatureGroupSummary(BaseModel):
    retained_groups: List[str] = []
    dropped_groups: List[str] = []
    partially_retained_groups: List[str] = []
    low_effective_feature_warning: bool = False


class PreprocessingSummary(BaseModel):
    imputation_executed: bool = False
    scaling_executed: bool = False
    feature_selection_executed: bool = False
    categorical_encoding_executed: bool = False
    preprocessing_pipeline_artifact_id: Optional[str] = None


class StrategyChangeRationale(BaseModel):
    """LLM's detailed rationale for a single strategy field change."""
    reason: str = ""
    evidence: List[str] = []
    expected_benefit: str = ""
    risk: str = ""
    fallback: str = ""


class StrategyChange(BaseModel):
    """A single field-level change in the model search strategy."""
    strategy_area: str = ""  # "model" | "hpo" | "validation" | "evaluation"
    field_path: str = ""  # e.g. "candidate_model_families", "search_method"
    original_value: Any = None
    updated_value: Any = None
    change_type: str = "modified"  # "modified" | "added" | "removed" | "confirmed"
    decision_rationale: Optional[StrategyChangeRationale] = None


class LLMStrategyAdvice(BaseModel):
    candidate_model_families: List[str] = []
    baseline_models: List[str] = []
    preferred_model_bias: Optional[str] = None
    hpo_search_method: Optional[str] = None
    hpo_budget_level: str = "moderate"
    max_trials: int = 30
    validation_split_strategy: Optional[str] = None
    n_splits: int = 5
    adjustment_reasons: List[str] = []
    risk_notes: List[str] = []
    confidence_score: float = 0.0


class SystemValidationResult(BaseModel):
    is_valid: bool = False
    rejected_suggestions: List[str] = []
    fallback_applied: bool = False


class StrategyAdjustment(BaseModel):
    model_strategy_adjusted: bool = False
    hpo_strategy_adjusted: bool = False
    validation_strategy_adjusted: bool = False
    evaluation_strategy_adjusted: bool = False
    adjustment_reasons: List[str] = []


class ModelSearchContextInput(BaseModel):
    model_ready_matrix_path: Optional[str] = None
    preprocessing_pipeline_artifact_id: Optional[str] = None
    target_column: Optional[str] = None
    feature_columns: List[str] = []
    task_type: Optional[str] = None
    primary_metric: Optional[str] = None
    model_strategy: dict = {}
    validation_strategy: dict = {}
    evaluation_strategy: dict = {}
    hpo_strategy: dict = {}
    ready_for_pipeline_generation: bool = False


# ---- Execution Plan DTOs (merged from model_search) ----

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
    allocation_rationale: Optional[str] = None


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
    choices: list = []  # mixed types: strings ("sqrt", "log2") + floats (0.5, 1.0) for sklearn
    sampling: str = "uniform"
    default_value: Optional[str] = None
    override_rationale: Optional[str] = None


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


# ---- Response schema ----

class ModelSearchContextResponse(BaseModel):
    context_id: str
    task_id: str
    workflow_plan_id: Optional[str] = None
    feature_engineering_id: Optional[str] = None
    feature_preprocessing_id: Optional[str] = None
    status: str
    update_mode: Optional[str] = None
    dataset_effective_profile: Optional[DatasetEffectiveProfile] = None
    feature_group_summary: Optional[FeatureGroupSummary] = None
    preprocessing_summary: Optional[PreprocessingSummary] = None
    llm_strategy_advice: Optional[LLMStrategyAdvice] = None
    system_validation_result: Optional[SystemValidationResult] = None
    strategy_adjustment: Optional[StrategyAdjustment] = None
    updated_model_strategy: dict = {}
    updated_hpo_strategy: dict = {}
    updated_validation_strategy: dict = {}
    updated_evaluation_strategy: dict = {}
    model_search_context_input: Optional[ModelSearchContextInput] = None
    # Execution plans (merged from model_search)
    candidate_model_plan: Optional[CandidateModelPlanGroup] = None
    hpo_plan: Optional[HPOPlan] = None
    search_space_plan: Optional[SearchSpacePlan] = None
    validation_plan: Optional[ValidationPlan] = None
    evaluation_plan: Optional[EvaluationPlan] = None
    pipeline_generation_input: Optional[PipelineGenerationInput] = None
    strategy_changes: List[StrategyChange] = []
    strategy_change_summary: Optional[str] = None
    warnings: List[str] = []
    errors: List[str] = []
    error_message: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
