from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime


class TaskSpecification(SQLModel, table=True):
    __tablename__ = "task_specification"

    id: Optional[str] = Field(default=None, primary_key=True)
    task_name: Optional[str] = Field(default=None, max_length=255)
    task_type: Optional[str] = Field(default=None, max_length=50)
    prediction_target: Optional[str] = Field(default=None, max_length=255)
    dataset_description: Optional[str] = Field(default=None, max_length=2000)
    input_type: Optional[str] = Field(default=None, max_length=50)
    target_column: Optional[str] = Field(default=None, max_length=255)
    evaluation_metric: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = Field(default="received", max_length=50)
    task_spec_json: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB)
    )
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
