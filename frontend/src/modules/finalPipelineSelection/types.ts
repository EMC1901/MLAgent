export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}

export interface FinalPipelineSelectionCreateRequest {
  workflow_refinement_id?: string;
  force_rerun?: boolean;
  selection_profile?: string;
  use_llm_explainer?: boolean;
  allow_baseline_as_final?: boolean;
  min_baseline_improvement_required?: boolean;
  stability_weight?: number;
  interpretability_weight?: number;
  cost_weight?: number;
  require_model_artifact?: boolean;
  require_prediction_artifact?: boolean;
  notes?: string;
}

export interface CandidateSelectionItem {
  candidate_id: string;
  metric_evaluation_id?: string;
  pipeline_execution_id?: string;
  pipeline_generation_id?: string;
  pipeline_spec_id?: string;
  trial_id?: string;
  model_id?: string;
  model_family?: string;
  pipeline_role: string;
  trial_type: string;
  hyperparameters: Record<string, unknown>;
  primary_metric_value?: number;
  primary_metric_rank?: number;
  primary_metric_score: number;
  stability_score: number;
  baseline_improvement_score: number;
  interpretability_score: number;
  cost_score: number;
  constraint_score: number;
  selection_score: number;
  selection_rank?: number;
  candidate_status: string;
  is_final_selected: boolean;
  rejection_reason?: string;
}

export interface SystemSelectionReason {
  main_reason: string;
  metric_reason: string;
  stability_reason: string;
  baseline_reason: string;
  interpretability_reason: string;
  cost_reason: string;
  constraint_reason: string;
  artifact_reason: string;
  tradeoff_summary: string;
}

export interface CandidateDifferenceSummary {
  candidate: string;
  summary: string;
}

export interface LLMSelectionExplanation {
  why_selected: string;
  candidate_difference_summary: CandidateDifferenceSummary[];
  selection_rationale_natural_language: string;
  human_review_notes: string[];
  risk_notes: string[];
  confidence_level: string;
}

export interface FinalArtifactManifest {
  model_artifact_path?: string;
  prediction_artifact_paths: string[];
  preprocessor_artifact_path?: string;
  model_ready_matrix_path?: string;
  feature_matrix_path?: string;
  metric_results_path?: string;
  selection_result_path?: string;
  workflow_trace_paths: Record<string, string>;
  artifact_integrity_status: string;
}

export interface InterpretabilityAnalysisInput {
  final_pipeline_selection_id?: string;
  task_id?: string;
  task_type?: string;
  target_column?: string;
  final_model_id?: string;
  final_model_family?: string;
  final_trial_id?: string;
  final_pipeline_spec_id?: string;
  model_artifact_path?: string;
  model_ready_matrix_path?: string;
  feature_columns: string[];
  prediction_artifact_paths: string[];
  preprocessor_artifact_path?: string;
  primary_metric?: string;
  primary_metric_value?: number;
  secondary_metrics: Record<string, unknown>;
  interpretability_methods_recommended: string[];
  selection_reason_summary: string;
  ready_for_interpretability_analysis: boolean;
}

export interface ConstraintCheckResult {
  passed: boolean;
  hard_constraints_met: boolean;
  soft_constraints_met: boolean;
  issues: string[];
  warnings: string[];
}

export interface StabilitySummary {
  fold_std?: number;
  fold_mean?: number;
  n_folds?: number;
  stability_level: string;
}

export interface BaselineComparison {
  baseline_model_id?: string;
  baseline_metric_value?: number;
  improvement?: number;
  improvement_pct?: number;
  improvement_level: string;
}

export interface FinalPipelineSelectionResponse {
  final_pipeline_selection_id?: string;
  task_id?: string;
  workflow_refinement_id?: string;
  metric_evaluation_id?: string;
  pipeline_execution_id?: string;
  pipeline_generation_id?: string;
  status: string;
  selection_profile: string;
  final_pipeline_spec_id?: string;
  final_model_id?: string;
  final_model_family?: string;
  final_trial_id?: string;
  final_trial_type?: string;
  final_hyperparameters: Record<string, unknown>;
  primary_metric?: string;
  primary_metric_value?: number;
  metric_direction?: string;
  secondary_metrics: Record<string, unknown>;
  stability_summary?: StabilitySummary;
  baseline_comparison?: BaselineComparison;
  selection_score?: number;
  candidate_ranking: CandidateSelectionItem[];
  constraint_check_result?: ConstraintCheckResult;
  system_selection_reason?: SystemSelectionReason;
  llm_selection_explanation?: LLMSelectionExplanation;
  candidate_difference_summary: CandidateDifferenceSummary[];
  human_review_notes: string[];
  risk_notes: string[];
  llm_used: boolean;
  llm_confidence_level?: string;
  final_artifact_manifest?: FinalArtifactManifest;
  interpretability_analysis_input?: InterpretabilityAnalysisInput;
  ready_for_interpretability_analysis: boolean;
  warnings: string[];
  error_message?: string;
  created_at?: string;
  updated_at?: string;
}
