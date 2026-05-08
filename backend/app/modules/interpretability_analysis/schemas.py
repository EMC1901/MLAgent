from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel


# ---- Request schemas ----

class InterpretabilityAnalysisCreateRequest(BaseModel):
    final_pipeline_selection_id: Optional[str] = None
    force_rerun: bool = False
    use_llm_summarizer: bool = True
    interpretability_profile: str = "standard"
    max_shap_samples: int = 200
    max_local_explanations: int = 10
    include_high_error_samples: bool = True
    include_permutation_importance: bool = True
    include_shap: bool = True
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
    final_pipeline_selection_id: Optional[str] = None
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


# ---- Response schema ----

class InterpretabilityAnalysisResponse(BaseModel):
    interpretability_analysis_id: Optional[str] = None
    task_id: Optional[str] = None
    final_pipeline_selection_id: Optional[str] = None
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
    analysis_artifact_manifest: Optional[Dict[str, Any]] = None
    final_output_input: Optional[Dict[str, Any]] = None
    ready_for_final_output: bool = False
    warnings: List[str] = []
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
