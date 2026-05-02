from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ---- Request schemas ----

class FeatureEngineeringCreateRequest(BaseModel):
    force_rerun: bool = False
    override_feature_strategy: Optional[dict] = None
    output_format: str = "parquet"


# ---- Internal DTOs ----

class ExecutedFeaturizer(BaseModel):
    name: str
    display_name: str = ""
    status: str
    n_features_generated: int = 0
    failed_sample_count: int = 0
    execution_time_ms: int = 0
    dependency_versions: dict = {}


class FeatureGeneration(BaseModel):
    selected_featurizers: List[str] = []
    semantic_featurizers: List[str] = []
    unsupported_future_featurizers: List[str] = []
    fallback_featurizers: List[str] = []
    skipped_featurizers: List[str] = []
    executed_featurizers: List[ExecutedFeaturizer] = []


class FeatureMatrixInfo(BaseModel):
    artifact_id: Optional[str] = None
    storage_type: str = "local_file"
    file_path: Optional[str] = None
    n_samples: int = 0
    n_features: int = 0
    target_column: Optional[str] = None
    index_column: str = "sample_id"


class FeatureSchemaInfo(BaseModel):
    feature_columns: List[str] = []
    feature_groups: List[dict] = []
    numeric_feature_count: int = 0
    categorical_feature_count: int = 0
    constant_feature_count: int = 0
    all_missing_feature_count: int = 0


class MissingValues(BaseModel):
    total_missing: int = 0
    columns_with_missing: List[str] = []


class FeatureQuality(BaseModel):
    missing_values: MissingValues = MissingValues()
    invalid_features: List[str] = []
    dropped_features: List[str] = []
    failed_samples: List[str] = []
    constant_features: List[str] = []
    all_missing_features: List[str] = []
    is_valid_feature_matrix: bool = True
    warnings: List[str] = []
    errors: List[str] = []


class PreprocessingRequirements(BaseModel):
    scaling_required: bool = False
    imputation_required: bool = False
    feature_selection_required: bool = False


class DownstreamInput(BaseModel):
    feature_matrix_artifact_id: Optional[str] = None
    feature_matrix_path: Optional[str] = None
    target_column: Optional[str] = None
    feature_columns: List[str] = []
    feature_groups: List[dict] = []
    task_type: Optional[str] = None
    primary_metric: Optional[str] = None
    scaling_required: bool = False
    imputation_required: bool = False
    feature_selection_required: bool = False
    ready_for_pipeline_generation: bool = False


class LoadingSummary(BaseModel):
    is_loaded: bool = False
    n_rows: int = 0
    n_columns: int = 0
    columns: List[str] = []


class FeaturePreviewRow(BaseModel):
    sample_id: Optional[str] = None
    values: dict = {}


# ---- Response schema ----

class FeatureEngineeringResponse(BaseModel):
    feature_engineering_id: str
    task_id: str
    interpretation_id: Optional[str] = None
    dataset_profile_id: Optional[str] = None
    workflow_plan_id: Optional[str] = None
    status: str
    input_modality: Optional[str] = None
    feature_type: Optional[str] = None
    feature_generation: Optional[FeatureGeneration] = None
    feature_matrix: Optional[FeatureMatrixInfo] = None
    feature_schema: Optional[FeatureSchemaInfo] = None
    feature_quality: Optional[FeatureQuality] = None
    preprocessing_requirements: Optional[PreprocessingRequirements] = None
    downstream_input: Optional[DownstreamInput] = None
    warnings: List[str] = []
    errors: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FeaturePreviewResponse(BaseModel):
    columns: List[str] = []
    preview_rows: int = 0
    total_rows: int = 0
    rows: List[dict] = []


class ResolvedFeatureStrategy(BaseModel):
    feature_type: Optional[str] = None
    input_modality: Optional[str] = None
    selected_featurizers: List[str] = []
    semantic_featurizers: List[str] = []
    fallback_featurizers: List[str] = []
    unsupported_featurizers: List[str] = []
    resolution_log: List[dict] = []
    scaling_required: bool = False
    feature_selection_required: bool = False
    structure_features_required: bool = False
