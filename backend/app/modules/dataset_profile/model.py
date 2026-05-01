from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime


class DatasetProfile(SQLModel, table=True):
    __tablename__ = "dataset_profile"

    id: Optional[str] = Field(default=None, primary_key=True)
    task_id: Optional[str] = Field(default=None, max_length=255, index=True)
    interpretation_id: Optional[str] = Field(default=None, max_length=255, index=True)
    status: Optional[str] = Field(default="pending", max_length=50, index=True)
    source_type: Optional[str] = Field(default=None, max_length=50, index=True)
    dataset_reference: Optional[str] = Field(default=None, max_length=500)
    loader_name: Optional[str] = Field(default=None, max_length=100)
    n_samples: Optional[int] = Field(default=None)
    n_columns: Optional[int] = Field(default=None)
    input_modality: Optional[str] = Field(default=None, max_length=50)
    target_column: Optional[str] = Field(default=None, max_length=255)
    quality_level: Optional[str] = Field(default=None, max_length=50)
    is_usable_for_ml: Optional[bool] = Field(default=None)
    profile_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    preview_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    error_message: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, index=True)
    updated_at: Optional[datetime] = Field(default=None)
