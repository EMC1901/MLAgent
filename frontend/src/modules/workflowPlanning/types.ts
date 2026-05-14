// ---- Core Workflow Plan sub-types ----

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

// ---- Decision Rationale (new capability-aware) ----

export interface DecisionRationale {
  reason: string;
  evidence: string[];
  material_science_basis: string;
  expected_benefit: string;
  risk: string;
  fallback: string;
}

// ---- Feature Strategy (new capability-aware) ----

export interface SelectedFeatureAction {
  action_id: string;
  capability_id: string;
  priority: string;
  input_columns: string[];
  parameters: Record<string, unknown>;
  output_feature_group: string;
  decision_rationale: DecisionRationale;
}

export interface RejectedFeatureAction {
  capability_id: string;
  reason: string;
  evidence: string[];
}

export interface FallbackStrategy {
  fallback_actions: string[];
  trigger_conditions: string[];
}

export interface FeatureGroupExpectation {
  feature_group: string;
  expected_signal: string;
  known_limitations: string;
}

export interface InputModalityAssessment {
  detected_modalities: string[];
  usable_modalities: string[];
  unusable_modalities: string[];
  rationale: string;
}

// ---- Preprocessing Intent (new) ----

export interface PreprocessingIntent {
  intent_id?: string;
  high_level_goals: string[];
  risks_to_check_after_feature_engineering: string[];
  non_final_notes: string;
}

// ---- Workflow Rationale (new) ----

export interface WorkflowRationale {
  overall_reasoning_summary: string;
  key_assumptions: string[];
  known_risks: string[];
}

// ---- Execution Hints (new) ----

export interface FallbackRule {
  trigger: string;
  action: string;
  rationale: string;
}

export interface ExecutionHints {
  module_order: string[];
  fallback_rules: FallbackRule[];
  resource_guidance: string;
}

// ---- Legacy Feature Strategy (backward compat) ----

export interface FeatureStrategy {
  feature_type?: string;
  executable_featurizers?: string[];
  semantic_featurizers?: string[];
  unsupported_future_featurizers?: string[];
  recommended_featurizers?: string[];
  requires_structure_features?: boolean;
  feature_selection_required?: boolean;
  feature_scaling_required?: boolean;

  // New capability-aware fields
  selected_feature_actions?: SelectedFeatureAction[];
  rejected_feature_actions?: RejectedFeatureAction[];
  fallback_strategy?: FallbackStrategy;
  feature_group_expectations?: FeatureGroupExpectation[];
  input_modality_assessment?: InputModalityAssessment;
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

// ---- Main Workflow Plan Response ----

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

  // New fields
  preprocessing_intent?: PreprocessingIntent;
  workflow_rationale?: WorkflowRationale;
  execution_hints?: ExecutionHints;
  fe_registry_snapshot_version?: string;

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

// ---- Sub-resource responses ----

export interface FeatureStrategyResponse {
  plan_id: string;
  feature_strategy: FeatureStrategy;
}

export interface FeatureStrategyRationaleResponse {
  plan_id: string;
  rationales: DecisionRationale[];
  rejected_rationales: RejectedFeatureAction[];
}

export interface PreprocessingIntentResponse {
  plan_id: string;
  preprocessing_intent: PreprocessingIntent;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}
