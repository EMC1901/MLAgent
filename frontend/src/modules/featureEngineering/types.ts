export interface FeatureEngineeringCreateRequest {
  force_rerun?: boolean;
  override_feature_strategy?: Record<string, unknown> | null;
  output_format?: string;
}

export interface ExecutedFeaturizer {
  name: string;
  display_name?: string;
  status: string;
  n_features_generated: number;
  failed_sample_count: number;
  execution_time_ms?: number;
  dependency_versions?: Record<string, string>;
}

export interface FeatureGroup {
  group_name: string;
  display_name?: string;
  n_features: number;
  feature_columns?: string[];
  status?: string;
}

export interface FeatureGeneration {
  selected_featurizers: string[];
  semantic_featurizers: string[];
  unsupported_future_featurizers: string[];
  fallback_featurizers: string[];
  skipped_featurizers: string[];
  executed_featurizers: ExecutedFeaturizer[];
}

export interface FeatureMatrixInfo {
  artifact_id?: string | null;
  storage_type: string;
  file_path?: string | null;
  n_samples: number;
  n_features: number;
  target_column?: string | null;
  index_column: string;
}

export interface FeatureSchemaInfo {
  feature_columns: string[];
  feature_groups: FeatureGroup[];
  numeric_feature_count: number;
  categorical_feature_count: number;
  constant_feature_count: number;
  all_missing_feature_count: number;
}

export interface MissingValues {
  total_missing: number;
  columns_with_missing: string[];
}

export interface FeatureQuality {
  missing_values: MissingValues;
  invalid_features: string[];
  dropped_features: string[];
  failed_samples: string[];
  constant_features: string[];
  all_missing_features: string[];
  is_valid_feature_matrix: boolean;
  warnings: string[];
  errors: string[];
}

export interface PreprocessingRequirements {
  scaling_required: boolean;
  imputation_required: boolean;
  feature_selection_required: boolean;
}

export interface DownstreamInput {
  feature_matrix_artifact_id?: string | null;
  feature_matrix_path?: string | null;
  target_column?: string | null;
  feature_columns: string[];
  feature_groups: FeatureGroup[];
  task_type?: string | null;
  primary_metric?: string | null;
  scaling_required: boolean;
  imputation_required: boolean;
  feature_selection_required: boolean;
  ready_for_pipeline_generation: boolean;
}

export interface FeaturizerSpec {
  id: string;
  display_name: string;
  description?: string;
  input_modalities: string[];
  feature_type: string;
  status: string;
  mvp_supported: boolean;
  requires_dependencies: string[];
  dependency_status: Record<string, { status: string; version?: string | null }>;
  estimated_feature_count: string;
  fallback_priority: number;
}

export interface DependencyStatus {
  status: string;
  version?: string | null;
}

export interface RegistryListResponse {
  featurizers: FeaturizerSpec[];
  total_available: number;
  total_planned: number;
}

export interface RegistryDetailResponse {
  spec: FeaturizerSpec;
  dependency_status: Record<string, DependencyStatus>;
  effective_status: string;
}

export interface DependenciesStatusResponse {
  dependencies: Record<string, DependencyStatus>;
}

export interface FeatureEngineeringResponse {
  feature_engineering_id: string;
  task_id: string;
  interpretation_id?: string | null;
  dataset_profile_id?: string | null;
  workflow_plan_id?: string | null;
  status: string;
  input_modality?: string | null;
  feature_type?: string | null;
  feature_generation?: FeatureGeneration | null;
  feature_matrix?: FeatureMatrixInfo | null;
  feature_schema?: FeatureSchemaInfo | null;
  feature_quality?: FeatureQuality | null;
  preprocessing_requirements?: PreprocessingRequirements | null;
  downstream_input?: DownstreamInput | null;
  warnings: string[];
  errors: string[];
  created_at?: string | null;
  updated_at?: string | null;
}

export interface FeaturePreviewResponse {
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
