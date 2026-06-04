export interface InterpretabilityAnalysisCreateRequest {
  force_rerun?: boolean;
  use_llm_summarizer?: boolean;
  interpretability_profile?: string;
  max_shap_samples?: number;
  max_local_explanations?: number;
  include_high_error_samples?: boolean;
  include_permutation_importance?: boolean;
  include_shap?: boolean;
  notes?: string;
}

export interface GlobalFeatureImportanceItem {
  feature_name: string;
  importance_value: number;
  importance_rank: number;
  importance_method: string;
  direction: string;
  feature_group: string;
  interpretation_hint: string;
}

export interface TopShapFeature {
  feature_name: string;
  mean_abs_shap: number;
  rank: number;
  direction_summary: string;
}

export interface ShapSummary {
  shap_available: boolean;
  explainer_type: string;
  n_samples_explained: number;
  top_shap_features: TopShapFeature[];
  shap_artifact_paths?: {
    shap_values: string;
    summary_data: string;
  };
  warnings: string[];
}

export interface LocalExplanationItem {
  sample_id: string;
  y_true?: number;
  y_pred?: number;
  prediction_error?: number;
  top_positive_features: { feature: string; contribution: number }[];
  top_negative_features: { feature: string; contribution: number }[];
  local_shap_values: Record<string, number>;
  local_explanation_summary: string;
}

export interface HighErrorSampleAnalysis {
  sample_id: string;
  absolute_error: number;
  relative_error?: number;
  error_rank: number;
  possible_error_factors: string[];
  feature_pattern_summary: string;
  review_suggestion: string;
}

export interface MaterialPattern {
  pattern: string;
  supporting_features: string[];
  possible_material_meaning: string;
  evidence_strength: string;
  caution: string;
}

export interface FeatureGroupInterpretation {
  feature_group: string;
  summary: string;
}

export interface MaterialInsightSummary {
  top_material_patterns: MaterialPattern[];
  feature_groups_interpretation: FeatureGroupInterpretation[];
  domain_hypotheses: string[];
  limitations: string[];
  confidence_level: string;
}

export interface LLMInterpretabilitySummary {
  top_material_patterns: MaterialPattern[];
  feature_groups_interpretation: FeatureGroupInterpretation[];
  domain_hypotheses: string[];
  limitations: string[];
  human_review_notes: string[];
  confidence_level: string;
}

export interface InterpretabilityRiskNote {
  risk_type: string;
  description: string;
  severity: string;
}

export interface FinalOutputInput {
  interpretability_analysis_id?: string;
  task_id?: string;
  final_model_id?: string;
  final_trial_id?: string;
  model_artifact_path?: string;
  prediction_artifact_paths: string[];
  global_feature_importance: GlobalFeatureImportanceItem[];
  shap_summary?: ShapSummary;
  material_insight_summary?: MaterialInsightSummary;
  ready_for_final_output: boolean;
}

export interface InterpretabilityAnalysisResponse {
  interpretability_analysis_id?: string;
  task_id?: string;
  metric_evaluation_id?: string;
  pipeline_execution_id?: string;
  status: string;
  analysis_profile: string;
  final_model_id?: string;
  final_model_family?: string;
  final_trial_id?: string;
  interpretability_methods_used: string[];
  global_feature_importance: GlobalFeatureImportanceItem[];
  permutation_importance: Record<string, unknown>[];
  shap_summary?: ShapSummary;
  local_explanations: LocalExplanationItem[];
  high_error_sample_analysis: HighErrorSampleAnalysis[];
  feature_group_summary?: Record<string, unknown>;
  material_insight_summary?: MaterialInsightSummary;
  llm_interpretability_summary?: LLMInterpretabilitySummary;
  interpretability_risk_notes: InterpretabilityRiskNote[];
  analysis_artifact_manifest?: Record<string, unknown>;
  final_output_input?: FinalOutputInput;
  ready_for_final_output: boolean;
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
