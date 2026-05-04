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
}

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

export interface FeaturePreprocessingResponse {
  preprocessing_id: string;
  task_id: string;
  interpretation_id?: string | null;
  dataset_profile_id?: string | null;
  workflow_plan_id?: string | null;
  feature_engineering_id?: string | null;
  status: string;
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
