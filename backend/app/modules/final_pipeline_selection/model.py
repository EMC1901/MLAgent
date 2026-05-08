from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


class FinalPipelineSelection(SQLModel, table=True):
    __tablename__ = "final_pipeline_selection"

    id: Optional[str] = Field(default=None, primary_key=True)
    task_id: Optional[str] = Field(default=None, index=True, max_length=255)
    workflow_refinement_id: Optional[str] = Field(default=None, index=True, max_length=255)
    metric_evaluation_id: Optional[str] = Field(default=None, index=True, max_length=255)
    pipeline_execution_id: Optional[str] = Field(default=None, index=True, max_length=255)
    pipeline_generation_id: Optional[str] = Field(default=None, index=True, max_length=255)
    status: Optional[str] = Field(default=None, index=True, max_length=50)
    selection_profile: Optional[str] = Field(default=None, index=True, max_length=50)
    final_pipeline_spec_id: Optional[str] = Field(default=None, index=True, max_length=255)
    final_model_id: Optional[str] = Field(default=None, index=True, max_length=255)
    final_model_family: Optional[str] = Field(default=None, index=True, max_length=255)
    final_trial_id: Optional[str] = Field(default=None, index=True, max_length=255)
    primary_metric: Optional[str] = Field(default=None, index=True, max_length=50)
    primary_metric_value: Optional[float] = Field(default=None)
    selection_score: Optional[float] = Field(default=None)
    ready_for_interpretability_analysis: Optional[bool] = Field(default=None, index=True)
    llm_used: Optional[bool] = Field(default=None)
    llm_confidence_level: Optional[str] = Field(default=None, max_length=20)
    selection_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    candidate_ranking_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    system_selection_reason_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    llm_selection_explanation_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    candidate_difference_summary_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    human_review_notes_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    risk_notes_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    interpretability_analysis_input_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    artifact_manifest_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    llm_request_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    llm_response_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    error_message: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, index=True)
    updated_at: Optional[datetime] = Field(default=None)
