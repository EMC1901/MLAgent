export interface IterationDecisionCreateRequest {
  metric_evaluation_id?: string | null;
  force_rerun?: boolean;
  max_iterations?: number;
  current_iteration_index?: number | null;
  minimum_improvement_threshold?: number | null;
  notes?: string | null;
}

export interface EvidenceItem {
  evidence_type: string;
  source_module: string;
  source_field: string;
  value?: unknown;
  interpretation: string;
}

export interface EvidenceBundle {
  ml_performance: EvidenceItem[];
  materials: EvidenceItem[];
  workflow_quality: EvidenceItem[];
  history_trends: EvidenceItem[];
}

export interface SystemChecks {
  weak_baseline_improvement: boolean;
  high_fold_variance: boolean;
  all_models_weak: boolean;
  hpo_budget_limited: boolean;
  candidate_underperforms_baseline: boolean;
  unstable_best_model: boolean;
  small_sample_warning: boolean;
  feature_count_low: boolean;
  many_features_dropped: boolean;
  physics_constraint_violated: boolean;
  feature_materials_relevance_low: boolean;
  chemical_space_coverage_low: boolean;
  max_iterations_reached: boolean;
  no_improvement_trend: boolean;
  repeated_root_cause: boolean;
  additional_checks: Record<string, unknown>;
  warnings: string[];
}

export interface TaskCompletionAssessment {
  completion_level: string;
  target_metric?: string | null;
  target_value?: number | null;
  actual_value?: number | null;
  gap_description: string;
  physics_constraints_satisfied: boolean;
  physics_violations: string[];
}

export interface GapAnalysis {
  primary_gap: string;
  gap_magnitude: string;
  contributing_factors: string[];
}

export interface RootCauseAnalysis {
  primary_root_cause: string;
  dimension: string;
  causal_chain: string;
  upstream_stage_at_fault?: string | null;
  supporting_evidence: string[];
}

export interface ImprovementPotential {
  estimate: string;
  key_levers: string[];
  estimated_effort: string;
}

export interface DecisionReasoning {
  task_completion: TaskCompletionAssessment;
  performance_assessment: string;
  gap_analysis: GapAnalysis;
  root_cause: RootCauseAnalysis;
  improvement_potential: ImprovementPotential;
  final_reasoning_summary: string;
}

export interface StageChange {
  stage: string;
  action: string;
  description: string;
  rationale: string;
  specific_instructions?: Record<string, unknown> | null;
}

export interface IterationPlan {
  rerun_from_stage: string;
  stage_changes: StageChange[];
  preserved_stages: string[];
  expected_improvement: string;
  estimated_remaining_iterations: number;
  stop_condition: string;
}

export interface StopRationale {
  primary_reason: string;
  category: string;
  supporting_reasons: string[];
  best_result_summary: string;
}

export interface RevisedWorkflowPlan {
  status: string;
  planning_mode: string;
  task_summary?: Record<string, unknown> | null;
  data_strategy?: Record<string, unknown> | null;
  feature_strategy?: Record<string, unknown> | null;
  model_strategy?: Record<string, unknown> | null;
  validation_strategy?: Record<string, unknown> | null;
  evaluation_strategy?: Record<string, unknown> | null;
  hpo_strategy?: Record<string, unknown> | null;
  changed_sections: string[];
  preserved_sections: string[];
  planning_warnings: string[];
  llm_reasoning_summary: string;
}

export interface IterationRerunPlan {
  next_iteration_index: number;
  rerun_from_stage?: string | null;
  rerun_stages: string[];
  reuse_artifacts: string[];
  invalidate_artifacts: string[];
  expected_improvement_targets: string[];
  minimum_improvement_threshold?: number | null;
  stop_after_next_iteration_if_no_gain: boolean;
  reasoning: string;
}

export interface ArtifactManifest {
  manifest_path?: string | null;
  decision_result_path?: string | null;
  context_path?: string | null;
  evidence_path?: string | null;
  system_checks_path?: string | null;
  llm_request_path?: string | null;
  llm_response_path?: string | null;
  iteration_plan_path?: string | null;
  revised_workflow_plan_path?: string | null;
  stop_output_path?: string | null;
}

export interface IterationDecisionResponse {
  iteration_decision_id?: string | null;
  task_id?: string | null;
  metric_evaluation_id?: string | null;
  iteration_index: number;
  status: string;
  decision?: string | null;
  decision_confidence?: string | null;
  reasoning?: DecisionReasoning | null;
  evidence_basis: EvidenceItem[];

  // ITERATE path
  iteration_plan?: IterationPlan | null;
  revised_workflow_plan?: RevisedWorkflowPlan | null;
  iteration_rerun_plan?: IterationRerunPlan | null;
  ready_for_iteration: boolean;

  // STOP path
  stop_rationale?: StopRationale | null;

  // Diagnostics
  evidence_bundle?: EvidenceBundle | null;
  system_checks?: SystemChecks | null;
  artifact_manifest?: ArtifactManifest | null;

  warnings: string[];
  error_message?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface IterationDecisionSummary {
  iteration_decision_id: string;
  task_id: string;
  iteration_index: number;
  status: string;
  decision?: string | null;
  confidence?: string | null;
  primary_root_cause?: string | null;
  rerun_from_stage?: string | null;
  ready_for_iteration: boolean;
  reasoning_summary: string;
  created_at?: string | null;
}

export interface AdoptRevisedPlanResult {
  adopted: boolean;
  iteration_decision_id: string;
  adopted_workflow_plan_id: string;
  rerun_from_stage?: string | null;
  rerun_stages: string[];
  reuse_artifacts: string[];
  invalidate_artifacts: string[];
  reasoning: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}
