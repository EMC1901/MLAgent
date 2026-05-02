export interface TaskSummary {
  task_type?: string;
  input_modality?: string;
  prediction_target?: string;
  material_domain?: string;
  primary_goal?: string;
}

export interface TargetHandling {
  requires_transformation_check?: boolean;
  recommended_transformation?: string;
}

export interface DataStrategy {
  input_columns?: string[];
  target_column?: string;
  required_cleaning_steps?: string[];
  target_handling?: TargetHandling;
  duplicate_handling?: string;
  missing_value_strategy?: string;
}

export interface FeatureStrategy {
  feature_type?: string;
  recommended_featurizers?: string[];
  requires_structure_features?: boolean;
  feature_selection_required?: boolean;
  feature_scaling_required?: boolean;
}

export interface ModelStrategy {
  candidate_model_families?: string[];
  baseline_models?: string[];
  preferred_model_bias?: string;
  excluded_model_families?: string[];
}

export interface ValidationStrategy {
  split_strategy?: string;
  n_splits?: number;
  test_size?: number | null;
  random_state?: number;
  stratification_required?: boolean;
}

export interface EvaluationStrategy {
  primary_metric?: string;
  secondary_metrics?: string[];
  metric_direction?: string;
}

export interface HPOStrategy {
  enabled?: boolean;
  search_method?: string;
  budget_level?: string;
  max_trials?: number;
}

export interface InterpretabilityStrategy {
  enabled?: boolean;
  methods?: string[];
  priority?: string;
}

export interface RequiredComponents {
  data_cleaner?: boolean;
  featurizer?: boolean;
  model_trainer?: boolean;
  evaluator?: boolean;
}

export interface PipelineGenerationInput {
  pipeline_steps?: string[];
  required_components?: RequiredComponents;
}

export interface WorkflowPlanResponse {
  workflow_plan_id: string;
  task_id: string;
  interpretation_id?: string;
  dataset_profile_id?: string;
  status: string;
  planning_mode?: string;
  task_summary?: TaskSummary;
  data_strategy?: DataStrategy;
  feature_strategy?: FeatureStrategy;
  model_strategy?: ModelStrategy;
  validation_strategy?: ValidationStrategy;
  evaluation_strategy?: EvaluationStrategy;
  hpo_strategy?: HPOStrategy;
  interpretability_strategy?: InterpretabilityStrategy;
  pipeline_generation_input?: PipelineGenerationInput;
  planning_warnings?: string[];
  planning_assumptions?: string[];
  llm_reasoning_summary?: string;
  confidence_score?: number;
  created_at?: string;
  updated_at?: string;
}

export interface WorkflowPlanCreateRequest {
  force_rerun?: boolean;
  planning_mode?: string;
  llm_provider?: string;
  model_name?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}
