from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime


class WorkflowPlan(SQLModel, table=True):
    __tablename__ = "workflow_plan"

    id: Optional[str] = Field(default=None, primary_key=True)
    task_id: Optional[str] = Field(default=None, max_length=255, index=True)
    interpretation_id: Optional[str] = Field(default=None, max_length=255, index=True)
    dataset_profile_id: Optional[str] = Field(default=None, max_length=255, index=True)
    status: Optional[str] = Field(default="pending", max_length=50, index=True)
    planning_mode: Optional[str] = Field(default="llm_guided", max_length=50)
    task_type: Optional[str] = Field(default=None, max_length=50)
    input_modality: Optional[str] = Field(default=None, max_length=50)
    primary_metric: Optional[str] = Field(default=None, max_length=50)
    feature_type: Optional[str] = Field(default=None, max_length=100)
    validation_strategy: Optional[str] = Field(default=None, max_length=100)
    hpo_enabled: Optional[bool] = Field(default=None)
    interpretability_enabled: Optional[bool] = Field(default=None)
    confidence_score: Optional[float] = Field(default=None)
    plan_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    llm_request_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    llm_response_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    # New columns
    fe_registry_snapshot_version: Optional[str] = Field(default=None, max_length=50)
    feature_strategy_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    preprocessing_intent_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    workflow_rationale_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    error_message: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, index=True)
    updated_at: Optional[datetime] = Field(default=None)
