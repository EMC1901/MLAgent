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
    academic_insights: List[Dict[str, Any]] = []
    rejected_claims: List[Dict[str, Any]] = []
    missing_evidence: List[Dict[str, Any]] = []
    feature_groups_interpretation: List[FeatureGroupInterpretation] = []
    domain_hypotheses: List[str] = []
    limitations: List[str] = []
    human_review_notes: List[str] = []
    confidence_level: str = "medium"
    mechanism_candidates: List[Dict[str, Any]] = []


class LLMInterpretabilitySummary(BaseModel):
    top_material_patterns: List[MaterialPattern] = []
    academic_insights: List[Dict[str, Any]] = []
    rejected_claims: List[Dict[str, Any]] = []
    missing_evidence: List[Dict[str, Any]] = []
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
    scientific_insight_summary: Optional[Dict[str, Any]] = None
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
    scientific_insight_report_path: Optional[str] = None
    material_patterns_path: Optional[str] = None
    material_pattern_validation_path: Optional[str] = None
    material_mechanisms_path: Optional[str] = None


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


# ---- Evidence Layer DTOs ----

class EvidenceUnit(BaseModel):
    """Single piece of evidence from one analysis method about one or more features."""
    evidence_id: str = ""
    evidence_type: str = ""  # shap_importance, permutation_importance, coefficient_importance, native_importance, pdp_1d, correlation_linear, correlation_rank, residual_segment, physics_constraint, error_concentration, shap_interaction
    feature_names: List[str] = []
    quantitative_summary: Dict[str, Any] = {}
    direction: str = "unknown"  # positive, negative, non_monotonic, flat, unknown
    strength: float = 0.0
    reliability: float = 0.0
    limitations: List[str] = []
    method_name: str = ""


class FeatureEvidenceProfile(BaseModel):
    """Unified evidence profile for a single feature across all methods."""
    feature_name: str = ""
    rank_percentile: float = 0.0
    z_score: float = 0.0
    top_k_membership: Dict[str, bool] = {}
    consensus_score: float = 0.0
    direction_consistency: float = 0.0
    method_agreement: Dict[str, float] = {}
    stability_score: float = 0.0
    redundancy_risk: float = 0.0
    physical_interpretability_score: float = 0.0
    evidence_units: List[EvidenceUnit] = []


class ConfidenceBreakdown(BaseModel):
    """Transparent confidence score breakdown."""
    cross_method_agreement: float = 0.0
    model_performance_reliability: float = 0.0
    sample_support: float = 0.0
    pdp_shap_direction_consistency: float = 0.0
    correlation_support: float = 0.0
    physics_consistency: float = 0.0
    contradiction_penalty: float = 0.0
    total_confidence: float = 0.0
    confidence_label: str = "medium"


# ---- Hypothesis Layer DTOs ----

class ScientificHypothesis(BaseModel):
    """Rule-driven hypothesis with evidence grounding."""
    hypothesis_id: str = ""
    claim: str = ""
    claim_type: str = ""  # association, mechanism_hypothesis, limitation, anomaly
    supporting_evidence_ids: List[str] = []
    contradicting_evidence_ids: List[str] = []
    confidence_score: float = 0.0
    confidence_breakdown: Optional[ConfidenceBreakdown] = None
    confidence_label: str = "medium"
    scope_conditions: List[str] = []
    validation_suggestions: List[str] = []
    hypothesis_pattern: str = ""


class ModelApplicabilityBoundary(BaseModel):
    """Describes regions where the model is reliable vs. unreliable."""
    boundary_id: str = ""
    description: str = ""
    feature_conditions: Dict[str, Any] = {}
    error_ratio: float = 0.0
    supporting_evidence_ids: List[str] = []
    severity: str = "warning"  # info, warning, critical


class AnomalyPattern(BaseModel):
    """Counterexample or anomaly pattern from high-error samples."""
    pattern_id: str = ""
    description: str = ""
    sample_count: int = 0
    feature_signature: Dict[str, Any] = {}
    supporting_evidence_ids: List[str] = []


# ---- Phase 1: Material Pattern Mining DTOs ----

class PatternCondition(BaseModel):
    """A single condition describing when a material pattern holds."""
    feature_name: str = ""
    material_concept: str = ""
    operator: str = ""          # low, high, between, outside, increasing, decreasing
    value_range: Dict[str, Any] = {}
    quantile_range: Optional[List[float]] = None
    source: str = ""            # pdp, shap_dependence, subgroup_contrast, interaction


class PatternEffect(BaseModel):
    """The predicted effect of a material pattern on the target property."""
    target_direction: str = ""  # increases, decreases, peaks, drops, uncertain
    effect_size: float = 0.0
    effect_unit: str = ""
    evidence_basis: str = ""    # predicted_target, observed_target, pdp_delta


class PatternCounterexample(BaseModel):
    """Counterexample evidence that contradicts or limits a pattern."""
    description: str = ""
    sample_count: int = 0
    feature_signature: Dict[str, Any] = {}
    supporting_evidence_ids: List[str] = []


# ---- Phase 3: Pattern Validation & Ranking DTOs ----

class PatternSampleSupport(BaseModel):
    """Sample-level support statistics for a material pattern."""
    in_scope_count: int = 0
    out_scope_count: int = 0
    coverage: float = 0.0
    in_scope_fraction: float = 0.0
    feature_bounds: Dict[str, Any] = {}


class PatternValidationResult(BaseModel):
    """Result of a single validation check on a material pattern."""
    validation_id: str = ""
    pattern_id: str = ""
    validation_type: str = ""  # subgroup_contrast, bootstrap, ice_consistency, boundary_error_check
    status: str = ""           # pass, weak, fail, not_applicable
    metrics: Dict[str, Any] = {}
    interpretation: str = ""
    limitations: List[str] = []
    supporting_evidence_ids: List[str] = []


class PatternScientificScore(BaseModel):
    """Multi-factor scientific quality score for a material pattern."""
    validation_support: float = 0.0
    robustness: float = 0.0
    effect_size: float = 0.0
    sample_support: float = 0.0
    physical_interpretability: float = 0.0
    actionability: float = 0.0
    counterexample_penalty: float = 0.0
    total: float = 0.0
    rank_reason: str = ""


class MaterialPatternCandidate(BaseModel):
    """Deterministically mined material pattern candidate.

    This is the Phase 1 core artifact 鈥?a structured, evidence-grounded
    candidate material design rule, not an importance summary.
    """
    pattern_id: str = ""
    pattern_type: str = ""      # monotonic, threshold, window, interaction, subgroup, boundary
    statement: str = ""
    material_concepts: List[str] = []
    conditions: List[PatternCondition] = []
    predicted_effect: PatternEffect = PatternEffect()
    supporting_evidence_ids: List[str] = []
    contradicting_evidence_ids: List[str] = []
    counterexamples: List[PatternCounterexample] = []
    scope_conditions: List[str] = []
    validation_suggestions: List[str] = []
    confidence_score: float = 0.0
    confidence_label: str = "medium"
    limitations: List[str] = []
    # Phase 3: Validation & ranking
    sample_support: Optional[PatternSampleSupport] = None
    validation_results: List[PatternValidationResult] = []
    validation_status: str = "unvalidated"
    scientific_score: Optional[PatternScientificScore] = None
    display_priority: int = 999


# ---- Phase 4: Material Mechanism DTOs ----

class MaterialMechanismCandidate(BaseModel):
    """Material-domain mechanism candidate synthesized from validated patterns.

    Bridges the gap between 'descriptor pattern' and 'scientific mechanism'
    by grounding patterns in material science concepts, causal chains,
    applicable material families, and experimental validation paths.
    """
    mechanism_id: str = ""
    source_pattern_ids: List[str] = []
    mechanism_family: str = ""
    # e.g. electronic_structure, lattice_distortion, bonding_strength,
    # composition_complexity, thermodynamic_stability, processing_structure

    mechanism_statement: str = ""
    material_variables: List[str] = []
    descriptor_variables: List[str] = []
    causal_chain: List[str] = []

    applicable_material_scope: List[str] = []
    excluded_or_weak_scope: List[str] = []

    supporting_evidence_ids: List[str] = []
    supporting_pattern_validation: List[Dict[str, Any]] = []
    counterexamples: List[Dict[str, Any]] = []

    confidence_score: float = 0.0
    confidence_label: str = "medium"
    grounding_level: str = "descriptor_grounded"
    # descriptor_grounded, lineage_grounded, physics_prior_grounded, externally_validated

    limitations: List[str] = []
    validation_suggestions: List[str] = []


class ScientificInsightReport(BaseModel):
    """Structured report generated before LLM narrative."""
    executive_insights: List[ScientificHypothesis] = []
    ranked_hypotheses: List[ScientificHypothesis] = []
    mechanism_candidates: List[ScientificHypothesis] = []
    model_applicability_boundaries: List[ModelApplicabilityBoundary] = []
    anomaly_or_counterexample_patterns: List[AnomalyPattern] = []
    material_pattern_candidates: List[MaterialPatternCandidate] = []
    material_mechanism_candidates: List[MaterialMechanismCandidate] = []
    physics_consistency_summary: Dict[str, Any] = {}
    evidence_graph: Dict[str, Any] = {}
    limitations: List[str] = []
    feature_profiles: List[FeatureEvidenceProfile] = []


class LLMNarrativeOutput(BaseModel):
    """Structured LLM output referencing evidence IDs."""
    narrative_title: str = ""
    executive_summary: str = ""
    insights: List[Dict[str, Any]] = []
    limitations_section: List[Dict[str, Any]] = []
    validation_suggestions: List[Dict[str, Any]] = []


class LLMScientificInsightOutput(BaseModel):
    """Evidence-grounded academic insight output from the LLM."""
    narrative_title: str = ""
    executive_summary: str = ""
    academic_insights: List[Dict[str, Any]] = []
    rejected_claims: List[Dict[str, Any]] = []
    missing_evidence: List[Dict[str, Any]] = []
    human_review_notes: List[str] = []
    limitations_section: List[Dict[str, Any]] = []
    validation_suggestions: List[Dict[str, Any]] = []


# ---- Debug & Observability DTOs ----

class DebugWarning(BaseModel):
    """Structured warning with step, code, severity, and message."""
    step: str = ""
    code: str = ""
    severity: str = "warning"  # warning | error
    message: str = ""


class DebugTraceStep(BaseModel):
    """A single step in the debug trace timeline."""
    step: str = ""
    step_name: str = ""
    status: str = "pending"  # pending | running | completed | failed
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    input_summary: Optional[Dict[str, Any]] = None
    output_summary: Optional[Dict[str, Any]] = None
    warnings: List[DebugWarning] = []
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    recoverable: bool = True


class DebugTrace(BaseModel):
    """Full debug trace for an interpretability analysis run."""
    run_id: str = ""
    steps: List[DebugTraceStep] = []
    environment: Dict[str, Any] = {}
    cache_hit: bool = False
    cached_from_ia_id: Optional[str] = None
    total_duration_seconds: Optional[float] = None


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
    scientific_insight_report: Optional[Dict[str, Any]] = None
    final_output_input: Optional[Dict[str, Any]] = None
    ready_for_final_output: bool = False
    warnings: List[str] = []
    debug_warnings: List[DebugWarning] = []
    debug_trace: Optional[DebugTrace] = None
    current_step: Optional[str] = None
    last_completed_step: Optional[str] = None
    duration_seconds: Optional[float] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

