export interface PipelineExecutionCreateRequest {
  force_rerun?: boolean;
  pipeline_generation_id?: string | null;
  execution_mode?: string;
  max_trials_override?: number | null;
  max_runtime_seconds?: number | null;
  fail_fast?: boolean;
  save_trained_models?: boolean;
  save_predictions?: boolean;
  notes?: string | null;
}

export interface FoldResultDTO {
  fold_index: number;
  train_size: number;
  validation_size: number;
  status: string;
  prediction_artifact_path?: string | null;
  model_artifact_path?: string | null;
  raw_metric_values: Record<string, number>;
  duration_seconds: number;
  error_message?: string | null;
}

export interface TrialResultDTO {
  trial_id: string;
  pipeline_spec_id: string;
  pipeline_run_id: string;
  model_id: string;
  trial_index: number;
  trial_type: string;
  params: Record<string, unknown>;
  status: string;
  fold_results: FoldResultDTO[];
  prediction_artifact_paths: string[];
  model_artifact_paths: string[];
  raw_metric_values: Record<string, number>;
  started_at?: string | null;
  finished_at?: string | null;
  duration_seconds: number;
  error_message?: string | null;
}

export interface PipelineRunResultDTO {
  pipeline_run_id: string;
  pipeline_spec_id: string;
  pipeline_role: string;
  model_id: string;
  model_family?: string | null;
  status: string;
  hpo_enabled: boolean;
  n_trials_planned: number;
  n_trials_completed: number;
  n_trials_failed: number;
  best_trial_id?: string | null;
  model_artifact_paths: string[];
  prediction_artifact_paths: string[];
  duration_seconds: number;
  warnings: string[];
  error_message?: string | null;
}

export interface MetricEvaluationInputDTO {
  pipeline_execution_id: string;
  pipeline_generation_id: string;
  task_id: string;
  task_type?: string | null;
  target_column?: string | null;
  primary_metric?: string | null;
  metric_direction: string;
  evaluation_plan: Record<string, unknown>;
  validation_plan: Record<string, unknown>;
  trial_results: Record<string, unknown>[];
  prediction_artifacts: string[];
  model_artifacts: string[];
  ready_for_metric_evaluation: boolean;
}

export interface TrainingArtifactManifestDTO {
  pipeline_execution_id: string;
  training_artifact_dir: string;
  manifest_path?: string | null;
  execution_result_path?: string | null;
  trial_results_path?: string | null;
  prediction_paths: string[];
  model_paths: string[];
  log_path?: string | null;
  split_metadata_path?: string | null;
  metric_evaluation_input_path?: string | null;
  external_test_prediction_path?: string | null;
  final_train_test_prediction_path?: string | null;
  external_test_metadata?: Record<string, unknown> | null;
}

export interface ExecutionSummaryDTO {
  pipeline_execution_id: string;
  task_id: string;
  pipeline_generation_id: string;
  status: string;
  execution_mode: string;
  n_pipeline_specs: number;
  n_trials_planned: number;
  n_trials_completed: number;
  n_trials_failed: number;
  n_models_trained: number;
  duration_seconds: number;
  ready_for_metric_evaluation: boolean;
}

export interface RuntimeEnvironmentDTO {
  python_version?: string | null;
  platform?: string | null;
  scikit_learn_version?: string | null;
  pandas_version?: string | null;
  numpy_version?: string | null;
  joblib_version?: string | null;
}

export interface PipelineExecutionResponse {
  pipeline_execution_id?: string | null;
  task_id?: string | null;
  pipeline_generation_id?: string | null;
  status: string;
  execution_mode: string;
  n_pipeline_specs: number;
  n_trials_planned: number;
  n_trials_completed: number;
  n_trials_failed: number;
  n_models_trained: number;
  started_at?: string | null;
  finished_at?: string | null;
  duration_seconds: number;
  execution_summary?: ExecutionSummaryDTO | null;
  pipeline_run_results: PipelineRunResultDTO[];
  trial_results: TrialResultDTO[];
  training_artifact_manifest?: TrainingArtifactManifestDTO | null;
  runtime_environment?: RuntimeEnvironmentDTO | null;
  metric_evaluation_input?: MetricEvaluationInputDTO | null;
  ready_for_metric_evaluation: boolean;
  warnings: string[];
  error_message?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PipelineExecutionSummary {
  pipeline_execution_id: string;
  task_id: string;
  status: string;
  n_pipeline_specs: number;
  n_trials_planned: number;
  n_trials_completed: number;
  n_trials_failed: number;
  n_models_trained: number;
  ready_for_metric_evaluation: boolean;
  duration_seconds: number;
  warnings: string[];
  created_at?: string | null;
}

export interface LogsResponse {
  pipeline_execution_id: string;
  status: string;
  started_at?: string | null;
  finished_at?: string | null;
  duration_seconds: number;
  event_log: Record<string, unknown>[];
  error_message?: string | null;
  warnings: string[];
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}
