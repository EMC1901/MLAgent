from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ---- Internal DTOs ----

class ColumnInfo(BaseModel):
    name: str
    role: str  # "input" | "target" | "other"
    dtype: str
    missing_count: int = 0
    missing_ratio: float = 0.0


class DatasetSource(BaseModel):
    source_type: str
    dataset_reference: Optional[str] = None
    loader: Optional[str] = None
    loaded_from: Optional[str] = None
    file_name: Optional[str] = None


class DatasetSchema(BaseModel):
    n_samples: int = 0
    n_columns: int = 0
    columns: List[ColumnInfo] = []
    input_columns: List[str] = []
    target_column: Optional[str] = None


class ModalityCheck(BaseModel):
    expected_input_modality: Optional[str] = None
    detected_input_modality: Optional[str] = None
    is_consistent: bool = True
    messages: List[str] = []


class TargetProfileRegression(BaseModel):
    target_column: str
    task_type: str = "regression"
    dtype: Optional[str] = None
    missing_count: int = 0
    missing_ratio: float = 0.0
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    skewness: Optional[float] = None
    outlier_count: int = 0


class ClassDistribution(BaseModel):
    label: str
    count: int
    ratio: float


class TargetProfileClassification(BaseModel):
    target_column: str
    task_type: str = "classification"
    dtype: Optional[str] = None
    missing_count: int = 0
    missing_ratio: float = 0.0
    class_count: int = 0
    class_distribution: List[ClassDistribution] = []
    majority_class_ratio: Optional[float] = None
    minority_class_count: int = 0
    is_imbalanced: bool = False


class TargetProfile(BaseModel):
    target_column: Optional[str] = None
    task_type: Optional[str] = None
    dtype: Optional[str] = None
    missing_count: int = 0
    missing_ratio: float = 0.0
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    skewness: Optional[float] = None
    outlier_count: int = 0
    class_count: Optional[int] = None
    class_distribution: Optional[List[ClassDistribution]] = None
    majority_class_ratio: Optional[float] = None
    minority_class_count: Optional[int] = None
    is_imbalanced: Optional[bool] = None


class MissingValues(BaseModel):
    total_missing: int = 0
    columns_with_missing: List[str] = []


class Duplicates(BaseModel):
    duplicate_rows: int = 0
    duplicate_input_samples: int = 0


class InvalidRows(BaseModel):
    count: int = 0
    examples: List[dict] = []


class DataQuality(BaseModel):
    missing_values: MissingValues = MissingValues()
    duplicates: Duplicates = Duplicates()
    invalid_rows: InvalidRows = InvalidRows()
    warnings: List[str] = []
    errors: List[str] = []


class ProfilingSummary(BaseModel):
    is_loadable: bool = False
    is_usable_for_ml: bool = False
    sample_size_level: str = "very_small"
    quality_level: str = "unusable"
    main_issues: List[str] = []
    recommended_next_step: Optional[str] = None


class WorkflowPlanningInput(BaseModel):
    input_modality: Optional[str] = None
    task_type: Optional[str] = None
    target_column: Optional[str] = None
    input_columns: List[str] = []
    n_samples: int = 0
    n_columns: int = 0
    n_features_raw: int = 0
    sample_size_level: str = "very_small"
    has_missing_values: bool = False
    has_duplicates: bool = False
    requires_cleaning: bool = False
    requires_target_transformation_check: bool = False
    target_distribution: Optional[dict] = None
    quality_level: str = "unusable"
    is_usable_for_ml: bool = False


# ---- Request schemas ----

class DatasetProfileCreateRequest(BaseModel):
    force_rerun: bool = False
    uploaded_file_id: Optional[str] = None
    uploaded_file_path: Optional[str] = None
    max_preview_rows: int = 20


# ---- Response schemas ----

class DatasetProfileResponse(BaseModel):
    dataset_profile_id: str
    task_id: str
    interpretation_id: Optional[str] = None
    status: str
    dataset_source: Optional[DatasetSource] = None
    dataset_schema: Optional[DatasetSchema] = None
    modality_check: Optional[ModalityCheck] = None
    target_profile: Optional[TargetProfile] = None
    data_quality: Optional[DataQuality] = None
    profiling_summary: Optional[ProfilingSummary] = None
    workflow_planning_input: Optional[WorkflowPlanningInput] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DatasetFileUploadResponse(BaseModel):
    file_id: str
    file_name: str
    file_size_bytes: int
    n_rows: int
    n_columns: int
    columns: List[str] = []
    preview_rows: List[dict] = []


class DatasetPreviewResponse(BaseModel):
    dataset_profile_id: str
    columns: List[str] = []
    rows: List[dict] = []
    total_rows: int = 0
    preview_rows: int = 0
