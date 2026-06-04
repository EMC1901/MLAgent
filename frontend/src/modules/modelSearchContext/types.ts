export interface ModelSearchContextCreateRequest {
  force_rerun?: boolean;
  use_llm_advisor?: boolean;
  adjust_model_strategy?: boolean;
  adjust_hpo_strategy?: boolean;
  adjust_validation_strategy?: boolean;
  adjust_evaluation_strategy?: boolean;
}

export interface DatasetEffectiveProfile {
  n_samples: number;
  n_raw_features: number;
  n_final_features: number;
  n_dropped_features: number;
  feature_reduction_ratio: number;
  target_column?: string | null;
  task_type?: string | null;
}

export interface FeatureGroupSummary {
  retained_groups: string[];
  dropped_groups: string[];
  partially_retained_groups: string[];
  low_effective_feature_warning: boolean;
}

export interface StrategyChangeRationale {
  reason: string;
  evidence: string[];
  expected_benefit: string;
  risk: string;
  fallback: string;
}

export interface StrategyChange {
  strategy_area: string;
  field_path: string;
  original_value: any;
  updated_value: any;
  change_type: string;
  decision_rationale?: StrategyChangeRationale | null;
}

export interface PreprocessingSummary {
  imputation_executed: boolean;
  scaling_executed: boolean;
  feature_selection_executed: boolean;
  categorical_encoding_executed: boolean;
  preprocessing_pipeline_artifact_id?: string | null;
  // Fold-safe execution mode — "global" | "fold_safe" | "none"
  imputation_execution_mode?: string | null;
  scaling_execution_mode?: string | null;
  feature_selection_execution_mode?: string | null;
  // Deferred fold operations summary
  fold_safe_deferred?: Record<string, unknown> | null;
}

export interface LLMStrategyAdvice {
  candidate_model_families: string[];
  baseline_models: string[];
  preferred_model_bias?: string | null;
  hpo_search_method?: string | null;
  hpo_budget_level: string;
  max_trials: number;
  validation_split_strategy?: string | null;
  n_splits: number;
  adjustment_reasons: string[];
  risk_notes: string[];
  confidence_score: number;
}

export interface SystemValidationResult {
  is_valid: boolean;
  rejected_suggestions: string[];
  fallback_applied: boolean;
}

export interface StrategyAdjustment {
  model_strategy_adjusted: boolean;
  hpo_strategy_adjusted: boolean;
  validation_strategy_adjusted: boolean;
  evaluation_strategy_adjusted: boolean;
  adjustment_reasons: string[];
}

export interface ModelSearchContextInput {
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
  ready_for_pipeline_generation: boolean;
}

// ---- Execution Plan Types (merged from model search) ----

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
  allocation_rationale?: string | null;
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
  choices: (string | number)[];
  sampling: string;
  default_value?: string | null;
  override_rationale?: string | null;
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

// ---- Response ----

export interface ModelSearchContextResponse {
  context_id: string;
  task_id: string;
  workflow_plan_id?: string | null;
  feature_engineering_id?: string | null;
  feature_preprocessing_id?: string | null;
  status: string;
  update_mode?: string | null;
  dataset_effective_profile?: DatasetEffectiveProfile | null;
  feature_group_summary?: FeatureGroupSummary | null;
  preprocessing_summary?: PreprocessingSummary | null;
  llm_strategy_advice?: LLMStrategyAdvice | null;
  system_validation_result?: SystemValidationResult | null;
  strategy_adjustment?: StrategyAdjustment | null;
  updated_model_strategy: Record<string, unknown>;
  updated_hpo_strategy: Record<string, unknown>;
  updated_validation_strategy: Record<string, unknown>;
  updated_evaluation_strategy: Record<string, unknown>;
  model_search_context_input?: ModelSearchContextInput | null;
  // Execution plans
  candidate_model_plan?: CandidateModelPlanGroup | null;
  hpo_plan?: HPOPlan | null;
  search_space_plan?: SearchSpacePlan | null;
  validation_plan?: ValidationPlan | null;
  evaluation_plan?: EvaluationPlan | null;
  pipeline_generation_input?: PipelineGenerationInput | null;
  strategy_changes: StrategyChange[];
  strategy_change_summary?: string | null;
  warnings: string[];
  errors: string[];
  error_message?: string | null;
  confidence_score?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}
