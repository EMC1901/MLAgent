from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ---- Request schemas ----

class FeaturePreprocessingCreateRequest(BaseModel):
    force_rerun: bool = False
    max_missing_ratio: float = 0.5
    drop_invalid_features: bool = True
    drop_all_missing_features: bool = True
    drop_constant_features: bool = True
    drop_high_missing_features: bool = True
    imputation_strategy: str = "median"
    scaling_strategy: str = "standard_scaler"
    feature_selection_strategy: str = "variance_threshold"
    output_format: str = "parquet"


# ---- Internal DTOs ----

class DroppedFeature(BaseModel):
    name: str
    reason: str
    action: str = "dropped"


class ColumnValidation(BaseModel):
    dropped_invalid_features: List[DroppedFeature] = []
    dropped_all_missing_features: List[DroppedFeature] = []
    dropped_constant_features: List[DroppedFeature] = []
    dropped_high_missing_features: List[DroppedFeature] = []
    retained_features: List[str] = []


class FeatureGroupValidationItem(BaseModel):
    group_name: str
    n_raw_features: int = 0
    n_valid_features: int = 0
    status: str = "retained"
    reason: str = ""


class FeatureGroupValidation(BaseModel):
    groups: List[FeatureGroupValidationItem] = []


class PreprocessingStepResult(BaseModel):
    executed: bool = False
    strategy: str = "none"
    columns: List[str] = []
    artifact_component: str = ""


class FeatureSelectionStepResult(BaseModel):
    executed: bool = False
    strategy: str = "none"
    columns_dropped: List[str] = []


class PreprocessingExecution(BaseModel):
    imputation: PreprocessingStepResult = PreprocessingStepResult()
    scaling: PreprocessingStepResult = PreprocessingStepResult()
    categorical_encoding: PreprocessingStepResult = PreprocessingStepResult()
    feature_selection: FeatureSelectionStepResult = FeatureSelectionStepResult()


class InputArtifact(BaseModel):
    feature_matrix_artifact_id: Optional[str] = None
    file_path: Optional[str] = None
    n_samples: int = 0
    n_raw_features: int = 0


class ValidationSummary(BaseModel):
    is_model_ready: bool = False
    n_samples: int = 0
    n_raw_features: int = 0
    n_valid_features_before_preprocessing: int = 0
    n_features_after_preprocessing: int = 0
    n_dropped_features: int = 0
    target_column: Optional[str] = None
    task_type: Optional[str] = None


class ModelReadyArtifact(BaseModel):
    artifact_id: Optional[str] = None
    storage_type: str = "parquet"
    file_path: Optional[str] = None
    n_samples: int = 0
    n_features: int = 0
    target_column: Optional[str] = None


class PreprocessingPipelineArtifact(BaseModel):
    artifact_id: Optional[str] = None
    storage_type: str = "joblib"
    file_path: Optional[str] = None


class ModelSearchInput(BaseModel):
    model_ready_artifact_id: Optional[str] = None
    model_ready_matrix_path: Optional[str] = None
    preprocessing_pipeline_artifact_id: Optional[str] = None
    target_column: Optional[str] = None
    feature_columns: List[str] = []
    task_type: Optional[str] = None
    primary_metric: Optional[str] = None
    model_strategy: dict = {}
    validation_strategy: dict = {}
    evaluation_strategy: dict = {}
    hpo_strategy: dict = {}
    ready_for_model_search: bool = False


# ---- Response schema ----

class FeaturePreprocessingResponse(BaseModel):
    preprocessing_id: str
    task_id: str
    interpretation_id: Optional[str] = None
    dataset_profile_id: Optional[str] = None
    workflow_plan_id: Optional[str] = None
    feature_engineering_id: Optional[str] = None
    status: str
    input_artifact: Optional[InputArtifact] = None
    validation_summary: Optional[ValidationSummary] = None
    column_validation: Optional[ColumnValidation] = None
    feature_group_validation: Optional[FeatureGroupValidation] = None
    preprocessing_execution: Optional[PreprocessingExecution] = None
    model_ready_artifact: Optional[ModelReadyArtifact] = None
    preprocessing_pipeline_artifact: Optional[PreprocessingPipelineArtifact] = None
    model_search_input: Optional[ModelSearchInput] = None
    warnings: List[str] = []
    errors: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PreviewResponse(BaseModel):
    columns: List[str] = []
    preview_rows: int = 0
    total_rows: int = 0
    rows: List[dict] = []
