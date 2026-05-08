from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


class FinalOutput(SQLModel, table=True):
    __tablename__ = "final_output"

    id: Optional[str] = Field(default=None, primary_key=True)
    task_id: Optional[str] = Field(default=None, index=True, max_length=255)
    interpretability_analysis_id: Optional[str] = Field(default=None, index=True, max_length=255)
    final_pipeline_selection_id: Optional[str] = Field(default=None, index=True, max_length=255)
    status: Optional[str] = Field(default=None, index=True, max_length=50)
    report_profile: Optional[str] = Field(default=None, index=True, max_length=50)
    final_model_id: Optional[str] = Field(default=None, index=True, max_length=255)
    final_trial_id: Optional[str] = Field(default=None, index=True, max_length=255)
    primary_metric: Optional[str] = Field(default=None, index=True, max_length=255)
    primary_metric_value: Optional[float] = Field(default=None)
    ready_for_delivery: Optional[bool] = Field(default=None, index=True)
    final_output_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    final_report_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    llm_report_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    workflow_trace_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    reproducibility_summary_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    artifact_manifest_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    output_package_manifest_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    download_links_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    llm_used: Optional[bool] = Field(default=None)
    llm_confidence_level: Optional[str] = Field(default=None, max_length=20)
    llm_request_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    llm_response_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    artifact_dir: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, index=True)
    updated_at: Optional[datetime] = Field(default=None)
