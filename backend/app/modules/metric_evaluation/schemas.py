from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


# ---- Request schemas ----

class MetricEvaluationCreateRequest(BaseModel):
    force_rerun: bool = False
    pipeline_execution_id: Optional[str] = None
    include_fold_metrics: bool = True
    include_baseline_comparison: bool = True
    include_ranking_details: bool = True
    metric_profile: str = "standard"
    notes: Optional[str] = None


# ---- Internal DTOs ----

class FoldMetricResult(BaseModel):
    fold_metric_id: str
    trial_id: str
    pipeline_spec_id: str
    model_id: str
    fold_index: int
    n_samples: int
    metrics: Dict[str, float] = {}
    primary_metric_value: Optional[float] = None
    prediction_artifact_path: Optional[str] = None
    status: str = "evaluated"
    warnings: List[str] = []
    error_message: Optional[str] = None


class TrialMetricResult(BaseModel):
    trial_id: str
    pipeline_spec_id: str
    pipeline_run_id: str
    model_id: str
    model_family: Optional[str] = None
    pipeline_role: Optional[str] = None
    trial_type: Optional[str] = None
    params: Dict[str, Any] = {}
    n_folds: int = 0
    fold_metrics: List[FoldMetricResult] = []
    aggregated_metrics: Dict[str, float] = {}
    primary_metric_mean: Optional[float] = None
    primary_metric_std: Optional[float] = None
    primary_metric_min: Optional[float] = None
    primary_metric_max: Optional[float] = None
    rank: Optional[int] = None
    is_best_trial: bool = False
    status: str = "evaluated"
    warnings: List[str] = []


class PipelineMetricResult(BaseModel):
    pipeline_spec_id: str
    pipeline_run_id: str
    model_id: str
    model_family: Optional[str] = None
    pipeline_role: Optional[str] = None
    n_trials_evaluated: int = 0
    best_trial_id: Optional[str] = None
    best_primary_metric_value: Optional[float] = None
    mean_primary_metric_value: Optional[float] = None
    std_primary_metric_value: Optional[float] = None
    best_trial_params: Dict[str, Any] = {}
    rank: Optional[int] = None
    is_best_model: bool = False
    warnings: List[str] = []


class ModelRankingItem(BaseModel):
    rank: int
    model_id: str
    model_family: Optional[str] = None
    pipeline_spec_id: str
    best_trial_id: Optional[str] = None
    primary_metric: Optional[str] = None
    primary_metric_value: Optional[float] = None
    metric_direction: str = "minimize"
    improvement_over_best_baseline: Optional[float] = None
    improvement_percentage: Optional[float] = None
    stability_score: Optional[float] = None
    ranking_reason: str = ""


class BaselineComparison(BaseModel):
    baseline_available: bool = False
    best_baseline_model_id: Optional[str] = None
    best_baseline_trial_id: Optional[str] = None
    best_baseline_metric_value: Optional[float] = None
    best_candidate_model_id: Optional[str] = None
    best_candidate_trial_id: Optional[str] = None
    best_candidate_metric_value: Optional[float] = None
    absolute_improvement: Optional[float] = None
    relative_improvement_percentage: Optional[float] = None
    candidate_beats_baseline: bool = False
    comparison_notes: List[str] = []


class MetricValidationResult(BaseModel):
    is_valid: bool = True
    all_metrics_finite: bool = True
    primary_metric_present: bool = True
    ranking_consistent: bool = True
    best_trial_in_results: bool = True
    baseline_references_valid: bool = True
    diagnosis_input_complete: bool = True
    issues: List[str] = []


class EvaluationArtifactManifest(BaseModel):
    metric_evaluation_id: str
    pipeline_execution_id: str
    artifact_dir: str
    manifest_path: Optional[str] = None
    metric_results_path: Optional[str] = None
    fold_metrics_path: Optional[str] = None
    trial_metrics_path: Optional[str] = None
    pipeline_metrics_path: Optional[str] = None
    model_ranking_path: Optional[str] = None
    baseline_comparison_path: Optional[str] = None
    result_diagnosis_input_path: Optional[str] = None


class MetricSummary(BaseModel):
    primary_metric: Optional[str] = None
    metric_direction: str = "minimize"
    best_metric_value: Optional[float] = None
    worst_metric_value: Optional[float] = None
    mean_metric_value: Optional[float] = None
    std_metric_value: Optional[float] = None
    n_trials_contributing: int = 0
    n_models_contributing: int = 0


class ResultDiagnosisInput(BaseModel):
    metric_evaluation_id: str
    pipeline_execution_id: str
    task_id: str
    task_type: Optional[str] = None
    primary_metric: Optional[str] = None
    metric_direction: str = "minimize"
    best_trial: Optional[Dict[str, Any]] = None
    best_model: Optional[Dict[str, Any]] = None
    model_ranking: List[ModelRankingItem] = []
    baseline_comparison: Optional[BaselineComparison] = None
    metric_summary: Optional[MetricSummary] = None
    failed_trials_summary: Dict[str, Any] = {}
    stability_summary: Dict[str, Any] = {}
    evaluation_warnings: List[str] = []
    ready_for_result_diagnosis: bool = False


class FinalHoldoutEvaluation(BaseModel):
    available: bool = False
    split: str = "test"
    prediction_artifact_path: Optional[str] = None
    model_id: Optional[str] = None
    trial_id: Optional[str] = None
    n_test_samples: int = 0
    r2_test: Optional[float] = None
    rmse_test: Optional[float] = None
    mae_test: Optional[float] = None
    notes: List[str] = []

# ---- Response schemas ----

class MetricEvaluationResponse(BaseModel):
    metric_evaluation_id: Optional[str] = None
    task_id: Optional[str] = None
    pipeline_execution_id: Optional[str] = None
    pipeline_generation_id: Optional[str] = None
    status: str = "pending"
    task_type: Optional[str] = None
    primary_metric: Optional[str] = None
    metric_direction: str = "minimize"
    n_trials_evaluated: int = 0
    n_trials_failed: int = 0
    n_models_evaluated: int = 0
    best_trial_id: Optional[str] = None
    best_model_id: Optional[str] = None
    best_pipeline_spec_id: Optional[str] = None
    metric_summary: Optional[MetricSummary] = None
    final_holdout_evaluation: Optional[FinalHoldoutEvaluation] = None
    trial_metric_results: List[TrialMetricResult] = []
    pipeline_metric_results: List[PipelineMetricResult] = []
    fold_metric_results: List[FoldMetricResult] = []
    model_ranking: List[ModelRankingItem] = []
    baseline_comparison: Optional[BaselineComparison] = None
    metric_validation_result: Optional[MetricValidationResult] = None
    evaluation_artifact_manifest: Optional[EvaluationArtifactManifest] = None
    result_diagnosis_input: Optional[ResultDiagnosisInput] = None
    ready_for_result_diagnosis: bool = False
    warnings: List[str] = []
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MetricEvaluationSummaryResponse(BaseModel):
    metric_evaluation_id: str
    task_id: str
    status: str
    primary_metric: Optional[str] = None
    best_model_id: Optional[str] = None
    best_trial_id: Optional[str] = None
    best_metric_value: Optional[float] = None
    baseline_improvement: Optional[float] = None
    ready_for_result_diagnosis: bool = False
    created_at: Optional[datetime] = None
