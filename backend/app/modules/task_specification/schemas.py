from pydantic import BaseModel
from typing import Optional, List, Generic, TypeVar
from datetime import datetime

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    error_code: Optional[str] = None


class TaskSpecificationCreateRequest(BaseModel):
    task_name: Optional[str] = None
    task_description: Optional[str] = None
    material_system: Optional[str] = None
    prediction_target: Optional[str] = None
    task_type: Optional[str] = None
    dataset_description: Optional[str] = None
    input_type: Optional[str] = None
    target_column: Optional[str] = None
    evaluation_metric: Optional[str] = None
    user_priority: Optional[List[str]] = []
    constraints: Optional[List[str]] = []


class TaskSpecificationUpdateRequest(BaseModel):
    task_name: Optional[str] = None
    task_description: Optional[str] = None
    material_system: Optional[str] = None
    prediction_target: Optional[str] = None
    task_type: Optional[str] = None
    dataset_description: Optional[str] = None
    input_type: Optional[str] = None
    target_column: Optional[str] = None
    evaluation_metric: Optional[str] = None
    user_priority: Optional[List[str]] = None
    constraints: Optional[List[str]] = None


class TaskSpecificationResponse(BaseModel):
    task_id: str
    task_name: Optional[str] = None
    task_description: Optional[str] = None
    material_system: Optional[str] = None
    prediction_target: Optional[str] = None
    task_type: Optional[str] = None
    dataset_description: Optional[str] = None
    input_type: Optional[str] = None
    target_column: Optional[str] = None
    evaluation_metric: Optional[str] = None
    user_priority: Optional[List[str]] = []
    constraints: Optional[List[str]] = []
    status: str
    missing_fields: Optional[List[str]] = []
    validation_messages: Optional[List[str]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TaskSummaryResponse(BaseModel):
    task_id: str
    task_name: Optional[str] = None
    task_type: Optional[str] = None
    prediction_target: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ValidationResultResponse(BaseModel):
    status: str
    missing_fields: Optional[List[str]] = []
    validation_messages: Optional[List[str]] = []
    warnings: Optional[List[str]] = []
