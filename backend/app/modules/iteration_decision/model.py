from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


class IterationDecision(SQLModel, table=True):
    __tablename__ = "iteration_decision"

    id: Optional[str] = Field(default=None, primary_key=True)
    task_id: Optional[str] = Field(default=None, index=True, max_length=255)
    metric_evaluation_id: Optional[str] = Field(default=None, index=True, max_length=255)
    pipeline_execution_id: Optional[str] = Field(default=None, max_length=255)
    source_workflow_plan_id: Optional[str] = Field(default=None, max_length=255)
    iteration_index: Optional[int] = Field(default=None, index=True)

    status: Optional[str] = Field(default=None, index=True, max_length=50)
    decision: Optional[str] = Field(default=None, index=True, max_length=20)
    decision_confidence: Optional[str] = Field(default=None, max_length=20)

    # Reasoning
    reasoning_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))

    # ITERATE path
    rerun_from_stage: Optional[str] = Field(default=None, max_length=50)
    iteration_plan_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    revised_workflow_plan_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    iteration_rerun_plan_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    ready_for_iteration: Optional[bool] = Field(default=None)

    # STOP path
    stop_rationale_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))

    # Process artifacts
    evidence_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    system_checks_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    llm_request_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    llm_response_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    validation_result_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))

    artifact_dir: Optional[str] = Field(default=None, max_length=1024)
    error_message: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, index=True)
    updated_at: Optional[datetime] = Field(default=None)
