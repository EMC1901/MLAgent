from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


class InterpretabilityAnalysis(SQLModel, table=True):
    __tablename__ = "interpretability_analysis"

    id: Optional[str] = Field(default=None, primary_key=True)
    task_id: Optional[str] = Field(default=None, index=True, max_length=255)
    metric_evaluation_id: Optional[str] = Field(default=None, index=True, max_length=255)
    pipeline_execution_id: Optional[str] = Field(default=None, index=True, max_length=255)
    status: Optional[str] = Field(default=None, index=True, max_length=50)
    analysis_profile: Optional[str] = Field(default=None, index=True, max_length=50)
    final_model_id: Optional[str] = Field(default=None, index=True, max_length=255)
    final_model_family: Optional[str] = Field(default=None, index=True, max_length=255)
    final_trial_id: Optional[str] = Field(default=None, index=True, max_length=255)
    methods_used_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    global_feature_importance_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    permutation_importance_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    shap_summary_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    local_explanations_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    high_error_sample_analysis_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    cross_method_consensus_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    partial_dependence_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    residual_analysis_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    correlation_analysis_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    physics_constraint_check_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    material_insight_summary_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    llm_summary_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    scientific_insight_report_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    final_output_input_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    artifact_manifest_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    feature_group_summary_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    ready_for_final_output: Optional[bool] = Field(default=None, index=True)
    llm_used: Optional[bool] = Field(default=None)
    llm_confidence_level: Optional[str] = Field(default=None, max_length=20)
    llm_request_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    llm_response_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    error_message: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, index=True)
    updated_at: Optional[datetime] = Field(default=None)

    # ── Debug & observability fields ──
    warnings_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    debug_trace_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    request_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    input_snapshot_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    current_step: Optional[str] = Field(default=None, max_length=100)
    last_completed_step: Optional[str] = Field(default=None, max_length=100)
    started_at: Optional[datetime] = Field(default=None)
    finished_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[float] = Field(default=None)
