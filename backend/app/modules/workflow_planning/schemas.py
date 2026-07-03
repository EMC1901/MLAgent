from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# ---- Request schemas ----

class WorkflowPlanCreateRequest(BaseModel):
    force_rerun: bool = False
    planning_mode: str = "llm_guided"
    llm_provider: Optional[str] = None
    model_name: Optional[str] = None


# ---- Rationale DTO (shared) ----

class DecisionRationale(BaseModel):
    reason: str = ""
    evidence: List[str] = []
    material_science_basis: Optional[str] = ""
    expected_benefit: str = ""
    risk: str = ""
    fallback: str = ""


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


# ---- Enhanced FeatureStrategy ----

class InputModalityAssessment(BaseModel):
    detected_modalities: List[str] = []
    usable_modalities: List[str] = []
    unusable_modalities: List[str] = []
    rationale: str = ""


class SelectedFeatureAction(BaseModel):
    action_id: str = ""
    capability_id: str = ""
    priority: str = "recommended"  # required | recommended | optional | fallback
    input_columns: List[str] = []
    parameters: Dict[str, Any] = {}
    output_feature_group: str = ""
    decision_rationale: DecisionRationale = DecisionRationale()


class RejectedFeatureAction(BaseModel):
    capability_id: str = ""
    reason: str = ""
    evidence: List[str] = []


class FallbackStrategy(BaseModel):
    fallback_actions: List[str] = []
    trigger_conditions: List[str] = []


class FeatureGroupExpectation(BaseModel):
    feature_group: str = ""
    expected_signal: str = ""
    known_limitations: str = ""


class FeatureStrategy(BaseModel):
    # Legacy fields (backward compat)
    feature_type: Optional[str] = None
    executable_featurizers: List[str] = []
    semantic_featurizers: List[str] = []
    unsupported_future_featurizers: List[str] = []
    recommended_featurizers: List[str] = []
    requires_structure_features: bool = False
    feature_selection_required: bool = False
    feature_scaling_required: bool = False

    # New capability-aware fields
    strategy_id: Optional[str] = None
    strategy_version: Optional[str] = None
    input_modality_assessment: Optional[InputModalityAssessment] = None
    selected_feature_actions: List[SelectedFeatureAction] = []
    rejected_feature_actions: List[RejectedFeatureAction] = []
    fallback_strategy: Optional[FallbackStrategy] = None
    feature_group_expectations: List[FeatureGroupExpectation] = []


# ---- PreprocessingIntent ----

class PreprocessingIntent(BaseModel):
    intent_id: Optional[str] = None
    high_level_goals: List[str] = []
    risks_to_check_after_feature_engineering: List[str] = []
    non_final_notes: str = "Final executable preprocessing decisions will be made by Feature Preprocessing after Feature Engineering output is available."


# ---- WorkflowRationale ----

class WorkflowRationale(BaseModel):
    overall_reasoning_summary: str = ""
    key_assumptions: List[str] = []
    known_risks: List[str] = []


# ---- FallbackRule ----

class FallbackRule(BaseModel):
    trigger: str = ""
    action: str = ""
    rationale: str = ""


class ExecutionHints(BaseModel):
    module_order: List[str] = []
    fallback_rules: List[FallbackRule] = []
    resource_guidance: str = ""


class ModelDecisionRationale(BaseModel):
    reason: str = ""
    evidence: List[str] = []
    expected_performance: str = ""
    risk: str = ""
    fallback: str = ""


class SelectedModelAction(BaseModel):
    action_id: str = ""
    model_family: str = ""
    priority: str = "recommended"  # required | recommended | optional | fallback
    decision_rationale: ModelDecisionRationale = ModelDecisionRationale()


class RejectedModelAction(BaseModel):
    model_family: str = ""
    reason: str = ""
    evidence: List[str] = []


class ModelStrategy(BaseModel):
    candidate_model_families: List[str] = []
    baseline_models: List[str] = []
    preferred_model_bias: str = "balance_accuracy_and_interpretability"
    excluded_model_families: List[str] = []
    # New detailed rationale fields
    selected_model_actions: List[SelectedModelAction] = []
    rejected_model_actions: List[RejectedModelAction] = []
    model_selection_rationale_summary: str = ""


class ValidationStrategy(BaseModel):
    split_strategy: str = "k_fold_cross_validation"
    n_splits: int = 5
    test_size: Optional[float] = None
    external_test_enabled: bool = True
    external_test_size: Optional[float] = 0.2
    cv_strategy: Optional[str] = None
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
    preprocessing_intent: Optional[PreprocessingIntent] = None
    model_strategy: Optional[ModelStrategy] = None
    validation_strategy: Optional[ValidationStrategy] = None
    evaluation_strategy: Optional[EvaluationStrategy] = None
    hpo_strategy: Optional[HPOStrategy] = None
    interpretability_strategy: Optional[InterpretabilityStrategy] = None
    pipeline_generation_input: Optional[PipelineGenerationInput] = None
    workflow_rationale: Optional[WorkflowRationale] = None
    execution_hints: Optional[ExecutionHints] = None
    fe_registry_snapshot_version: Optional[str] = None
    planning_warnings: Optional[List[str]] = []
    planning_assumptions: Optional[List[str]] = []
    llm_reasoning_summary: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ---- Sub-resource response schemas ----

class FeatureStrategyResponse(BaseModel):
    workflow_plan_id: str
    feature_strategy: FeatureStrategy
    fe_registry_snapshot_version: Optional[str] = None


class FeatureStrategyRationaleResponse(BaseModel):
    workflow_plan_id: str
    rationales: List[DecisionRationale] = []
    rejected_rationales: List[RejectedFeatureAction] = []


class ModelStrategyResponse(BaseModel):
    workflow_plan_id: str
    model_strategy: ModelStrategy


class PreprocessingIntentResponse(BaseModel):
    workflow_plan_id: str
    preprocessing_intent: PreprocessingIntent
