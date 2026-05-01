export interface InterpretedPredictionTarget {
  raw_target?: string;
  normalized_target?: string;
  target_category?: string;
  target_unit?: string;
  target_description?: string;
}

export interface ModelingIntent {
  primary_goal?: string;
  secondary_goals?: string[];
  optimization_direction?: string;
  preferred_metric?: string;
}

export interface DatasetLoadingHint {
  source_type?: string;
  possible_loader?: string;
  needs_file_upload?: boolean;
}

export interface DatasetIntent {
  dataset_reference?: string;
  expected_input_columns?: string[];
  expected_target_column?: string;
  requires_structure_file?: boolean;
  dataset_loading_hint?: DatasetLoadingHint | null;
}

export interface PlanningHint {
  task_family?: string;
  input_representation?: string;
  requires_feature_engineering?: boolean;
  requires_model_interpretability?: boolean;
  suggested_metric_direction?: string;
}

export interface ConstraintInterpretation {
  hard_constraints?: string[];
  soft_constraints?: string[];
  potential_conflicts?: string[];
}

export interface RecommendedDefaults {
  evaluation_metric?: string;
  validation_strategy?: string;
  baseline_requirement?: boolean;
}

export interface AmbiguityItem {
  field?: string;
  message?: string;
  severity?: string;
}

export interface TaskInterpretationResponse {
  interpretation_id: string;
  task_id: string;
  status: string;
  interpreted_task_type?: string;
  interpreted_input_modality?: string;
  interpreted_material_domain?: string;
  interpreted_prediction_target?: InterpretedPredictionTarget;
  modeling_intent?: ModelingIntent;
  dataset_intent?: DatasetIntent;
  planning_hint?: PlanningHint;
  constraint_interpretation?: ConstraintInterpretation;
  recommended_defaults?: RecommendedDefaults;
  ambiguities?: AmbiguityItem[];
  warnings?: string[];
  llm_reasoning_summary?: string;
  confidence_score?: number;
  created_at?: string;
  updated_at?: string;
}

export interface TaskInterpretationCreateRequest {
  force_rerun?: boolean;
  llm_provider?: string;
  model_name?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}
