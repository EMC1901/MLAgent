export interface PipelineGenerationCreateRequest {
  force_rerun?: boolean;
  use_llm_reviewer?: boolean;
  include_baselines?: boolean;
  include_hpo_candidates?: boolean;
  pipeline_profile?: string;
  max_pipeline_specs_override?: number | null;
  notes?: string | null;
}

export interface ArtifactManifest {
  model_ready_matrix_path?: string | null;
  preprocessor_artifact_path?: string | null;
  metadata_path?: string | null;
  model_ready_exists: boolean;
  preprocessor_exists: boolean;
  feature_columns: string[];
  n_features: number;
  target_column?: string | null;
  is_complete: boolean;
}

export interface ComponentBinding {
  model_id: string;
  model_family?: string | null;
  model_registry_valid: boolean;
  hpo_method?: string | null;
  hpo_registry_valid: boolean;
  validation_strategy?: string | null;
  validation_strategy_valid: boolean;
  primary_metric?: string | null;
  metric_valid: boolean;
  preprocessor_artifact_bound: boolean;
  model_ready_matrix_bound: boolean;
}

export interface ComponentBindingResult {
  bindings: ComponentBinding[];
  all_valid: boolean;
  errors: string[];
}

export interface SafetyConstraints {
  max_runtime_seconds: number;
  max_memory_mb: number;
  allow_unregistered_components: boolean;
  allow_dynamic_code: boolean;
  allow_network_access: boolean;
}

export interface PipelineSpec {
  pipeline_spec_id: string;
  pipeline_role: string;
  model_id: string;
  model_family?: string | null;
  model_display_name?: string | null;
  priority: string;
  hpo_enabled: boolean;
  search_space_ref?: string | null;
  fixed_params: Record<string, unknown>;
  search_space?: Record<string, unknown> | null;
  validation_plan_ref: string;
  evaluation_plan_ref: string;
  input_artifact_ref?: string | null;
  preprocessor_artifact_ref?: string | null;
  component_bindings: Record<string, unknown>;
  safety_constraints?: SafetyConstraints | null;
  execution_ready: boolean;
  warnings: string[];
}

export interface TrialAllocationItem {
  model_id: string;
  pipeline_spec_id?: string | null;
  max_trials: number;
  role: string;
}

export interface BaselineTrialPolicy {
  single_run: boolean;
  description: string;
}

export interface CandidateTrialPolicy {
  expand_by_search_space: boolean;
  description: string;
}

export interface EarlyStoppingPolicy {
  enabled: boolean;
  patience: number;
  min_delta: number;
}

export interface FallbackPolicy {
  enabled: boolean;
  fallback_model_id?: string | null;
  description: string;
}

export interface TrialPlan {
  trial_plan_id: string;
  hpo_enabled: boolean;
  search_method?: string | null;
  max_total_trials: number;
  max_parallel_trials: number;
  trial_allocation: TrialAllocationItem[];
  baseline_trial_policy?: BaselineTrialPolicy | null;
  candidate_trial_policy?: CandidateTrialPolicy | null;
  early_stopping_policy?: EarlyStoppingPolicy | null;
  fallback_policy?: FallbackPolicy | null;
}

export interface ExecutionConstraints {
  max_runtime_seconds: number;
  max_memory_mb: number;
  allow_unregistered_components: boolean;
  allow_dynamic_code: boolean;
}

export interface ExecutionInput {
  pipeline_generation_id: string;
  pipeline_bundle_id: string;
  task_id: string;
  task_type?: string | null;
  model_ready_matrix_path?: string | null;
  preprocessor_artifact_path?: string | null;
  target_column?: string | null;
  feature_columns: string[];
  pipeline_specs: PipelineSpec[];
  trial_plan?: TrialPlan | null;
  validation_plan: Record<string, unknown>;
  evaluation_plan: Record<string, unknown>;
  execution_constraints?: ExecutionConstraints | null;
  ready_for_execution: boolean;
}

export interface PipelineBundle {
  bundle_id: string;
  task_id: string;
  model_search_plan_id: string;
  task_type?: string | null;
  target_column?: string | null;
  feature_columns: string[];
  primary_metric?: string | null;
  metric_direction: string;
  model_ready_matrix_path?: string | null;
  preprocessor_artifact_path?: string | null;
  pipeline_specs: PipelineSpec[];
  validation_plan: Record<string, unknown>;
  evaluation_plan: Record<string, unknown>;
  hpo_plan: Record<string, unknown>;
  execution_policy: Record<string, unknown>;
  created_by: string;
}

export interface PipelineValidationResult {
  is_valid: boolean;
  structure_valid: boolean;
  registry_valid: boolean;
  artifact_valid: boolean;
  task_type_compatible: boolean;
  search_space_valid: boolean;
  trial_valid: boolean;
  data_fields_valid: boolean;
  execution_input_valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface SafetyCheckResult {
  is_safe: boolean;
  checks: Record<string, unknown>;
  errors: string[];
  warnings: string[];
}

export interface LLMAdvisoryChecklistItem {
  dimension: string;
  status: string;
  comment: string;
}

export interface LLMAdvisoryRisk {
  category: string;
  severity: string;
  message: string;
  suggested_action: string;
}

export interface LLMAdvisoryReview {
  enabled: boolean;
  review_status: string;
  execution_impact: string;
  risk_level: string;
  confidence_level: string;
  checklist: LLMAdvisoryChecklistItem[];
  blocking_issues: LLMAdvisoryRisk[];
  non_blocking_risks: LLMAdvisoryRisk[];
  resource_warnings: string[];
  future_improvement_suggestions: string[];
  normalization_notes: string[];
  raw_llm_summary: Record<string, unknown>;
}

export interface PipelineGenerationResponse {
  pipeline_generation_id?: string | null;
  task_id?: string | null;
  model_search_plan_id?: string | null;
  feature_preprocessing_id?: string | null;
  status: string;
  generation_mode?: string | null;
  n_pipeline_specs: number;
  n_baseline_specs: number;
  n_hpo_specs: number;
  pipeline_bundle?: PipelineBundle | null;
  pipeline_specs: PipelineSpec[];
  trial_plan?: TrialPlan | null;
  component_binding_result?: ComponentBindingResult | null;
  artifact_manifest?: ArtifactManifest | null;
  pipeline_validation_result?: PipelineValidationResult | null;
  safety_check_result?: SafetyCheckResult | null;
  llm_advisory_review?: LLMAdvisoryReview | null;
  execution_input?: ExecutionInput | null;
  ready_for_execution: boolean;
  warnings: string[];
  error_message?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PipelineGenerationSummary {
  pipeline_generation_id: string;
  task_id: string;
  status: string;
  n_pipeline_specs: number;
  n_baseline_specs: number;
  n_hpo_specs: number;
  hpo_enabled: boolean;
  ready_for_execution: boolean;
  warnings: string[];
  created_at?: string | null;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}
