from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ---- Request schemas ----

class WorkflowPlanCreateRequest(BaseModel):
    force_rerun: bool = False
    planning_mode: str = "llm_guided"
    llm_provider: Optional[str] = None
    model_name: Optional[str] = None


# ---- Internal DTOs for strategy objects ----

class TaskSummary(BaseModel):
    task_type: Optional[str] = None
    input_modality: Optional[str] = None
    prediction_target: Optional[str] = None
    material_domain: Optional[str] = None
    primary_goal: Optional[str] = None


class TargetHandling(BaseModel):
    requires_transformation_check: bool = False
    recommended_transformation: str = "none"


class DataStrategy(BaseModel):
    input_columns: List[str] = []
    target_column: Optional[str] = None
    required_cleaning_steps: List[str] = []
    target_handling: TargetHandling = TargetHandling()
    duplicate_handling: str = "none"
    missing_value_strategy: str = "no_missing_values_detected"


class FeatureStrategy(BaseModel):
    feature_type: Optional[str] = None
    executable_featurizers: List[str] = []
    semantic_featurizers: List[str] = []
    unsupported_future_featurizers: List[str] = []
    recommended_featurizers: List[str] = []
    requires_structure_features: bool = False
    feature_selection_required: bool = False
    feature_scaling_required: bool = False


class ModelStrategy(BaseModel):
    candidate_model_families: List[str] = []
    baseline_models: List[str] = []
    preferred_model_bias: str = "balance_accuracy_and_interpretability"
    excluded_model_families: List[str] = []


class ValidationStrategy(BaseModel):
    split_strategy: str = "k_fold_cross_validation"
    n_splits: int = 5
    test_size: Optional[float] = None
    random_state: int = 42
    stratification_required: bool = False


class EvaluationStrategy(BaseModel):
    primary_metric: Optional[str] = None
    secondary_metrics: List[str] = []
    metric_direction: str = "minimize"


class HPOStrategy(BaseModel):
    enabled: bool = True
    search_method: str = "random_search"
    budget_level: str = "medium"
    max_trials: int = 30


class InterpretabilityStrategy(BaseModel):
    enabled: bool = True
    methods: List[str] = []
    priority: str = "medium"


class RequiredComponents(BaseModel):
    data_cleaner: bool = False
    featurizer: bool = False
    model_trainer: bool = False
    evaluator: bool = False


class PipelineGenerationInput(BaseModel):
    pipeline_steps: List[str] = []
    required_components: RequiredComponents = RequiredComponents()


# ---- Response schema ----

class WorkflowPlanResponse(BaseModel):
    workflow_plan_id: str
    task_id: str
    interpretation_id: Optional[str] = None
    dataset_profile_id: Optional[str] = None
    status: str
    planning_mode: str = "llm_guided"
    task_summary: Optional[TaskSummary] = None
    data_strategy: Optional[DataStrategy] = None
    feature_strategy: Optional[FeatureStrategy] = None
    model_strategy: Optional[ModelStrategy] = None
    validation_strategy: Optional[ValidationStrategy] = None
    evaluation_strategy: Optional[EvaluationStrategy] = None
    hpo_strategy: Optional[HPOStrategy] = None
    interpretability_strategy: Optional[InterpretabilityStrategy] = None
    pipeline_generation_input: Optional[PipelineGenerationInput] = None
    planning_warnings: Optional[List[str]] = []
    planning_assumptions: Optional[List[str]] = []
    llm_reasoning_summary: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
