// ---- Request types ----

export interface FeaturePreprocessingCreateRequest {
  force_rerun?: boolean;
  max_missing_ratio?: number;
  drop_invalid_features?: boolean;
  drop_all_missing_features?: boolean;
  drop_constant_features?: boolean;
  drop_high_missing_features?: boolean;
  imputation_strategy?: string;
  scaling_strategy?: string;
  feature_selection_strategy?: string;
  output_format?: string;
  planning_mode?: string;
}

export interface PlanRequest {
  force_regenerate?: boolean;
  llm_provider?: string | null;
  model_name?: string | null;
}

export interface ExecuteRequest {
  plan_id?: string | null;
  plan?: Record<string, unknown> | null;
}

// ---- Decision Rationale ----

export interface PPRationale {
  reason: string;
  evidence: string[];
  expected_benefit: string;
  risk: string;
  fallback: string;
}

// ---- PreprocessingPlan DTOs ----

export interface LeakagePrevention {
  fit_transform_scope: string;
  target_column_excluded: boolean;
  id_columns_excluded: boolean;
  target_aware_selection_allowed: boolean;
  rationale: string;
}

export interface VariantStrategy {
  mode: string;
  rationale: string;
}

export interface GlobalPolicy {
  leakage_prevention: LeakagePrevention;
  variant_strategy: VariantStrategy;
}

export interface ColumnPolicy {
  column_name: string;
  action: string;
  reason: string;
  evidence: string[];
  risk: string;
}

export interface Operation {
  operation_id: string;
  capability_id: string;
  parameters: Record<string, unknown>;
  execution_scope: string;
  decision_rationale: PPRationale;
}

export interface FeatureGroupPolicy {
  feature_group: string;
  policy: string;
  operations: Operation[];
}

export interface OperationSequenceItem {
  step_order: number;
  operation_id: string;
  capability_id: string;
  target_feature_groups: string[];
  target_columns: string[];
  parameters: Record<string, unknown>;
  execution_scope: string;
  decision_rationale: PPRationale;
}

export interface ModelFamilyNote {
  model_family: string;
  preprocessing_needs: string[];
  rationale: string;
}

export interface RejectedOperation {
  capability_id: string;
  reason: string;
  evidence: string[];
}

export interface PreprocessingPlan {
  plan_id?: string | null;
  plan_version: string;
  global_policy: GlobalPolicy;
  capability_groups_used: string[];
  column_policies: ColumnPolicy[];
  feature_group_policies: FeatureGroupPolicy[];
  operation_sequence: OperationSequenceItem[];
  model_family_specific_notes: ModelFamilyNote[];
  rejected_operations: RejectedOperation[];
  warnings_for_downstream: string[];
}

// ---- Execution Report DTOs ----

export interface OperationResult {
  operation_id: string;
  capability_id: string;
  capability_group: string;
  status: string;
  affected_features: string[];
  removed_features: string[];
  warnings: string[];
  error_message?: string | null;
}

export interface PreprocessingExecutionReport {
  operation_results: OperationResult[];
}

// ---- Removed Feature ----

export interface RemovedFeature {
  feature_name: string;
  reason: string;
  evidence: string;
  source_feature_group: string;
}

// ---- Artifact DTOs ----

export interface ModelReadyArtifactNew {
  artifact_id: string;
  variant_name: string;
  path: string;
  usage: string;
  row_count: number;
  feature_count: number;
  artifact_hash: string;
}

export interface PreprocessorArtifact {
  artifact_id: string;
  variant_name: string;
  path: string;
  usage: string;
  artifact_hash: string;
}

// ---- Feature Lineage DTOs ----

export interface FeatureLineageEntry {
  original_name: string;
  transformed_name: string;
  source_feature_group: string;
  source_feature_action: string;
  transformations_applied: string[];
  imputed: boolean;
  scaled: boolean;
  transformed: boolean;
  selected: boolean;
  reduced: boolean;
  is_interpretable: boolean;
  removed: boolean;
  removal_reason?: string | null;
}

export interface FeatureGroupLineageEntry {
  group_name: string;
  group_status: string;
  original_feature_count: number;
  retained_feature_count: number;
  removed_feature_count: number;
  operations_applied: string[];
}

export interface ExplainabilityPreservationReport {
  total_original_features: number;
  total_retained_features: number;
  total_interpretable_features: number;
  total_reduced_features: number;
  interpretability_score: number;
  notes: string[];
}

// ---- Provenance ----

export interface PreprocessingProvenance {
  registry_snapshot_version: string;
  input_feature_artifact_hash: string;
  output_artifact_hash: string;
  operation_parameter_snapshot: Record<string, unknown>;
  fitted_statistics_summary: Record<string, unknown>;
  dependency_versions: Record<string, string>;
  random_seed?: number | null;
  created_at?: string | null;
}

// ---- Model Search Context Input ----

export interface ModelSearchContextInput {
  model_ready_matrix_path?: string | null;
  preprocessor_path?: string | null;
  feature_summary: Record<string, unknown>;
  default_variant_id?: string | null;
  available_variants: Record<string, unknown>[];
  recommended_variant_by_model_family: Record<string, string>;
}

// ---- Legacy DTOs (backward compat) ----

export interface DroppedFeature {
  name: string;
  reason: string;
  action: string;
}

export interface ColumnValidation {
  dropped_invalid_features: DroppedFeature[];
  dropped_all_missing_features: DroppedFeature[];
  dropped_constant_features: DroppedFeature[];
  dropped_high_missing_features: DroppedFeature[];
  retained_features: string[];
}

export interface FeatureGroupValidationItem {
  group_name: string;
  n_raw_features: number;
  n_valid_features: number;
  status: string;
  reason: string;
}

export interface FeatureGroupValidation {
  groups: FeatureGroupValidationItem[];
}

export interface PreprocessingStepResult {
  executed: boolean;
  strategy: string;
  columns: string[];
  artifact_component: string;
}

export interface FeatureSelectionStepResult {
  executed: boolean;
  strategy: string;
  columns_dropped: string[];
}

export interface PreprocessingExecution {
  imputation: PreprocessingStepResult;
  scaling: PreprocessingStepResult;
  categorical_encoding: PreprocessingStepResult;
  feature_selection: FeatureSelectionStepResult;
}

export interface InputArtifact {
  feature_matrix_artifact_id?: string | null;
  file_path?: string | null;
  n_samples: number;
  n_raw_features: number;
}

export interface ValidationSummary {
  is_model_ready: boolean;
  n_samples: number;
  n_raw_features: number;
  n_valid_features_before_preprocessing: number;
  n_features_after_preprocessing: number;
  n_dropped_features: number;
  target_column?: string | null;
  task_type?: string | null;
}

export interface ModelReadyArtifact {
  artifact_id?: string | null;
  storage_type: string;
  file_path?: string | null;
  n_samples: number;
  n_features: number;
  target_column?: string | null;
}

export interface PreprocessingPipelineArtifact {
  artifact_id?: string | null;
  storage_type: string;
  file_path?: string | null;
}

export interface ModelSearchInput {
  model_ready_artifact_id?: string | null;
  model_ready_matrix_path?: string | null;
  preprocessing_pipeline_artifact_id?: string | null;
  target_column?: string | null;
  feature_columns: string[];
  task_type?: string | null;
  primary_metric?: string | null;
  model_strategy: Record<string, unknown>;
  validation_strategy: Record<string, unknown>;
  evaluation_strategy: Record<string, unknown>;
  hpo_strategy: Record<string, unknown>;
  ready_for_model_search: boolean;
}

// ---- Main Response ----

export interface FeaturePreprocessingResponse {
  preprocessing_id: string;
  task_id: string;
  interpretation_id?: string | null;
  dataset_profile_id?: string | null;
  workflow_plan_id?: string | null;
  feature_engineering_id?: string | null;
  status: string;

  // New fields
  preprocessing_plan?: PreprocessingPlan | null;
  preprocessing_registry_snapshot_version?: string | null;
  execution_report?: PreprocessingExecutionReport | null;
  removed_features?: RemovedFeature[];
  retained_feature_groups?: Record<string, unknown>[];
  feature_lineage_map?: Record<string, unknown>;
  feature_group_lineage_map?: Record<string, unknown>;
  explainability_preservation_report?: ExplainabilityPreservationReport | null;
  model_ready_artifacts?: ModelReadyArtifactNew[];
  preprocessor_artifacts?: PreprocessorArtifact[];
  preprocessing_provenance?: PreprocessingProvenance | null;
  model_search_context_input?: ModelSearchContextInput | null;

  // Legacy fields (backward compat)
  input_artifact?: InputArtifact | null;
  validation_summary?: ValidationSummary | null;
  column_validation?: ColumnValidation | null;
  feature_group_validation?: FeatureGroupValidation | null;
  preprocessing_execution?: PreprocessingExecution | null;
  model_ready_artifact?: ModelReadyArtifact | null;
  preprocessing_pipeline_artifact?: PreprocessingPipelineArtifact | null;
  model_search_input?: ModelSearchInput | null;
  warnings: string[];
  errors: string[];
  created_at?: string | null;
  updated_at?: string | null;
}

// ---- Sub-resource responses ----

export interface PlanResponse {
  preprocessing_id: string;
  task_id: string;
  preprocessing_plan: PreprocessingPlan;
}

export interface RationaleResponse {
  preprocessing_id: string;
  rationales: PPRationale[];
  rejected_operations: RejectedOperation[];
}

export interface ExecutionReportResponse {
  preprocessing_id: string;
  execution_report: PreprocessingExecutionReport;
}

export interface RemovedFeaturesResponse {
  preprocessing_id: string;
  removed_features: RemovedFeature[];
  total_removed: number;
}

export interface FeatureLineageResponse {
  preprocessing_id: string;
  feature_lineage_map: Record<string, unknown>;
  feature_group_lineage_map: Record<string, unknown>;
}

export interface ArtifactManifestResponse {
  preprocessing_id: string;
  model_ready_artifacts: ModelReadyArtifactNew[];
  preprocessor_artifacts: PreprocessorArtifact[];
}

export interface ProvenanceResponse {
  preprocessing_id: string;
  preprocessing_provenance: PreprocessingProvenance;
}

export interface CapabilitiesResponse {
  capability_groups: Record<string, string>;
  available_capabilities: Record<string, unknown>[];
  snapshot: Record<string, unknown>;
}

export interface PreviewResponse {
  columns: string[];
  preview_rows: number;
  total_rows: number;
  rows: Record<string, unknown>[];
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}
