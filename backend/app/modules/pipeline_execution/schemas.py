from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ---- Request schemas ----

class PipelineExecutionCreateRequest(BaseModel):
    force_rerun: bool = False
    pipeline_generation_id: Optional[str] = None
    execution_mode: str = "sequential"
    max_trials_override: Optional[int] = None
    max_runtime_seconds: Optional[int] = None
    fail_fast: bool = False
    save_trained_models: bool = True
    save_predictions: bool = True
    notes: Optional[str] = None


# ---- Internal DTOs ----

class FoldResultDTO(BaseModel):
    fold_index: int
    train_size: int
    validation_size: int
    status: str = "completed"
    prediction_artifact_path: Optional[str] = None
    model_artifact_path: Optional[str] = None
    raw_metric_values: dict = {}
    duration_seconds: float = 0.0
    error_message: Optional[str] = None


class TrialResultDTO(BaseModel):
    trial_id: str
    pipeline_spec_id: str
    pipeline_run_id: str
    model_id: str
    trial_index: int
    trial_type: str
    params: dict = {}
    status: str = "pending"
    fold_results: List[FoldResultDTO] = []
    prediction_artifact_paths: List[str] = []
    model_artifact_paths: List[str] = []
    raw_metric_values: dict = {}
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    error_message: Optional[str] = None


class PipelineRunResultDTO(BaseModel):
    pipeline_run_id: str
    pipeline_spec_id: str
    pipeline_role: str
    model_id: str
    model_family: Optional[str] = None
    status: str = "pending"
    hpo_enabled: bool = False
    n_trials_planned: int = 0
    n_trials_completed: int = 0
    n_trials_failed: int = 0
    best_trial_id: Optional[str] = None
    model_artifact_paths: List[str] = []
    prediction_artifact_paths: List[str] = []
    duration_seconds: float = 0.0
    warnings: List[str] = []
    error_message: Optional[str] = None


class MetricEvaluationInputDTO(BaseModel):
    pipeline_execution_id: str
    pipeline_generation_id: str
    task_id: str
    task_type: Optional[str] = None
    target_column: Optional[str] = None
    primary_metric: Optional[str] = None
    metric_direction: str = "minimize"
    evaluation_plan: dict = {}
    validation_plan: dict = {}
    trial_results: List[dict] = []
    prediction_artifacts: List[str] = []
    model_artifacts: List[str] = []
    ready_for_metric_evaluation: bool = False


class TrainingArtifactManifestDTO(BaseModel):
    pipeline_execution_id: str
    training_artifact_dir: str
    manifest_path: Optional[str] = None
    execution_result_path: Optional[str] = None
    trial_results_path: Optional[str] = None
    prediction_paths: List[str] = []
    model_paths: List[str] = []
    log_path: Optional[str] = None
    split_metadata_path: Optional[str] = None
    metric_evaluation_input_path: Optional[str] = None


class ExecutionSummaryDTO(BaseModel):
    pipeline_execution_id: str
    task_id: str
    pipeline_generation_id: str
    status: str
    execution_mode: str
    n_pipeline_specs: int = 0
    n_trials_planned: int = 0
    n_trials_completed: int = 0
    n_trials_failed: int = 0
    n_models_trained: int = 0
    duration_seconds: float = 0.0
    ready_for_metric_evaluation: bool = False


class RuntimeEnvironmentDTO(BaseModel):
    python_version: Optional[str] = None
    platform: Optional[str] = None
    scikit_learn_version: Optional[str] = None
    pandas_version: Optional[str] = None
    numpy_version: Optional[str] = None
    joblib_version: Optional[str] = None


# ---- Response schemas ----

class PipelineExecutionResponse(BaseModel):
    pipeline_execution_id: Optional[str] = None
    task_id: Optional[str] = None
    pipeline_generation_id: Optional[str] = None
    status: str = "pending"
    execution_mode: str = "sequential"
    n_pipeline_specs: int = 0
    n_trials_planned: int = 0
    n_trials_completed: int = 0
    n_trials_failed: int = 0
    n_models_trained: int = 0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    execution_summary: Optional[ExecutionSummaryDTO] = None
    pipeline_run_results: List[PipelineRunResultDTO] = []
    trial_results: List[TrialResultDTO] = []
    training_artifact_manifest: Optional[TrainingArtifactManifestDTO] = None
    runtime_environment: Optional[RuntimeEnvironmentDTO] = None
    metric_evaluation_input: Optional[MetricEvaluationInputDTO] = None
    ready_for_metric_evaluation: bool = False
    warnings: List[str] = []
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PipelineExecutionSummaryResponse(BaseModel):
    pipeline_execution_id: str
    task_id: str
    status: str
    n_pipeline_specs: int = 0
    n_trials_planned: int = 0
    n_trials_completed: int = 0
    n_trials_failed: int = 0
    n_models_trained: int = 0
    ready_for_metric_evaluation: bool = False
    duration_seconds: float = 0.0
    warnings: List[str] = []
    created_at: Optional[datetime] = None


class LogsResponse(BaseModel):
    pipeline_execution_id: str
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    event_log: List[dict] = []
    error_message: Optional[str] = None
    warnings: List[str] = []
