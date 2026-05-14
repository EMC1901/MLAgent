from pydantic import BaseModel
from typing import Optional, List, Dict, Any
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


# ---- New: Feature Quality Profile ----

class GlobalQualitySummary(BaseModel):
    row_count: int = 0
    feature_count: int = 0
    numeric_feature_count: int = 0
    categorical_feature_count: int = 0
    missing_value_ratio: float = 0.0
    constant_feature_count: int = 0
    near_constant_feature_count: int = 0
    low_information_feature_count: int = 0
    high_missing_feature_count: int = 0
    high_correlation_pair_count: int = 0
    high_skewness_feature_count: int = 0


class PerFeatureSummary(BaseModel):
    feature_name: str = ""
    dtype: str = "float64"
    missing_ratio: float = 0.0
    variance: Optional[float] = None
    skewness: Optional[float] = None
    unique_ratio: float = 0.0
    is_constant: bool = False
    is_near_constant: bool = False
    is_low_variance: bool = False
    source_feature_group: str = ""


class PerGroupSummary(BaseModel):
    group_name: str = ""
    feature_count: int = 0
    missing_ratio: float = 0.0
    constant_feature_count: int = 0
    near_constant_feature_count: int = 0
    avg_variance: Optional[float] = None
    avg_skewness: Optional[float] = None


class QualityWarning(BaseModel):
    warning_type: str = ""
    severity: str = "low"  # low | medium | high
    affected_features: List[str] = []
    message: str = ""


class FeatureQualityProfile(BaseModel):
    global_summary: GlobalQualitySummary = GlobalQualitySummary()
    per_feature_summary: List[PerFeatureSummary] = []
    per_group_summary: List[PerGroupSummary] = []
    quality_warnings: List[QualityWarning] = []


# ---- New: Execution Report ----

class ActionResult(BaseModel):
    action_id: str = ""
    capability_id: str = ""
    status: str = "pending"  # success | failed | fallback_used | skipped
    generated_feature_count: int = 0
    warnings: List[str] = []
    error_message: Optional[str] = None
    fallback_action_id: Optional[str] = None


class ExecutionReport(BaseModel):
    action_results: List[ActionResult] = []


# ---- New: Feature Provenance ----

class FeatureProvenance(BaseModel):
    registry_snapshot_version: str = ""
    input_artifact_hash: str = ""
    featurizer_versions: Dict[str, str] = {}
    dependency_versions: Dict[str, str] = {}
    created_at: Optional[datetime] = None


# ---- New: Feature Groups (structured) ----

class FeatureGroup(BaseModel):
    group_id: str = ""
    source_action_id: str = ""
    capability_id: str = ""
    feature_family: str = ""  # composition | structure | descriptor | metadata
    feature_names: List[str] = []
    feature_count: int = 0
    semantic_description: str = ""


# ---- New: FeaturePreprocessingDecisionInput ----

class FeaturePreprocessingDecisionInput(BaseModel):
    task_context: Dict[str, Any] = {}
    dataset_context: Dict[str, Any] = {}
    workflow_context: Dict[str, Any] = {}
    feature_matrix_context: Dict[str, Any] = {}
    execution_context: Dict[str, Any] = {}
    known_preprocessing_risks: List[str] = []


# ---- Existing DTOs (backward compat) ----

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
    # New fields
    executed_feature_strategy_id: Optional[str] = None
    feature_groups: List[FeatureGroup] = []
    feature_quality_profile: Optional[FeatureQualityProfile] = None
    execution_report: Optional[ExecutionReport] = None
    feature_provenance: Optional[FeatureProvenance] = None
    feature_preprocessing_decision_input: Optional[FeaturePreprocessingDecisionInput] = None
    # Legacy
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


# ---- Sub-resource responses ----

class ExecutionReportResponse(BaseModel):
    feature_engineering_id: str
    execution_report: ExecutionReport


class FeatureGroupsResponse(BaseModel):
    feature_engineering_id: str
    feature_groups: List[FeatureGroup]


class QualityProfileResponse(BaseModel):
    feature_engineering_id: str
    feature_quality_profile: FeatureQualityProfile


class PreprocessingDecisionInputResponse(BaseModel):
    feature_engineering_id: str
    feature_preprocessing_decision_input: FeaturePreprocessingDecisionInput


class ProvenanceResponse(BaseModel):
    feature_engineering_id: str
    feature_provenance: FeatureProvenance
