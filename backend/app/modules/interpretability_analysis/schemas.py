from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel


# ---- Request schemas ----

class InterpretabilityAnalysisCreateRequest(BaseModel):
    force_rerun: bool = False
    use_llm_summarizer: bool = True
    interpretability_profile: str = "standard"
    max_shap_samples: int = 200
    max_local_explanations: int = 10
    include_high_error_samples: bool = True
    include_permutation_importance: bool = True
    include_shap: bool = True
    include_pdp: bool = True
    include_correlation: bool = True
    include_residual_analysis: bool = True
    include_cross_method_consensus: bool = True
    include_physics_constraints: bool = True
    pdp_top_n_features: int = 10
    correlation_top_n_features: int = 30
    notes: Optional[str] = None


# ---- Internal DTOs ----

class GlobalFeatureImportanceItem(BaseModel):
    feature_name: str = ""
    importance_value: float = 0.0
    importance_rank: int = 0
    importance_method: str = "permutation_importance"
    direction: str = "unknown"
    feature_group: str = "other"
    interpretation_hint: str = ""


class PermutationImportanceResult(BaseModel):
    feature_name: str = ""
    importance_mean: float = 0.0
    importance_std: float = 0.0
    rank: int = 0
    n_repeats: int = 10


class TopShapFeature(BaseModel):
    feature_name: str = ""
    mean_abs_shap: float = 0.0
    rank: int = 0
    direction_summary: str = ""


class ShapArtifactPaths(BaseModel):
    shap_values: str = ""
    summary_data: str = ""


class ShapSummary(BaseModel):
    shap_available: bool = False
    explainer_type: str = ""
    n_samples_explained: int = 0
    top_shap_features: List[TopShapFeature] = []
    shap_artifact_paths: Optional[ShapArtifactPaths] = None
    warnings: List[str] = []


class LocalExplanationItem(BaseModel):
    sample_id: str = ""
    y_true: Optional[float] = None
    y_pred: Optional[float] = None
    prediction_error: Optional[float] = None
    top_positive_features: List[Dict[str, Any]] = []
    top_negative_features: List[Dict[str, Any]] = []
    local_shap_values: Dict[str, float] = {}
    local_explanation_summary: str = ""


class HighErrorSampleAnalysis(BaseModel):
    sample_id: str = ""
    absolute_error: float = 0.0
    relative_error: Optional[float] = None
    error_rank: int = 0
    possible_error_factors: List[str] = []
    feature_pattern_summary: str = ""
    review_suggestion: str = ""


class MaterialPattern(BaseModel):
    pattern: str = ""
    supporting_features: List[str] = []
    possible_material_meaning: str = ""
    evidence_strength: str = "moderate"
    caution: str = ""


class FeatureGroupInterpretation(BaseModel):
    feature_group: str = "other"
    summary: str = ""


class MaterialInsightSummary(BaseModel):
    top_material_patterns: List[MaterialPattern] = []
    feature_groups_interpretation: List[FeatureGroupInterpretation] = []
    domain_hypotheses: List[str] = []
    limitations: List[str] = []
    confidence_level: str = "medium"


class LLMInterpretabilitySummary(BaseModel):
    top_material_patterns: List[MaterialPattern] = []
    feature_groups_interpretation: List[FeatureGroupInterpretation] = []
    domain_hypotheses: List[str] = []
    limitations: List[str] = []
    human_review_notes: List[str] = []
    confidence_level: str = "medium"


class LLMValidationResult(BaseModel):
    is_valid: bool = True
    issues: List[str] = []
    warnings: List[str] = []


class FeatureGroupSummary(BaseModel):
    feature_groups: Dict[str, Dict[str, Any]] = {}
    summary_text: str = ""


class InterpretabilityMethodPlan(BaseModel):
    methods_selected: List[str] = []
    methods_skipped: List[str] = []
    methods_failed: List[str] = []
    fallbacks_used: Dict[str, str] = {}
    shap_supported: bool = False
    shap_explainer_type: str = ""
    notes: List[str] = []


class FinalOutputInput(BaseModel):
    interpretability_analysis_id: Optional[str] = None
    task_id: Optional[str] = None
    final_model_id: Optional[str] = None
    final_trial_id: Optional[str] = None
    model_artifact_path: Optional[str] = None
    prediction_artifact_paths: List[str] = []
    metric_summary: Dict[str, Any] = {}
    selection_summary: Dict[str, Any] = {}
    global_feature_importance: List[Dict[str, Any]] = []
    shap_summary: Optional[Dict[str, Any]] = None
    material_insight_summary: Optional[Dict[str, Any]] = None
    interpretability_artifacts: Dict[str, str] = {}
    workflow_trace_refs: Dict[str, str] = {}
    ready_for_final_output: bool = False


class InterpretabilityRiskNote(BaseModel):
    risk_type: str = ""
    description: str = ""
    severity: str = "low"


# ---- Phase 2: New analysis DTOs ----

class CrossMethodConsensus(BaseModel):
    """Cross-method rank correlation analysis."""
    rank_correlation_matrix: Dict[str, Dict[str, float]] = {}
    consensus_features: List[str] = []
    divergent_features: List[Dict[str, Any]] = []
    overall_agreement_score: float = 0.0


class PDP1D(BaseModel):
    """1D partial dependence for a single feature."""
    feature_name: str = ""
    grid_values: List[float] = []
    pdp_values: List[float] = []


class PDP2D(BaseModel):
    """2D partial dependence for a feature pair."""
    feature_1: str = ""
    feature_2: str = ""
    grid_1: List[float] = []
    grid_2: List[float] = []
    pdp_matrix: List[List[float]] = []


class PartialDependenceResult(BaseModel):
    """Partial dependence analysis results."""
    pdp_1d: List[PDP1D] = []
    pdp_2d: List[PDP2D] = []


class ResidualAnalysisResult(BaseModel):
    """Residual analysis with systematic error detection."""
    residuals: List[float] = []
    predicted_values: List[float] = []
    r_squared: float = 0.0
    rmse: float = 0.0
    residual_mean: float = 0.0
    residual_std: float = 0.0
    histogram_bins: List[Dict[str, Any]] = []
    systematic_error_segments: List[Dict[str, Any]] = []


class CorrelationAnalysisResult(BaseModel):
    """Feature correlation analysis."""
    feature_correlation_matrix: List[List[float]] = []
    feature_names: List[str] = []
    target_correlations: List[Dict[str, Any]] = []
    high_correlation_pairs: List[Dict[str, Any]] = []


class PhysicsConstraintCheck(BaseModel):
    """Physics constraint validation result."""
    constraints: List[Dict[str, Any]] = []
    passed: bool = True


class ArtifactManifest(BaseModel):
    manifest_path: Optional[str] = None
    interpretability_analysis_result_path: Optional[str] = None
    global_feature_importance_path: Optional[str] = None
    permutation_importance_path: Optional[str] = None
    shap_values_path: Optional[str] = None
    shap_summary_path: Optional[str] = None
    local_explanations_path: Optional[str] = None
    high_error_sample_analysis_path: Optional[str] = None
    feature_group_summary_path: Optional[str] = None
    material_insight_summary_path: Optional[str] = None
    llm_interpretability_summary_path: Optional[str] = None
    final_output_input_path: Optional[str] = None
    cross_method_consensus_path: Optional[str] = None
    partial_dependence_path: Optional[str] = None
    residual_analysis_path: Optional[str] = None
    correlation_analysis_path: Optional[str] = None
    physics_constraint_check_path: Optional[str] = None


class InterpretabilityAnalysisInput(BaseModel):
    """Input data for interpretability analysis, gathered from upstream modules."""
    # Model artifacts
    model_artifact_path: Optional[str] = None
    model_ready_matrix_path: Optional[str] = None
    prediction_artifact_paths: List[str] = []
    preprocessor_artifact_path: Optional[str] = None

    # Task context
    task_id: Optional[str] = None
    task_type: Optional[str] = None
    target_column: Optional[str] = None
    primary_metric: Optional[str] = None
    primary_metric_value: Optional[float] = None
    metric_direction: Optional[str] = None

    # Model info
    final_model_id: Optional[str] = None
    final_model_family: Optional[str] = None
    final_trial_id: Optional[str] = None

    # Feature info
    feature_columns: List[str] = []
    feature_lineage: Dict[str, Any] = {}

    # Domain context (for LLM)
    material_domain: Optional[str] = None
    dataset_description: Optional[str] = None
    prediction_target_name: Optional[str] = None
    stop_rationale: Optional[Dict[str, Any]] = None

    # Upstream references
    metric_evaluation_id: Optional[str] = None
    pipeline_execution_id: Optional[str] = None
    pipeline_generation_id: Optional[str] = None

    # Selection context
    selection_reason_summary: Optional[str] = None
    model_ranking: List[Dict[str, Any]] = []
    metric_summary: Optional[Dict[str, Any]] = None


# ---- Response schema ----

class InterpretabilityAnalysisResponse(BaseModel):
    interpretability_analysis_id: Optional[str] = None
    task_id: Optional[str] = None
    metric_evaluation_id: Optional[str] = None
    pipeline_execution_id: Optional[str] = None
    status: str = "analyzing"
    analysis_profile: str = "standard"
    final_model_id: Optional[str] = None
    final_model_family: Optional[str] = None
    final_trial_id: Optional[str] = None
    interpretability_methods_used: List[str] = []
    global_feature_importance: List[Dict[str, Any]] = []
    permutation_importance: List[Dict[str, Any]] = []
    shap_summary: Optional[Dict[str, Any]] = None
    local_explanations: List[Dict[str, Any]] = []
    high_error_sample_analysis: List[Dict[str, Any]] = []
    feature_group_summary: Optional[Dict[str, Any]] = None
    material_insight_summary: Optional[Dict[str, Any]] = None
    llm_interpretability_summary: Optional[Dict[str, Any]] = None
    interpretability_risk_notes: List[Dict[str, Any]] = []
    cross_method_consensus: Optional[Dict[str, Any]] = None
    partial_dependence: Optional[Dict[str, Any]] = None
    residual_analysis: Optional[Dict[str, Any]] = None
    correlation_analysis: Optional[Dict[str, Any]] = None
    physics_constraint_check: Optional[Dict[str, Any]] = None
    analysis_artifact_manifest: Optional[Dict[str, Any]] = None
    final_output_input: Optional[Dict[str, Any]] = None
    ready_for_final_output: bool = False
    warnings: List[str] = []
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
