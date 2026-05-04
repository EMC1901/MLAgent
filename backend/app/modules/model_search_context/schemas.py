from pydantic import BaseModel
from typing import Optional, List
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
    ready_for_model_search_plan: bool = False


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
    warnings: List[str] = []
    errors: List[str] = []
    error_message: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
