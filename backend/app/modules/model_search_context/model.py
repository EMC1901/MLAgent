from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime


class ModelSearchContext(SQLModel, table=True):
    __tablename__ = "model_search_context"

    id: Optional[str] = Field(default=None, primary_key=True)
    task_id: Optional[str] = Field(default=None, max_length=255, index=True)
    workflow_plan_id: Optional[str] = Field(default=None, max_length=255, index=True)
    feature_engineering_id: Optional[str] = Field(default=None, max_length=255, index=True)
    feature_preprocessing_id: Optional[str] = Field(default=None, max_length=255, index=True)
    status: Optional[str] = Field(default="pending", max_length=50, index=True)
    update_mode: Optional[str] = Field(default=None, max_length=50)
    task_type: Optional[str] = Field(default=None, max_length=50)
    target_column: Optional[str] = Field(default=None, max_length=255)
    n_samples: Optional[int] = Field(default=None)
    n_final_features: Optional[int] = Field(default=None)
    primary_metric: Optional[str] = Field(default=None, max_length=50)
    model_strategy_adjusted: Optional[bool] = Field(default=None)
    hpo_strategy_adjusted: Optional[bool] = Field(default=None)
    llm_used: Optional[bool] = Field(default=None)
    llm_confidence_score: Optional[float] = Field(default=None)
    ready_for_model_search_plan: Optional[bool] = Field(default=None, index=True)
    context_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    llm_request_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    llm_response_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    error_message: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, index=True)
    updated_at: Optional[datetime] = Field(default=None)
