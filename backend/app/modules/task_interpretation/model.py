from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime


class TaskInterpretation(SQLModel, table=True):
    __tablename__ = "task_interpretation"

    id: Optional[str] = Field(default=None, primary_key=True)
    task_id: Optional[str] = Field(default=None, max_length=255, index=True)
    status: Optional[str] = Field(default="pending", max_length=50, index=True)
    interpreted_task_type: Optional[str] = Field(default=None, max_length=50)
    interpreted_input_modality: Optional[str] = Field(default=None, max_length=50)
    interpreted_material_domain: Optional[str] = Field(default=None, max_length=255)
    confidence_score: Optional[float] = Field(default=None)
    interpretation_json: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB)
    )
    llm_request_json: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB)
    )
    llm_response_json: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB)
    )
    error_message: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, index=True)
    updated_at: Optional[datetime] = Field(default=None)
