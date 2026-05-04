export interface ModelSearchPlanCreateRequest {
  force_rerun?: boolean;
  use_llm_advisor?: boolean;
  max_total_trials_override?: number | null;
  preferred_search_method?: string | null;
  include_models: string[];
  exclude_models: string[];
}

export interface DatasetContext {
  model_ready_matrix_path?: string | null;
  preprocessing_pipeline_artifact_id?: string | null;
  n_samples: number;
  n_features: number;
  target_column?: string | null;
  task_type?: string | null;
  primary_metric?: string | null;
}

export interface BaselineModelPlan {
  model_id: string;
  role: string;
  hpo_enabled: boolean;
}

export interface CandidateModelPlan {
  model_id: string;
  model_family: string;
  priority: string;
  hpo_enabled: boolean;
  reason?: string | null;
}

export interface ExcludedModelPlan {
  model_id: string;
  reason?: string | null;
}

export interface CandidateModelPlanGroup {
  baseline_models: BaselineModelPlan[];
  candidate_models: CandidateModelPlan[];
  excluded_models: ExcludedModelPlan[];
}

export interface TrialAllocationItem {
  model_id: string;
  max_trials: number;
}

export interface HPOPlan {
  enabled: boolean;
  search_method?: string | null;
  budget_level: string;
  max_total_trials: number;
  max_parallel_trials: number;
  trial_allocation: TrialAllocationItem[];
  early_stopping: boolean;
  fallback_method?: string | null;
}

export interface SearchSpaceParameter {
  name: string;
  param_type: string;
  low?: number | null;
  high?: number | null;
  choices: string[];
  sampling: string;
  default_value?: string | null;
}

export interface SearchSpaceItem {
  model_id: string;
  search_space_id: string;
  parameters: SearchSpaceParameter[];
}

export interface SearchSpacePlan {
  spaces: SearchSpaceItem[];
}

export interface ValidationPlan {
  split_strategy: string;
  n_splits: number;
  random_state: number;
  shuffle: boolean;
  stratification_required: boolean;
  benchmark_split: boolean;
}

export interface EvaluationPlan {
  primary_metric?: string | null;
  metric_direction: string;
  secondary_metrics: string[];
  scorer_id?: string | null;
}

export interface LLMModelSearchAdvice {
  used: boolean;
  confidence_score: number;
  summary?: string | null;
}

export interface SysValidationResult {
  is_valid: boolean;
  rejected_models: string[];
  rejected_hpo_methods: string[];
  fallback_applied: boolean;
  warnings: string[];
}

export interface PipelineGenerationInput {
  model_ready_matrix_path?: string | null;
  preprocessing_pipeline_artifact_id?: string | null;
  target_column?: string | null;
  feature_columns: string[];
  candidate_model_plan: Record<string, unknown>;
  hpo_plan: Record<string, unknown>;
  search_space_plan: Record<string, unknown>;
  validation_plan: Record<string, unknown>;
  evaluation_plan: Record<string, unknown>;
  ready_for_pipeline_generation: boolean;
}

export interface ModelSearchPlanResponse {
  model_search_plan_id?: string | null;
  task_id?: string | null;
  model_search_context_id?: string | null;
  feature_preprocessing_id?: string | null;
  workflow_plan_id?: string | null;
  status: string;
  planning_mode?: string | null;
  dataset_context?: DatasetContext | null;
  candidate_model_plan?: CandidateModelPlanGroup | null;
  hpo_plan?: HPOPlan | null;
  search_space_plan?: SearchSpacePlan | null;
  validation_plan?: ValidationPlan | null;
  evaluation_plan?: EvaluationPlan | null;
  llm_model_search_advice?: LLMModelSearchAdvice | null;
  system_validation_result?: SysValidationResult | null;
  pipeline_generation_input?: PipelineGenerationInput | null;
  warnings: string[];
  errors: string[];
  error_message?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ModelSearchPlanSummary {
  model_search_plan_id: string;
  task_id: string;
  status: string;
  task_type?: string | null;
  primary_metric?: string | null;
  n_candidate_models: number;
  hpo_enabled: boolean;
  hpo_method?: string | null;
  max_total_trials: number;
  ready_for_pipeline_generation: boolean;
  n_warnings: number;
  n_errors: number;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}
