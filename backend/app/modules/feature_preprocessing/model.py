from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime


class FeaturePreprocessing(SQLModel, table=True):
    __tablename__ = "feature_preprocessing"

    id: Optional[str] = Field(default=None, primary_key=True)
    task_id: Optional[str] = Field(default=None, max_length=255, index=True)
    interpretation_id: Optional[str] = Field(default=None, max_length=255, index=True)
    dataset_profile_id: Optional[str] = Field(default=None, max_length=255, index=True)
    workflow_plan_id: Optional[str] = Field(default=None, max_length=255, index=True)
    feature_engineering_id: Optional[str] = Field(default=None, max_length=255, index=True)
    status: Optional[str] = Field(default="pending", max_length=50, index=True)
    n_samples: Optional[int] = Field(default=None)
    n_raw_features: Optional[int] = Field(default=None)
    n_valid_features: Optional[int] = Field(default=None)
    n_final_features: Optional[int] = Field(default=None)
    n_dropped_features: Optional[int] = Field(default=None)
    target_column: Optional[str] = Field(default=None, max_length=255)
    model_ready_artifact_id: Optional[str] = Field(default=None, max_length=255)
    model_ready_artifact_path: Optional[str] = Field(default=None)
    preprocessor_artifact_id: Optional[str] = Field(default=None, max_length=255)
    preprocessor_artifact_path: Optional[str] = Field(default=None)
    is_ready_for_model_search: Optional[bool] = Field(default=None, index=True)
    preprocessing_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    preview_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    # New columns
    preprocessing_plan_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    execution_report_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    removed_features_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    feature_lineage_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    explainability_report_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    provenance_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    registry_snapshot_version: Optional[str] = Field(default=None, max_length=50)
    error_message: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, index=True)
    updated_at: Optional[datetime] = Field(default=None)
