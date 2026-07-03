export interface MetricEvaluationCreateRequest {
  force_rerun?: boolean;
  pipeline_execution_id?: string | null;
  include_fold_metrics?: boolean;
  include_baseline_comparison?: boolean;
  include_ranking_details?: boolean;
  metric_profile?: string;
  notes?: string | null;
}

export interface FoldMetricResult {
  fold_metric_id: string;
  trial_id: string;
  pipeline_spec_id: string;
  model_id: string;
  fold_index: number;
  n_samples: number;
  metrics: Record<string, number>;
  primary_metric_value?: number | null;
  prediction_artifact_path?: string | null;
  status: string;
  warnings: string[];
  error_message?: string | null;
}

export interface TrialMetricResult {
  trial_id: string;
  pipeline_spec_id: string;
  pipeline_run_id: string;
  model_id: string;
  model_family?: string | null;
  pipeline_role?: string | null;
  trial_type?: string | null;
  params: Record<string, unknown>;
  n_folds: number;
  fold_metrics: FoldMetricResult[];
  aggregated_metrics: Record<string, number>;
  primary_metric_mean?: number | null;
  primary_metric_std?: number | null;
  primary_metric_min?: number | null;
  primary_metric_max?: number | null;
  rank?: number | null;
  is_best_trial: boolean;
  status: string;
  warnings: string[];
}

export interface PipelineMetricResult {
  pipeline_spec_id: string;
  pipeline_run_id: string;
  model_id: string;
  model_family?: string | null;
  pipeline_role?: string | null;
  n_trials_evaluated: number;
  best_trial_id?: string | null;
  best_primary_metric_value?: number | null;
  mean_primary_metric_value?: number | null;
  std_primary_metric_value?: number | null;
  best_trial_params: Record<string, unknown>;
  rank?: number | null;
  is_best_model: boolean;
  warnings: string[];
}

export interface ModelRankingItem {
  rank: number;
  model_id: string;
  model_family?: string | null;
  pipeline_spec_id: string;
  best_trial_id?: string | null;
  primary_metric?: string | null;
  primary_metric_value?: number | null;
  metric_direction: string;
  improvement_over_best_baseline?: number | null;
  improvement_percentage?: number | null;
  stability_score?: number | null;
  ranking_reason: string;
}

export interface BaselineComparison {
  baseline_available: boolean;
  best_baseline_model_id?: string | null;
  best_baseline_trial_id?: string | null;
  best_baseline_metric_value?: number | null;
  best_candidate_model_id?: string | null;
  best_candidate_trial_id?: string | null;
  best_candidate_metric_value?: number | null;
  absolute_improvement?: number | null;
  relative_improvement_percentage?: number | null;
  candidate_beats_baseline: boolean;
  comparison_notes: string[];
}

export interface MetricValidationResult {
  is_valid: boolean;
  all_metrics_finite: boolean;
  primary_metric_present: boolean;
  ranking_consistent: boolean;
  best_trial_in_results: boolean;
  baseline_references_valid: boolean;
  diagnosis_input_complete: boolean;
  issues: string[];
}

export interface EvaluationArtifactManifest {
  metric_evaluation_id: string;
  pipeline_execution_id: string;
  artifact_dir: string;
  manifest_path?: string | null;
  metric_results_path?: string | null;
  fold_metrics_path?: string | null;
  trial_metrics_path?: string | null;
  pipeline_metrics_path?: string | null;
  model_ranking_path?: string | null;
  baseline_comparison_path?: string | null;
  result_diagnosis_input_path?: string | null;
}

export interface MetricSummary {
  primary_metric?: string | null;
  metric_direction: string;
  best_metric_value?: number | null;
  worst_metric_value?: number | null;
  mean_metric_value?: number | null;
  std_metric_value?: number | null;
  n_trials_contributing: number;
  n_models_contributing: number;
}

export interface ResultDiagnosisInput {
  metric_evaluation_id: string;
  pipeline_execution_id: string;
  task_id: string;
  task_type?: string | null;
  primary_metric?: string | null;
  metric_direction: string;
  best_trial?: Record<string, unknown> | null;
  best_model?: Record<string, unknown> | null;
  model_ranking: ModelRankingItem[];
  baseline_comparison?: BaselineComparison | null;
  metric_summary?: MetricSummary | null;
  failed_trials_summary: Record<string, unknown>;
  stability_summary: Record<string, unknown>;
  evaluation_warnings: string[];
  ready_for_result_diagnosis: boolean;
}

export interface FinalHoldoutEvaluation {
  available: boolean;
  split: string;
  prediction_artifact_path?: string | null;
  model_id?: string | null;
  trial_id?: string | null;
  n_test_samples: number;
  r2_test?: number | null;
  rmse_test?: number | null;
  mae_test?: number | null;
  notes: string[];
}
export interface MetricEvaluationResponse {
  metric_evaluation_id?: string | null;
  task_id?: string | null;
  pipeline_execution_id?: string | null;
  pipeline_generation_id?: string | null;
  status: string;
  task_type?: string | null;
  primary_metric?: string | null;
  metric_direction: string;
  n_trials_evaluated: number;
  n_trials_failed: number;
  n_models_evaluated: number;
  best_trial_id?: string | null;
  best_model_id?: string | null;
  best_pipeline_spec_id?: string | null;
  metric_summary?: MetricSummary | null;
  final_holdout_evaluation?: FinalHoldoutEvaluation | null;
  trial_metric_results: TrialMetricResult[];
  pipeline_metric_results: PipelineMetricResult[];
  fold_metric_results: FoldMetricResult[];
  model_ranking: ModelRankingItem[];
  baseline_comparison?: BaselineComparison | null;
  metric_validation_result?: MetricValidationResult | null;
  evaluation_artifact_manifest?: EvaluationArtifactManifest | null;
  result_diagnosis_input?: ResultDiagnosisInput | null;
  ready_for_result_diagnosis: boolean;
  warnings: string[];
  error_message?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface MetricEvaluationSummary {
  metric_evaluation_id: string;
  task_id: string;
  status: string;
  primary_metric?: string | null;
  best_model_id?: string | null;
  best_trial_id?: string | null;
  best_metric_value?: number | null;
  baseline_improvement?: number | null;
  ready_for_result_diagnosis: boolean;
  created_at?: string | null;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}
