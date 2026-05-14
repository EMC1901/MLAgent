from pydantic import BaseModel
from typing import Optional, List, Dict, Any
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
    # New: Plan execution mode
    planning_mode: str = "llm_guided"  # llm_guided | system_default


class PlanRequest(BaseModel):
    """Request to generate only the PreprocessingPlan (no execution)."""
    force_regenerate: bool = False
    llm_provider: Optional[str] = None
    model_name: Optional[str] = None


class ExecuteRequest(BaseModel):
    """Request to execute a validated PreprocessingPlan."""
    plan_id: Optional[str] = None
    plan: Optional[dict] = None


# ---- Decision Rationale (shared) ----

class PPRationale(BaseModel):
    reason: str = ""
    evidence: List[str] = []
    expected_benefit: str = ""
    risk: str = ""
    fallback: str = ""


# ---- PreprocessingPlan DTOs ----

class LeakagePrevention(BaseModel):
    fit_transform_scope: str = "train_fold_only"
    target_column_excluded: bool = True
    id_columns_excluded: bool = True
    target_aware_selection_allowed: bool = False
    rationale: str = ""


class VariantStrategy(BaseModel):
    mode: str = "single"  # single | model_family_specific | multiple_variants
    rationale: str = ""


class GlobalPolicy(BaseModel):
    leakage_prevention: LeakagePrevention = LeakagePrevention()
    variant_strategy: VariantStrategy = VariantStrategy()


class ColumnPolicy(BaseModel):
    column_name: str = ""
    action: str = "keep"  # keep | drop | transform | flag_for_review
    reason: str = ""
    evidence: List[str] = []
    risk: str = ""


class Operation(BaseModel):
    operation_id: str = ""
    capability_id: str = ""
    parameters: Dict[str, Any] = {}
    execution_scope: str = "train_only"  # dataset_profile_only | train_only | fold_only
    decision_rationale: PPRationale = PPRationale()


class FeatureGroupPolicy(BaseModel):
    feature_group: str = ""
    policy: str = "preserve"  # preserve | filter | transform | reduce_dimension | drop
    operations: List[Operation] = []


class OperationSequenceItem(BaseModel):
    step_order: int = 0
    operation_id: str = ""
    capability_id: str = ""
    target_feature_groups: List[str] = []
    target_columns: List[str] = []
    parameters: Dict[str, Any] = {}
    execution_scope: str = "train_only"
    decision_rationale: PPRationale = PPRationale()


class ModelFamilyNote(BaseModel):
    model_family: str = "linear_model"
    preprocessing_needs: List[str] = []
    rationale: str = ""


class RejectedOperation(BaseModel):
    capability_id: str = ""
    reason: str = ""
    evidence: List[str] = []


class PreprocessingPlan(BaseModel):
    plan_id: Optional[str] = None
    plan_version: str = "1.0.0"
    global_policy: GlobalPolicy = GlobalPolicy()
    capability_groups_used: List[str] = []
    column_policies: List[ColumnPolicy] = []
    feature_group_policies: List[FeatureGroupPolicy] = []
    operation_sequence: List[OperationSequenceItem] = []
    model_family_specific_notes: List[ModelFamilyNote] = []
    rejected_operations: List[RejectedOperation] = []
    warnings_for_downstream: List[str] = []


# ---- Execution Report DTOs ----

class OperationResult(BaseModel):
    operation_id: str = ""
    capability_id: str = ""
    capability_group: str = ""
    status: str = "pending"  # success | failed | skipped | fallback_used
    affected_features: List[str] = []
    removed_features: List[str] = []
    warnings: List[str] = []
    error_message: Optional[str] = None


class PreprocessingExecutionReport(BaseModel):
    operation_results: List[OperationResult] = []


# ---- Removed Feature DTO ----

class RemovedFeature(BaseModel):
    feature_name: str = ""
    reason: str = ""
    evidence: str = ""
    source_feature_group: str = ""


# ---- Model-Ready Artifact DTO ----

class ModelReadyArtifact(BaseModel):
    artifact_id: str = ""
    variant_name: str = "default"
    path: str = ""
    usage: str = "fold_safe_template"  # preview | fold_safe_template | final_training
    row_count: int = 0
    feature_count: int = 0
    artifact_hash: str = ""


class PreprocessorArtifact(BaseModel):
    artifact_id: str = ""
    variant_name: str = "default"
    path: str = ""
    usage: str = "pipeline_template"  # pipeline_template | fitted_preview | final_training
    artifact_hash: str = ""


# ---- Feature Lineage DTOs ----

class FeatureLineageEntry(BaseModel):
    original_name: str = ""
    transformed_name: str = ""
    source_feature_group: str = ""
    source_feature_action: str = ""
    transformations_applied: List[str] = []
    imputed: bool = False
    scaled: bool = False
    transformed: bool = False
    selected: bool = True
    reduced: bool = False
    is_interpretable: bool = True
    removed: bool = False
    removal_reason: Optional[str] = None


class FeatureGroupLineageEntry(BaseModel):
    group_name: str = ""
    group_status: str = "retained"  # retained | partially_retained | removed
    original_feature_count: int = 0
    retained_feature_count: int = 0
    removed_feature_count: int = 0
    operations_applied: List[str] = []


class ExplainabilityPreservationReport(BaseModel):
    total_original_features: int = 0
    total_retained_features: int = 0
    total_interpretable_features: int = 0
    total_reduced_features: int = 0
    interpretability_score: float = 1.0
    notes: List[str] = []


# ---- Provenance DTO ----

class PreprocessingProvenance(BaseModel):
    registry_snapshot_version: str = ""
    input_feature_artifact_hash: str = ""
    output_artifact_hash: str = ""
    operation_parameter_snapshot: Dict[str, Any] = {}
    fitted_statistics_summary: Dict[str, Any] = {}
    dependency_versions: Dict[str, str] = {}
    random_seed: Optional[int] = None
    created_at: Optional[datetime] = None


# ---- Model Search Context Input ----

class ModelSearchContextInput(BaseModel):
    model_ready_matrix_path: Optional[str] = None
    preprocessor_path: Optional[str] = None
    feature_summary: Dict[str, Any] = {}
    default_variant_id: Optional[str] = None
    available_variants: List[Dict[str, Any]] = []
    recommended_variant_by_model_family: Dict[str, str] = {}


# ---- Legacy DTOs (backward compat) ----

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


# Legacy (keep for compat)
class ModelReadyArtifactLegacy(BaseModel):
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

    # New fields
    preprocessing_plan: Optional[PreprocessingPlan] = None
    preprocessing_registry_snapshot_version: Optional[str] = None
    execution_report: Optional[PreprocessingExecutionReport] = None
    removed_features: List[RemovedFeature] = []
    retained_feature_groups: List[Dict[str, Any]] = []
    feature_lineage_map: Dict[str, Any] = {}
    feature_group_lineage_map: Dict[str, Any] = {}
    explainability_preservation_report: Optional[ExplainabilityPreservationReport] = None
    model_ready_artifacts: List[ModelReadyArtifact] = []
    preprocessor_artifacts: List[PreprocessorArtifact] = []
    preprocessing_provenance: Optional[PreprocessingProvenance] = None
    model_search_context_input: Optional[ModelSearchContextInput] = None

    # Legacy fields (backward compat)
    input_artifact: Optional[InputArtifact] = None
    validation_summary: Optional[ValidationSummary] = None
    column_validation: Optional[ColumnValidation] = None
    feature_group_validation: Optional[FeatureGroupValidation] = None
    preprocessing_execution: Optional[PreprocessingExecution] = None
    model_ready_artifact: Optional[ModelReadyArtifactLegacy] = None
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


# ---- Sub-resource responses ----

class PlanResponse(BaseModel):
    preprocessing_id: str
    task_id: str
    preprocessing_plan: PreprocessingPlan


class RationaleResponse(BaseModel):
    preprocessing_id: str
    rationales: List[PPRationale] = []
    rejected_operations: List[RejectedOperation] = []


class ExecutionReportResponse(BaseModel):
    preprocessing_id: str
    execution_report: PreprocessingExecutionReport


class RemovedFeaturesResponse(BaseModel):
    preprocessing_id: str
    removed_features: List[RemovedFeature]
    total_removed: int = 0


class FeatureLineageResponse(BaseModel):
    preprocessing_id: str
    feature_lineage_map: Dict[str, Any]
    feature_group_lineage_map: Dict[str, Any]


class ArtifactManifestResponse(BaseModel):
    preprocessing_id: str
    model_ready_artifacts: List[ModelReadyArtifact]
    preprocessor_artifacts: List[PreprocessorArtifact]


class ProvenanceResponse(BaseModel):
    preprocessing_id: str
    preprocessing_provenance: PreprocessingProvenance
