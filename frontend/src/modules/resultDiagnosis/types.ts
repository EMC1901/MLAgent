export interface ResultDiagnosisCreateRequest {
  metric_evaluation_id?: string | null;
  force_rerun?: boolean;
  use_llm?: boolean;
  include_dataset_context?: boolean;
  include_pipeline_context?: boolean;
  include_feature_context?: boolean;
  diagnosis_profile?: string;
  notes?: string | null;
}

export interface EvidenceItem {
  evidence_type: string;
  source_module: string;
  source_field: string;
  value?: unknown;
  interpretation: string;
}

export interface DiagnosticFinding {
  finding_id: string;
  diagnosis_type: string;
  severity: string;
  evidence_strength: string;
  description: string;
  evidence_items: EvidenceItem[];
  affected_models: string[];
  affected_trials: string[];
  possible_causes: string[];
  recommended_actions: string[];
  refinement_targets: string[];
  confidence_level: string;
}

export interface RootCauseHypothesis {
  hypothesis_id: string;
  root_cause_type: string;
  description: string;
  supporting_findings: string[];
  likelihood: string;
  actionability: string;
}

export interface SystemActionHint {
  suggested_feature_strategy?: string | null;
  suggested_model_family?: string | null;
  suggested_hpo_budget?: string | null;
  suggested_validation_strategy?: string | null;
}

export interface RefinementRecommendation {
  recommendation_id: string;
  target_stage: string;
  recommendation_type: string;
  priority: string;
  description: string;
  expected_benefit: string;
  risk: string;
  system_action_hint: SystemActionHint;
  requires_human_review: boolean;
}

export interface OverallAssessment {
  performance_level: string;
  baseline_improvement_level: string;
  stability_level: string;
  main_issue_category: string;
  should_refine: boolean;
  summary: string;
  confidence_level: string;
}

export interface EvidenceSummary {
  metric_evidence: EvidenceItem[];
  baseline_evidence: EvidenceItem[];
  fold_stability_evidence: EvidenceItem[];
  dataset_evidence: EvidenceItem[];
  feature_evidence: EvidenceItem[];
  pipeline_evidence: EvidenceItem[];
}

export interface SystemDiagnosticChecks {
  weak_baseline_improvement: boolean;
  high_fold_variance: boolean;
  all_models_weak: boolean;
  hpo_budget_limited: boolean;
  small_sample_warning: boolean;
  feature_count_low: boolean;
  many_features_dropped: boolean;
  candidate_underperforms_baseline: boolean;
  unstable_best_model: boolean;
  additional_checks: Record<string, unknown>;
  warnings: string[];
}

export interface LLMDiagnosisResult {
  overall_assessment?: OverallAssessment | null;
  diagnostic_findings: DiagnosticFinding[];
  root_cause_hypotheses: RootCauseHypothesis[];
  refinement_recommendations: RefinementRecommendation[];
  confidence_level: string;
}

export interface SuggestedNextIterationProfile {
  model_search_budget: string;
  hpo_trials: string;
  feature_strategy: string;
}

export interface ClosedLoopRefinementInput {
  result_diagnosis_id: string;
  metric_evaluation_id: string;
  task_id: string;
  should_refine: boolean;
  refinement_focus: string[];
  priority_recommendations: RefinementRecommendation[];
  diagnostic_findings_summary: Record<string, unknown>[];
  constraints_to_preserve: string[];
  avoid_actions: string[];
  suggested_next_iteration_profile: SuggestedNextIterationProfile;
  ready_for_closed_loop_refinement: boolean;
}

export interface DiagnosisArtifactManifest {
  manifest_path?: string | null;
  diagnosis_result_path?: string | null;
  diagnostic_context_path?: string | null;
  system_diagnostic_checks_path?: string | null;
  llm_diagnosis_path?: string | null;
  evidence_summary_path?: string | null;
  closed_loop_refinement_input_path?: string | null;
}

export interface ResultDiagnosisResponse {
  result_diagnosis_id?: string | null;
  task_id?: string | null;
  metric_evaluation_id?: string | null;
  pipeline_execution_id?: string | null;
  status: string;
  diagnosis_mode: string;
  overall_assessment?: OverallAssessment | null;
  diagnostic_findings: DiagnosticFinding[];
  evidence_summary?: EvidenceSummary | null;
  root_cause_hypotheses: RootCauseHypothesis[];
  refinement_recommendations: RefinementRecommendation[];
  closed_loop_refinement_input?: ClosedLoopRefinementInput | null;
  ready_for_closed_loop_refinement: boolean;
  llm_diagnosis?: LLMDiagnosisResult | null;
  system_diagnostic_checks?: SystemDiagnosticChecks | null;
  diagnosis_artifact_manifest?: DiagnosisArtifactManifest | null;
  warnings: string[];
  error_message?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ResultDiagnosisSummary {
  result_diagnosis_id: string;
  task_id: string;
  status: string;
  main_issue_category?: string | null;
  performance_level?: string | null;
  should_refine: boolean;
  ready_for_closed_loop_refinement: boolean;
  top_findings: Record<string, unknown>[];
  top_recommendations: Record<string, unknown>[];
  created_at?: string | null;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}
