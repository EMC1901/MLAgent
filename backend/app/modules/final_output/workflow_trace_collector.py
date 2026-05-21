import logging
from typing import Optional, Dict, Any
from sqlmodel import Session

from app.modules.final_output.schemas import WorkflowTraceSummary
from app.modules.final_output.exceptions import WorkflowTraceCollectException

logger = logging.getLogger(__name__)


def collect_workflow_trace(
    session: Session,
    task_id: str,
    task_spec_id: Optional[str] = None,
    task_interp_id: Optional[str] = None,
    dataset_profile_id: Optional[str] = None,
    workflow_plan_id: Optional[str] = None,
    feature_engineering_id: Optional[str] = None,
    feature_preprocessing_id: Optional[str] = None,
    model_search_context_id: Optional[str] = None,
    pipeline_generation_id: Optional[str] = None,
    pipeline_execution_id: Optional[str] = None,
    metric_evaluation_id: Optional[str] = None,
    result_diagnosis_id: Optional[str] = None,
    workflow_refinement_id: Optional[str] = None,
    final_pipeline_selection_id: Optional[str] = None,
    interpretability_analysis_id: Optional[str] = None,
) -> WorkflowTraceSummary:
    trace = WorkflowTraceSummary(
        task_specification_id=task_spec_id,
        task_interpretation_id=task_interp_id,
        dataset_profile_id=dataset_profile_id,
        workflow_plan_id=workflow_plan_id,
        feature_engineering_id=feature_engineering_id,
        feature_preprocessing_id=feature_preprocessing_id,
        model_search_context_id=model_search_context_id,
        pipeline_generation_id=pipeline_generation_id,
        pipeline_execution_id=pipeline_execution_id,
        metric_evaluation_id=metric_evaluation_id,
        result_diagnosis_id=result_diagnosis_id,
        workflow_refinement_id=workflow_refinement_id,
        final_pipeline_selection_id=final_pipeline_selection_id,
        interpretability_analysis_id=interpretability_analysis_id,
        iteration_count=0,
        workflow_trace_artifacts={},
    )

    try:
        _collect_module_summaries(session, trace, task_id)
        _collect_iteration_info(session, trace, task_id)
    except Exception as e:
        logger.warning("Partial workflow trace collection: %s", str(e))

    logger.info("Collected workflow trace for task %s: %d modules", task_id, 15)
    return trace


def _collect_module_summaries(session: Session, trace: WorkflowTraceSummary, task_id: str):
    summaries: Dict[str, Any] = {}

    # Task Specification
    if trace.task_specification_id:
        _safe_collect(
            session, summaries, "task_specification",
            "app.modules.task_specification.model", "TaskSpecification",
            trace.task_specification_id,
        )

    # Task Interpretation
    if trace.task_interpretation_id:
        _safe_collect(
            session, summaries, "task_interpretation",
            "app.modules.task_interpretation.model", "TaskInterpretation",
            trace.task_interpretation_id,
        )

    # Dataset Profile
    if trace.dataset_profile_id:
        _safe_collect(
            session, summaries, "dataset_profile",
            "app.modules.dataset_profile.model", "DatasetProfile",
            trace.dataset_profile_id,
        )

    # Workflow Plan
    if trace.workflow_plan_id:
        _safe_collect(
            session, summaries, "workflow_plan",
            "app.modules.workflow_planning.model", "WorkflowPlan",
            trace.workflow_plan_id,
        )

    # Feature Engineering
    if trace.feature_engineering_id:
        _safe_collect(
            session, summaries, "feature_engineering",
            "app.modules.feature_engineering.model", "FeatureEngineering",
            trace.feature_engineering_id,
        )

    # Feature Preprocessing
    if trace.feature_preprocessing_id:
        _safe_collect(
            session, summaries, "feature_preprocessing",
            "app.modules.feature_preprocessing.model", "FeaturePreprocessing",
            trace.feature_preprocessing_id,
        )

    # Model Search Context
    if trace.model_search_context_id:
        _safe_collect(
            session, summaries, "model_search_context",
            "app.modules.model_search_context.model", "ModelSearchContext",
            trace.model_search_context_id,
        )

    # Pipeline Generation
    if trace.pipeline_generation_id:
        _safe_collect(
            session, summaries, "pipeline_generation",
            "app.modules.pipeline_generation.model", "PipelineGeneration",
            trace.pipeline_generation_id,
        )

    # Pipeline Execution
    if trace.pipeline_execution_id:
        _safe_collect(
            session, summaries, "pipeline_execution",
            "app.modules.pipeline_execution.model", "PipelineExecution",
            trace.pipeline_execution_id,
        )

    # Metric Evaluation
    if trace.metric_evaluation_id:
        _safe_collect(
            session, summaries, "metric_evaluation",
            "app.modules.metric_evaluation.model", "MetricEvaluation",
            trace.metric_evaluation_id,
        )

    # Result Diagnosis
    if trace.result_diagnosis_id:
        _safe_collect(
            session, summaries, "result_diagnosis",
            "app.modules.result_diagnosis.model", "ResultDiagnosis",
            trace.result_diagnosis_id,
        )

    # Workflow Refinement
    if trace.workflow_refinement_id:
        _safe_collect(
            session, summaries, "workflow_refinement",
            "app.modules.workflow_refinement.model", "WorkflowRefinement",
            trace.workflow_refinement_id,
        )

    # Final Pipeline Selection
    if trace.final_pipeline_selection_id:
        _safe_collect(
            session, summaries, "final_pipeline_selection",
            "app.modules.final_pipeline_selection.model", "FinalPipelineSelection",
            trace.final_pipeline_selection_id,
        )

    # Interpretability Analysis
    if trace.interpretability_analysis_id:
        _safe_collect(
            session, summaries, "interpretability_analysis",
            "app.modules.interpretability_analysis.model", "InterpretabilityAnalysis",
            trace.interpretability_analysis_id,
        )

    trace.workflow_trace_artifacts = summaries


def _safe_collect(session: Session, summaries: dict, key: str, module_path: str, model_name: str, record_id: str):
    try:
        import importlib
        module = importlib.import_module(module_path)
        model_cls = getattr(module, model_name)
        record = session.get(model_cls, record_id)
        if record:
            summary = {"id": record_id, "status": getattr(record, "status", None)}
            if hasattr(record, "created_at"):
                summary["created_at"] = str(record.created_at) if record.created_at else None
            summaries[key] = summary
    except Exception as e:
        logger.warning("Failed to collect summary for %s/%s: %s", key, record_id, str(e))
        summaries[key] = {"id": record_id, "status": "unknown", "error": str(e)}


def _collect_iteration_info(session: Session, trace: WorkflowTraceSummary, task_id: str):
    try:
        from app.modules.workflow_refinement.model import WorkflowRefinement
        from app.modules.workflow_refinement.repository import WorkflowRefinementRepository
        wf_repo = WorkflowRefinementRepository()
        refinements = wf_repo.list_by_task_id(session, task_id)
        if refinements:
            refined = [r for r in refinements if r.decision == "refine"]
            trace.iteration_count = len(refined)
            if refined:
                trace.workflow_trace_artifacts["refinement_history"] = [
                    {"id": r.id, "decision": r.decision, "created_at": str(r.created_at)}
                    for r in refinements
                ]
    except Exception as e:
        logger.warning("Failed to collect iteration info: %s", str(e))
