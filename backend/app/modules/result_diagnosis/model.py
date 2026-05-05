from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


class ResultDiagnosis(SQLModel, table=True):
    __tablename__ = "result_diagnosis"

    id: Optional[str] = Field(default=None, primary_key=True)
    task_id: Optional[str] = Field(default=None, index=True, max_length=255)
    metric_evaluation_id: Optional[str] = Field(default=None, index=True, max_length=255)
    pipeline_execution_id: Optional[str] = Field(default=None, index=True, max_length=255)
    status: Optional[str] = Field(default=None, index=True, max_length=50)
    diagnosis_mode: Optional[str] = Field(default=None, index=True, max_length=30)
    main_issue_category: Optional[str] = Field(default=None, index=True, max_length=50)
    performance_level: Optional[str] = Field(default=None, index=True, max_length=30)
    should_refine: Optional[bool] = Field(default=None, index=True)
    ready_for_closed_loop_refinement: Optional[bool] = Field(default=None, index=True)
    llm_used: Optional[bool] = Field(default=None)
    llm_confidence_level: Optional[str] = Field(default=None, max_length=20)
    diagnosis_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    closed_loop_refinement_input_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    llm_request_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    llm_response_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    system_checks_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    diagnosis_artifact_dir: Optional[str] = Field(default=None, max_length=1024)
    error_message: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, index=True)
    updated_at: Optional[datetime] = Field(default=None)
