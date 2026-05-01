from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class InterpretedPredictionTarget(BaseModel):
    raw_target: Optional[str] = None
    normalized_target: Optional[str] = None
    target_category: Optional[str] = None
    target_unit: Optional[str] = None
    target_description: Optional[str] = None


class ModelingIntent(BaseModel):
    primary_goal: Optional[str] = None
    secondary_goals: Optional[List[str]] = []
    optimization_direction: Optional[str] = None
    preferred_metric: Optional[str] = None


class DatasetIntent(BaseModel):
    dataset_reference: Optional[str] = None
    expected_input_columns: Optional[List[str]] = []
    expected_target_column: Optional[str] = None
    requires_structure_file: Optional[bool] = False
    dataset_loading_hint: Optional[dict] = None


class PlanningHint(BaseModel):
    task_family: Optional[str] = None
    input_representation: Optional[str] = None
    requires_feature_engineering: Optional[bool] = False
    requires_model_interpretability: Optional[bool] = False
    suggested_metric_direction: Optional[str] = None


class ConstraintInterpretation(BaseModel):
    hard_constraints: Optional[List[str]] = []
    soft_constraints: Optional[List[str]] = []
    potential_conflicts: Optional[List[str]] = []


class RecommendedDefaults(BaseModel):
    evaluation_metric: Optional[str] = None
    validation_strategy: Optional[str] = None
    baseline_requirement: Optional[bool] = False


class AmbiguityItem(BaseModel):
    field: Optional[str] = None
    message: Optional[str] = None
    severity: Optional[str] = None


class TaskInterpretationCreateRequest(BaseModel):
    force_rerun: Optional[bool] = False
    llm_provider: Optional[str] = None
    model_name: Optional[str] = None


class TaskInterpretationResponse(BaseModel):
    interpretation_id: str
    task_id: str
    status: str
    interpreted_task_type: Optional[str] = None
    interpreted_input_modality: Optional[str] = None
    interpreted_material_domain: Optional[str] = None
    interpreted_prediction_target: Optional[InterpretedPredictionTarget] = None
    modeling_intent: Optional[ModelingIntent] = None
    dataset_intent: Optional[DatasetIntent] = None
    planning_hint: Optional[PlanningHint] = None
    constraint_interpretation: Optional[ConstraintInterpretation] = None
    recommended_defaults: Optional[RecommendedDefaults] = None
    ambiguities: Optional[List[AmbiguityItem]] = []
    warnings: Optional[List[str]] = []
    llm_reasoning_summary: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TaskInterpretationSummaryResponse(BaseModel):
    interpretation_id: str
    task_id: str
    status: str
    interpreted_task_type: Optional[str] = None
    interpreted_input_modality: Optional[str] = None
    confidence_score: Optional[float] = None
