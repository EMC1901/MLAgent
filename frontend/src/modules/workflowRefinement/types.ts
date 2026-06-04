export interface WorkflowRefinementCreateRequest {
  result_diagnosis_id?: string | null;
  force_rerun?: boolean;
  use_llm?: boolean;
  max_iterations?: number;
  current_iteration_index?: number | null;
  decision_profile?: string;
  allow_full_workflow_rerun?: boolean;
  allow_partial_rerun?: boolean;
  minimum_improvement_threshold?: number | null;
  notes?: string | null;
}

export interface WorkflowRefinementDecisionDTO {
  decision: string;
  decision_confidence_level: string;
  primary_reason: string;
  should_generate_revised_workflow_plan: boolean;
  recommended_rerun_from_stage?: string | null;
}

export interface DecisionReasoning {
  performance_assessment: string;
  baseline_assessment: string;
  stability_assessment: string;
  diagnosis_assessment: string;
  cost_assessment: string;
  risk_assessment: string;
  final_reasoning_summary: string;
}

export interface EvidenceUsed {
  evidence_id: string;
  source_module: string;
  evidence_type: string;
  source_field: string;
  value?: unknown;
  interpretation: string;
  supports_decision: string;
}

export interface RefinementMetadata {
  source_workflow_plan_id?: string | null;
  source_result_diagnosis_id?: string | null;
  changed_sections: string[];
  preserved_sections: string[];
  recommended_rerun_from_stage?: string | null;
}

export interface RevisedWorkflowPlanResponse {
  workflow_plan_id?: string | null;
  status: string;
  planning_mode: string;
  task_summary?: Record<string, unknown> | null;
  data_strategy?: Record<string, unknown> | null;
  feature_strategy?: Record<string, unknown> | null;
  model_strategy?: Record<string, unknown> | null;
  validation_strategy?: Record<string, unknown> | null;
  evaluation_strategy?: Record<string, unknown> | null;
  hpo_strategy?: Record<string, unknown> | null;
  interpretability_strategy?: Record<string, unknown> | null;
  pipeline_generation_input?: Record<string, unknown> | null;
  planning_warnings: string[];
  planning_assumptions: string[];
  llm_reasoning_summary: string;
  confidence_score: number;
  refinement_metadata?: RefinementMetadata | null;
}

export interface WorkflowPlanDelta {
  changed_sections: string[];
  preserved_sections: string[];
  feature_strategy_delta?: Record<string, unknown> | null;
  model_strategy_delta?: Record<string, unknown> | null;
  hpo_strategy_delta?: Record<string, unknown> | null;
  validation_strategy_delta?: Record<string, unknown> | null;
  evaluation_strategy_delta?: Record<string, unknown> | null;
  change_reason_map: Record<string, string>;
  diagnosis_to_change_map: Record<string, string>;
  rejected_or_unsafe_changes: string[];
}

export interface IterationRerunPlan {
  next_iteration_index: number;
  recommended_rerun_from_stage?: string | null;
  rerun_stages: string[];
  reuse_artifacts: string[];
  invalidate_artifacts: string[];
  expected_improvement_targets: string[];
  minimum_improvement_threshold?: number | null;
  stop_after_next_iteration_if_no_gain: boolean;
  reasoning: string;
}

export interface LLMWorkflowRefinementResult {
  workflow_refinement_decision?: WorkflowRefinementDecisionDTO | null;
  decision_reasoning?: DecisionReasoning | null;
  evidence_used: EvidenceUsed[];
  revised_workflow_plan?: Record<string, unknown> | null;
  iteration_rerun_plan?: Record<string, unknown> | null;
  confidence_level: string;
}

export interface WorkflowRefinementValidationResult {
  is_valid: boolean;
  decision_valid: boolean;
  reasoning_valid: boolean;
  revised_plan_valid?: boolean | null;
  rerun_plan_valid?: boolean | null;
  safety_scan_passed: boolean;
  issues: string[];
  warnings: string[];
}

export interface ArtifactManifest {
  manifest_path?: string | null;
  workflow_refinement_result_path?: string | null;
  llm_refinement_context_path?: string | null;
  llm_request_path?: string | null;
  llm_response_path?: string | null;
  revised_workflow_plan_path?: string | null;
  workflow_plan_delta_path?: string | null;
  iteration_rerun_plan_path?: string | null;
  validation_result_path?: string | null;
}

export interface WorkflowRefinementResponse {
  workflow_refinement_id?: string | null;
  task_id?: string | null;
  result_diagnosis_id?: string | null;
  metric_evaluation_id?: string | null;
  iteration_index: number;
  status: string;
  decision?: string | null;
  decision_confidence_level?: string | null;
  decision_reasoning?: DecisionReasoning | null;
  evidence_used: EvidenceUsed[];
  recommended_rerun_from_stage?: string | null;
  revised_workflow_plan?: RevisedWorkflowPlanResponse | null;
  workflow_plan_delta?: WorkflowPlanDelta | null;
  iteration_rerun_plan?: IterationRerunPlan | null;
  llm_workflow_refinement?: LLMWorkflowRefinementResult | null;
  workflow_refinement_validation_result?: WorkflowRefinementValidationResult | null;
  artifact_manifest?: ArtifactManifest | null;
  ready_for_iteration: boolean;
  warnings: string[];
  error_message?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AdoptRevisedPlanResult {
  adopted: boolean;
  workflow_refinement_id: string;
  task_id: string;
  adopted_workflow_plan_id: string;
  recommended_rerun_from_stage?: string | null;
  rerun_stages: string[];
  reuse_artifacts: string[];
  invalidate_artifacts: string[];
  expected_improvement_targets: string[];
  reasoning: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}
