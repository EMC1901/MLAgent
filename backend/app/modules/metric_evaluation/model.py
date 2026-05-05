from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


class MetricEvaluation(SQLModel, table=True):
    __tablename__ = "metric_evaluation"

    id: Optional[str] = Field(default=None, primary_key=True)
    task_id: Optional[str] = Field(default=None, index=True, max_length=255)
    pipeline_execution_id: Optional[str] = Field(default=None, index=True, max_length=255)
    pipeline_generation_id: Optional[str] = Field(default=None, index=True, max_length=255)
    status: Optional[str] = Field(default=None, index=True, max_length=50)
    task_type: Optional[str] = Field(default=None, index=True, max_length=50)
    target_column: Optional[str] = Field(default=None, max_length=255)
    primary_metric: Optional[str] = Field(default=None, index=True, max_length=50)
    metric_direction: Optional[str] = Field(default=None, max_length=20)
    n_trials_evaluated: Optional[int] = Field(default=None)
    n_trials_failed: Optional[int] = Field(default=None)
    n_models_evaluated: Optional[int] = Field(default=None)
    best_trial_id: Optional[str] = Field(default=None, index=True, max_length=255)
    best_model_id: Optional[str] = Field(default=None, index=True, max_length=255)
    best_pipeline_spec_id: Optional[str] = Field(default=None, index=True, max_length=255)
    best_primary_metric_value: Optional[float] = Field(default=None)
    ready_for_result_diagnosis: Optional[bool] = Field(default=None, index=True)
    evaluation_artifact_dir: Optional[str] = Field(default=None, max_length=1024)
    evaluation_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    result_diagnosis_input_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    metric_summary_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    model_ranking_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    error_message: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, index=True)
    updated_at: Optional[datetime] = Field(default=None)
