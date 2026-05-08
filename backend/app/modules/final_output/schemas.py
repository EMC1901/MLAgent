from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel


# ---- Request schema ----

class FinalOutputCreateRequest(BaseModel):
    interpretability_analysis_id: Optional[str] = None
    force_rerun: bool = False
    use_llm_report_writer: bool = True
    report_profile: str = "standard"
    output_format: List[str] = ["json", "markdown"]
    include_model_artifact: bool = True
    include_prediction_artifact: bool = True
    include_workflow_trace: bool = True
    include_interpretability_artifacts: bool = True
    include_reproducibility_summary: bool = True
    notes: Optional[str] = None


# ---- Internal DTOs ----

class FinalModelSummary(BaseModel):
    final_model_id: str = ""
    final_model_family: str = ""
    final_trial_id: str = ""
    final_pipeline_spec_id: str = ""
    final_hyperparameters: Dict[str, Any] = {}
    model_artifact_path: str = ""
    selection_reason_summary: str = ""


class FinalMetricSummary(BaseModel):
    primary_metric: str = ""
    primary_metric_value: Optional[float] = None
    metric_direction: str = "minimize"
    secondary_metrics: Dict[str, Any] = {}
    baseline_comparison: Dict[str, Any] = {}
    model_ranking_position: Optional[int] = None
    stability_summary: Dict[str, Any] = {}


class FinalSelectionSummary(BaseModel):
    final_pipeline_selection_id: str = ""
    selection_profile: str = ""
    selection_score: Optional[float] = None
    system_selection_reason: Dict[str, Any] = {}
    llm_selection_explanation: Dict[str, Any] = {}
    candidate_difference_summary: List[Dict[str, Any]] = []
    risk_notes: List[str] = []


class InterpretabilitySummary(BaseModel):
    interpretability_analysis_id: str = ""
    methods_used: List[str] = []
    top_features: List[Dict[str, Any]] = []
    shap_summary: Optional[Dict[str, Any]] = None
    material_insight_summary: Optional[Dict[str, Any]] = None
    interpretability_risk_notes: List[str] = []
    artifact_paths: Dict[str, str] = {}


class WorkflowTraceSummary(BaseModel):
    task_specification_id: Optional[str] = None
    task_interpretation_id: Optional[str] = None
    dataset_profile_id: Optional[str] = None
    workflow_plan_id: Optional[str] = None
    feature_engineering_id: Optional[str] = None
    feature_preprocessing_id: Optional[str] = None
    model_search_context_id: Optional[str] = None
    model_search_plan_id: Optional[str] = None
    pipeline_generation_id: Optional[str] = None
    pipeline_execution_id: Optional[str] = None
    metric_evaluation_id: Optional[str] = None
    result_diagnosis_id: Optional[str] = None
    workflow_refinement_id: Optional[str] = None
    final_pipeline_selection_id: Optional[str] = None
    interpretability_analysis_id: Optional[str] = None
    iteration_count: int = 0
    workflow_trace_artifacts: Dict[str, Any] = {}


class ReproducibilitySummary(BaseModel):
    dataset_source: str = ""
    target_column: str = ""
    feature_columns_count: Optional[int] = None
    feature_artifact_path: str = ""
    preprocessor_artifact_path: str = ""
    model_ready_matrix_path: str = ""
    model_artifact_path: str = ""
    prediction_artifact_paths: List[str] = []
    random_state: Optional[int] = None
    validation_strategy: Dict[str, Any] = {}
    hpo_summary: Dict[str, Any] = {}
    environment_summary: Dict[str, Any] = {}
    registry_versions: Dict[str, Any] = {}
    created_at: Optional[datetime] = None


class FinalReport(BaseModel):
    title: str = "Final AutoML Report for Materials Property Prediction"
    executive_summary: str = ""
    task_overview: str = ""
    dataset_summary: str = ""
    workflow_summary: str = ""
    feature_engineering_summary: str = ""
    model_search_summary: str = ""
    final_model_summary: str = ""
    metric_summary: str = ""
    interpretability_summary: str = ""
    material_insight_summary: str = ""
    limitations_and_risks: str = ""
    reproducibility_notes: str = ""
    artifact_summary: str = ""
    next_steps: str = ""


class LLMReportOutput(BaseModel):
    executive_summary: str = ""
    task_overview: str = ""
    dataset_summary: str = ""
    workflow_summary: str = ""
    feature_engineering_summary: str = ""
    model_search_summary: str = ""
    final_model_summary: str = ""
    metric_summary: str = ""
    interpretability_summary: str = ""
    material_insight_summary: str = ""
    limitations_and_risks: str = ""
    reproducibility_notes: str = ""
    artifact_summary: str = ""
    next_steps: str = ""
    confidence_level: str = "medium"


class OutputPackageManifest(BaseModel):
    output_package_id: str = ""
    package_root_dir: str = ""
    json_report_path: str = ""
    markdown_report_path: str = ""
    model_artifact_path: str = ""
    prediction_artifact_paths: List[str] = []
    interpretability_artifact_paths: Dict[str, str] = {}
    workflow_trace_path: str = ""
    manifest_path: str = ""
    package_zip_path: Optional[str] = None
    package_status: str = "complete"


class DownloadLinks(BaseModel):
    json_report: str = ""
    markdown_report: str = ""
    manifest: str = ""
    workflow_trace: str = ""
    reproducibility_summary: str = ""
    output_package_dir: str = ""
    model_artifact_ref: str = ""
    prediction_artifact_refs: List[str] = []


class FinalArtifactManifest(BaseModel):
    final_report_json_path: str = ""
    final_report_md_path: str = ""
    model_artifact_path: str = ""
    prediction_artifact_paths: List[str] = []
    interpretability_artifact_paths: Dict[str, str] = {}
    workflow_trace_path: str = ""
    reproducibility_summary_path: str = ""
    manifest_path: str = ""
    artifact_integrity_status: str = "complete"
    missing_artifacts: List[str] = []
    warnings: List[str] = []


class LLMReportValidationResult(BaseModel):
    is_valid: bool = True
    is_safe: bool = True
    schema_valid: bool = True
    issues: List[str] = []
    warnings: List[str] = []


# ---- Response schema ----

class FinalOutputResponse(BaseModel):
    final_output_id: Optional[str] = None
    task_id: Optional[str] = None
    interpretability_analysis_id: Optional[str] = None
    final_pipeline_selection_id: Optional[str] = None
    status: str = "generating"
    report_profile: str = "standard"
    final_model_summary: Optional[Dict[str, Any]] = None
    final_metric_summary: Optional[Dict[str, Any]] = None
    final_selection_summary: Optional[Dict[str, Any]] = None
    interpretability_summary: Optional[Dict[str, Any]] = None
    workflow_trace_summary: Optional[Dict[str, Any]] = None
    reproducibility_summary: Optional[Dict[str, Any]] = None
    final_artifact_manifest: Optional[Dict[str, Any]] = None
    final_report: Optional[Dict[str, Any]] = None
    llm_report_summary: Optional[Dict[str, Any]] = None
    output_package_manifest: Optional[Dict[str, Any]] = None
    download_links: Optional[Dict[str, Any]] = None
    ready_for_delivery: bool = False
    warnings: List[str] = []
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
