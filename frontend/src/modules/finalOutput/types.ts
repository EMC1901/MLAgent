export interface FinalOutputCreateRequest {
  interpretability_analysis_id?: string;
  force_rerun?: boolean;
  use_llm_report_writer?: boolean;
  report_profile?: string;
  output_format?: string[];
  include_model_artifact?: boolean;
  include_prediction_artifact?: boolean;
  include_workflow_trace?: boolean;
  include_interpretability_artifacts?: boolean;
  include_reproducibility_summary?: boolean;
  notes?: string;
}

export interface FinalModelSummary {
  final_model_id: string;
  final_model_family: string;
  final_trial_id: string;
  final_pipeline_spec_id: string;
  final_hyperparameters: Record<string, unknown>;
  model_artifact_path: string;
  selection_reason_summary: string;
}

export interface FinalMetricSummary {
  primary_metric: string;
  primary_metric_value?: number;
  metric_direction: string;
  secondary_metrics: Record<string, unknown>;
  baseline_comparison: Record<string, unknown>;
  model_ranking_position?: number;
  stability_summary: Record<string, unknown>;
}

export interface InterpretabilitySummary {
  interpretability_analysis_id: string;
  methods_used: string[];
  top_features: Record<string, unknown>[];
  shap_summary?: Record<string, unknown>;
  material_insight_summary?: Record<string, unknown>;
  interpretability_risk_notes: string[];
  artifact_paths: Record<string, string>;
}

export interface WorkflowTraceSummary {
  task_specification_id?: string;
  task_interpretation_id?: string;
  dataset_profile_id?: string;
  workflow_plan_id?: string;
  feature_engineering_id?: string;
  feature_preprocessing_id?: string;
  model_search_context_id?: string;
  pipeline_generation_id?: string;
  pipeline_execution_id?: string;
  metric_evaluation_id?: string;
  iteration_decision_id?: string;
  interpretability_analysis_id?: string;
  iteration_count: number;
  workflow_trace_artifacts: Record<string, unknown>;
}

export interface ReproducibilitySummary {
  dataset_source: string;
  target_column: string;
  feature_columns_count?: number;
  feature_artifact_path: string;
  preprocessor_artifact_path: string;
  model_ready_matrix_path: string;
  model_artifact_path: string;
  prediction_artifact_paths: string[];
  random_state?: number;
  validation_strategy: Record<string, unknown>;
  hpo_summary: Record<string, unknown>;
  environment_summary: Record<string, unknown>;
  registry_versions: Record<string, unknown>;
  created_at?: string;
}

export interface FinalReport {
  title: string;
  executive_summary: string;
  task_overview: string;
  dataset_summary: string;
  workflow_summary: string;
  feature_engineering_summary: string;
  model_search_summary: string;
  final_model_summary: string;
  metric_summary: string;
  interpretability_summary: string;
  material_insight_summary: string;
  limitations_and_risks: string;
  reproducibility_notes: string;
  artifact_summary: string;
  next_steps: string;
}

export interface OutputPackageManifest {
  output_package_id: string;
  package_root_dir: string;
  json_report_path: string;
  markdown_report_path: string;
  model_artifact_path: string;
  prediction_artifact_paths: string[];
  interpretability_artifact_paths: Record<string, string>;
  workflow_trace_path: string;
  manifest_path: string;
  package_zip_path?: string;
  package_status: string;
}

export interface DownloadLinks {
  json_report: string;
  markdown_report: string;
  manifest: string;
  workflow_trace: string;
  reproducibility_summary: string;
  output_package_dir: string;
  model_artifact_ref: string;
  prediction_artifact_refs: string[];
}

export interface FinalOutputResponse {
  final_output_id?: string;
  task_id?: string;
  interpretability_analysis_id?: string;
  status: string;
  report_profile: string;
  final_model_summary?: Record<string, unknown>;
  final_metric_summary?: Record<string, unknown>;
  interpretability_summary?: Record<string, unknown>;
  workflow_trace_summary?: Record<string, unknown>;
  reproducibility_summary?: Record<string, unknown>;
  final_artifact_manifest?: Record<string, unknown>;
  final_report?: Record<string, unknown>;
  llm_report_summary?: Record<string, unknown>;
  output_package_manifest?: Record<string, unknown>;
  download_links?: Record<string, unknown>;
  topic_files?: { file: string; topic: string }[];
  ready_for_delivery: boolean;
  warnings: string[];
  error_message?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}
