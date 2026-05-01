export interface ColumnInfo {
  name: string;
  role: string;
  dtype: string;
  missing_count: number;
  missing_ratio: number;
}

export interface DatasetSource {
  source_type: string;
  dataset_reference?: string;
  loader?: string;
  loaded_from?: string;
  file_name?: string;
}

export interface DatasetSchema {
  n_samples: number;
  n_columns: number;
  columns: ColumnInfo[];
  input_columns: string[];
  target_column?: string;
}

export interface ModalityCheck {
  expected_input_modality?: string;
  detected_input_modality?: string;
  is_consistent: boolean;
  messages: string[];
}

export interface ClassDistribution {
  label: string;
  count: number;
  ratio: number;
}

export interface TargetProfile {
  target_column?: string;
  task_type?: string;
  dtype?: string;
  missing_count: number;
  missing_ratio: number;
  min?: number;
  max?: number;
  mean?: number;
  median?: number;
  std?: number;
  skewness?: number;
  outlier_count: number;
  class_count?: number;
  class_distribution?: ClassDistribution[];
  majority_class_ratio?: number;
  minority_class_count?: number;
  is_imbalanced?: boolean;
}

export interface MissingValues {
  total_missing: number;
  columns_with_missing: string[];
}

export interface Duplicates {
  duplicate_rows: number;
  duplicate_input_samples: number;
}

export interface InvalidRows {
  count: number;
  examples: Record<string, unknown>[];
}

export interface DataQuality {
  missing_values: MissingValues;
  duplicates: Duplicates;
  invalid_rows: InvalidRows;
  warnings: string[];
  errors: string[];
}

export interface ProfilingSummary {
  is_loadable: boolean;
  is_usable_for_ml: boolean;
  sample_size_level: string;
  quality_level: string;
  main_issues: string[];
  recommended_next_step?: string;
}

export interface WorkflowPlanningInput {
  input_modality?: string;
  task_type?: string;
  target_column?: string;
  input_columns: string[];
  n_samples: number;
  n_columns: number;
  n_features_raw: number;
  sample_size_level: string;
  has_missing_values: boolean;
  has_duplicates: boolean;
  requires_cleaning: boolean;
  requires_target_transformation_check: boolean;
  quality_level: string;
  is_usable_for_ml: boolean;
}

export interface DatasetProfileResponse {
  dataset_profile_id: string;
  task_id: string;
  interpretation_id?: string;
  status: string;
  dataset_source?: DatasetSource;
  dataset_schema?: DatasetSchema;
  modality_check?: ModalityCheck;
  target_profile?: TargetProfile;
  data_quality?: DataQuality;
  profiling_summary?: ProfilingSummary;
  workflow_planning_input?: WorkflowPlanningInput;
  error_message?: string;
  created_at?: string;
  updated_at?: string;
}

export interface DatasetFileUploadResponse {
  file_id: string;
  file_name: string;
  file_size_bytes: number;
  n_rows: number;
  n_columns: number;
  columns: string[];
  preview_rows: Record<string, unknown>[];
}

export interface DatasetPreviewResponse {
  dataset_profile_id: string;
  columns: string[];
  rows: Record<string, unknown>[];
  total_rows: number;
  preview_rows: number;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}
