from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime


class PipelineExecution(SQLModel, table=True):
    __tablename__ = "pipeline_execution"

    id: Optional[str] = Field(default=None, primary_key=True)
    task_id: Optional[str] = Field(default=None, max_length=255, index=True)
    pipeline_generation_id: Optional[str] = Field(default=None, max_length=255, index=True)
    status: Optional[str] = Field(default="pending", max_length=50, index=True)
    execution_mode: Optional[str] = Field(default="sequential", max_length=50)
    task_type: Optional[str] = Field(default=None, max_length=50, index=True)
    target_column: Optional[str] = Field(default=None, max_length=255)
    primary_metric: Optional[str] = Field(default=None, max_length=50)
    n_pipeline_specs: Optional[int] = Field(default=None)
    n_trials_planned: Optional[int] = Field(default=None)
    n_trials_completed: Optional[int] = Field(default=None)
    n_trials_failed: Optional[int] = Field(default=None)
    n_models_trained: Optional[int] = Field(default=None)
    ready_for_metric_evaluation: Optional[bool] = Field(default=None, index=True)
    training_artifact_dir: Optional[str] = Field(default=None, max_length=1024)
    execution_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    metric_evaluation_input_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    runtime_log_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    error_message: Optional[str] = Field(default=None)
    started_at: Optional[datetime] = Field(default=None, index=True)
    finished_at: Optional[datetime] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, index=True)
    updated_at: Optional[datetime] = Field(default=None)
