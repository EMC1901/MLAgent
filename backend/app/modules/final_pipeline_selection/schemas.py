from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel


# ---- Request schemas ----

class FinalPipelineSelectionCreateRequest(BaseModel):
    workflow_refinement_id: Optional[str] = None
    force_rerun: bool = False
    selection_profile: str = "balanced"
    use_llm_explainer: bool = True
    allow_baseline_as_final: bool = True
    min_baseline_improvement_required: bool = False
    stability_weight: Optional[float] = None
    interpretability_weight: Optional[float] = None
    cost_weight: Optional[float] = None
    require_model_artifact: bool = True
    require_prediction_artifact: bool = True
    notes: Optional[str] = None


# ---- Internal DTOs ----

class FinalSelectedPipeline(BaseModel):
    final_pipeline_spec_id: Optional[str] = None
    final_model_id: Optional[str] = None
    final_model_family: Optional[str] = None
    final_trial_id: Optional[str] = None
    final_trial_type: str = "hpo"
    final_hyperparameters: Dict[str, Any] = {}
    source_metric_evaluation_id: Optional[str] = None
    source_pipeline_execution_id: Optional[str] = None
    source_pipeline_generation_id: Optional[str] = None


class CandidateSelectionItem(BaseModel):
    candidate_id: str = ""
    metric_evaluation_id: Optional[str] = None
    pipeline_execution_id: Optional[str] = None
    pipeline_generation_id: Optional[str] = None
    pipeline_spec_id: Optional[str] = None
    trial_id: Optional[str] = None
    model_id: Optional[str] = None
    model_family: Optional[str] = None
    pipeline_role: str = "candidate"
    trial_type: str = "hpo"
    hyperparameters: Dict[str, Any] = {}
    primary_metric_value: Optional[float] = None
    primary_metric_rank: Optional[int] = None
    primary_metric_score: float = 0.0
    stability_score: float = 0.5
    baseline_improvement_score: float = 0.5
    interpretability_score: float = 0.5
    cost_score: float = 0.5
    constraint_score: float = 1.0
    selection_score: float = 0.0
    selection_rank: Optional[int] = None
    candidate_status: str = "eligible"
    is_final_selected: bool = False
    rejection_reason: Optional[str] = None


class SelectionPolicy(BaseModel):
    selection_profile: str = "balanced"
    primary_metric_weight: float = 0.5
    stability_weight: float = 0.2
    baseline_improvement_weight: float = 0.15
    interpretability_weight: float = 0.1
    cost_weight: float = 0.05
    constraint_weight: float = 0.0
    require_model_artifact: bool = True
    require_prediction_artifact: bool = True
    allow_baseline_as_final: bool = True
    tie_breaker_order: List[str] = ["primary_metric", "stability", "interpretability", "cost"]


class SystemSelectionReason(BaseModel):
    main_reason: str = ""
    metric_reason: str = ""
    stability_reason: str = ""
    baseline_reason: str = ""
    interpretability_reason: str = ""
    cost_reason: str = ""
    constraint_reason: str = ""
    artifact_reason: str = ""
    tradeoff_summary: str = ""


class CandidateDifferenceSummary(BaseModel):
    candidate: str = ""
    summary: str = ""


class LLMSelectionExplanation(BaseModel):
    why_selected: str = ""
    candidate_difference_summary: List[CandidateDifferenceSummary] = []
    selection_rationale_natural_language: str = ""
    human_review_notes: List[str] = []
    risk_notes: List[str] = []
    confidence_level: str = "medium"


class FinalArtifactManifest(BaseModel):
    model_artifact_path: Optional[str] = None
    prediction_artifact_paths: List[str] = []
    preprocessor_artifact_path: Optional[str] = None
    model_ready_matrix_path: Optional[str] = None
    feature_matrix_path: Optional[str] = None
    metric_results_path: Optional[str] = None
    selection_result_path: Optional[str] = None
    workflow_trace_paths: Dict[str, str] = {}
    artifact_integrity_status: str = "complete"


class InterpretabilityAnalysisInput(BaseModel):
    final_pipeline_selection_id: Optional[str] = None
    task_id: Optional[str] = None
    task_type: Optional[str] = None
    target_column: Optional[str] = None
    final_model_id: Optional[str] = None
    final_model_family: Optional[str] = None
    final_trial_id: Optional[str] = None
    final_pipeline_spec_id: Optional[str] = None
    model_artifact_path: Optional[str] = None
    model_ready_matrix_path: Optional[str] = None
    feature_columns: List[str] = []
    prediction_artifact_paths: List[str] = []
    preprocessor_artifact_path: Optional[str] = None
    primary_metric: Optional[str] = None
    primary_metric_value: Optional[float] = None
    secondary_metrics: Dict[str, Any] = {}
    interpretability_methods_recommended: List[str] = []
    selection_reason_summary: str = ""
    ready_for_interpretability_analysis: bool = False


class ConstraintCheckResult(BaseModel):
    passed: bool = True
    hard_constraints_met: bool = True
    soft_constraints_met: bool = True
    issues: List[str] = []
    warnings: List[str] = []


class StabilitySummary(BaseModel):
    fold_std: Optional[float] = None
    fold_mean: Optional[float] = None
    n_folds: Optional[int] = None
    stability_level: str = "unknown"


class BaselineComparison(BaseModel):
    baseline_model_id: Optional[str] = None
    baseline_metric_value: Optional[float] = None
    improvement: Optional[float] = None
    improvement_pct: Optional[float] = None
    improvement_level: str = "unknown"


class ArtifactManifest(BaseModel):
    manifest_path: Optional[str] = None
    final_pipeline_selection_result_path: Optional[str] = None
    candidate_ranking_path: Optional[str] = None
    selection_policy_path: Optional[str] = None
    constraint_check_result_path: Optional[str] = None
    system_selection_reason_path: Optional[str] = None
    llm_selection_explanation_path: Optional[str] = None
    final_artifact_manifest_path: Optional[str] = None
    interpretability_analysis_input_path: Optional[str] = None


# ---- Response schema ----

class FinalPipelineSelectionResponse(BaseModel):
    final_pipeline_selection_id: Optional[str] = None
    task_id: Optional[str] = None
    workflow_refinement_id: Optional[str] = None
    metric_evaluation_id: Optional[str] = None
    pipeline_execution_id: Optional[str] = None
    pipeline_generation_id: Optional[str] = None
    status: str = "selecting"
    selection_profile: str = "balanced"
    final_pipeline_spec_id: Optional[str] = None
    final_model_id: Optional[str] = None
    final_model_family: Optional[str] = None
    final_trial_id: Optional[str] = None
    final_trial_type: Optional[str] = None
    final_hyperparameters: Dict[str, Any] = {}
    primary_metric: Optional[str] = None
    primary_metric_value: Optional[float] = None
    metric_direction: Optional[str] = None
    secondary_metrics: Dict[str, Any] = {}
    stability_summary: Optional[StabilitySummary] = None
    baseline_comparison: Optional[BaselineComparison] = None
    selection_score: Optional[float] = None
    candidate_ranking: List[CandidateSelectionItem] = []
    constraint_check_result: Optional[ConstraintCheckResult] = None
    system_selection_reason: Optional[SystemSelectionReason] = None
    llm_selection_explanation: Optional[LLMSelectionExplanation] = None
    candidate_difference_summary: List[CandidateDifferenceSummary] = []
    human_review_notes: List[str] = []
    risk_notes: List[str] = []
    llm_used: bool = False
    llm_confidence_level: Optional[str] = None
    final_artifact_manifest: Optional[FinalArtifactManifest] = None
    interpretability_analysis_input: Optional[InterpretabilityAnalysisInput] = None
    ready_for_interpretability_analysis: bool = False
    warnings: List[str] = []
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
