from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime


class FeatureEngineering(SQLModel, table=True):
    __tablename__ = "feature_engineering"

    id: Optional[str] = Field(default=None, primary_key=True)
    task_id: Optional[str] = Field(default=None, max_length=255, index=True)
    interpretation_id: Optional[str] = Field(default=None, max_length=255, index=True)
    dataset_profile_id: Optional[str] = Field(default=None, max_length=255, index=True)
    workflow_plan_id: Optional[str] = Field(default=None, max_length=255, index=True)
    status: Optional[str] = Field(default="pending", max_length=50, index=True)
    input_modality: Optional[str] = Field(default=None, max_length=50)
    feature_type: Optional[str] = Field(default=None, max_length=100)
    n_samples: Optional[int] = Field(default=None)
    n_features: Optional[int] = Field(default=None)
    target_column: Optional[str] = Field(default=None, max_length=255)
    artifact_id: Optional[str] = Field(default=None, max_length=255)
    artifact_path: Optional[str] = Field(default=None)
    is_ready_for_pipeline: Optional[bool] = Field(default=None)
    feature_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    preview_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    error_message: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, index=True)
    updated_at: Optional[datetime] = Field(default=None)
