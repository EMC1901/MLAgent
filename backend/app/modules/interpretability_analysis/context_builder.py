import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from sqlmodel import Session

from app.modules.metric_evaluation.model import MetricEvaluation
from app.modules.pipeline_execution.model import PipelineExecution
from app.modules.pipeline_generation.model import PipelineGeneration
from app.modules.feature_preprocessing.model import FeaturePreprocessing
from app.modules.iteration_decision.model import IterationDecision
from app.modules.task_interpretation.model import TaskInterpretation
from app.modules.task_specification.model import TaskSpecification

from app.modules.interpretability_analysis.exceptions import (
    InterpretabilityInputInvalidException,
)

logger = logging.getLogger(__name__)


@dataclass
class InterpretabilityContext:
    """Aggregated upstream records needed for interpretability analysis."""
    task_id: str
    metric_evaluation: MetricEvaluation
    pipeline_execution: Optional[PipelineExecution] = None
    pipeline_generation: Optional[PipelineGeneration] = None
    feature_preprocessing: Optional[FeaturePreprocessing] = None
    iteration_decision: Optional[IterationDecision] = None
    task_interpretation: Optional[TaskInterpretation] = None
    task_specification: Optional[TaskSpecification] = None
    warnings: list = field(default_factory=list)


def build_interpretability_context(
    session: Session,
    task_id: str,
) -> InterpretabilityContext:
    """
    Gather all upstream data needed for interpretability analysis.

    Queries the latest completed record from each upstream module by task_id.
    """
    warnings_list: list = []

    try:
        return _build_context_impl(session, task_id, warnings_list)
    except Exception as e:
        logger.exception("Failed to build interpretability context for task %s: %s", task_id, str(e))
        raise


def _build_context_impl(
    session: Session,
    task_id: str,
    warnings_list: list,
) -> InterpretabilityContext:

    # 1. MetricEvaluation - the primary source of model info
    me = _get_latest_completed(session, MetricEvaluation, task_id,
                               status_field="status",
                               valid_statuses={"evaluated", "evaluated_with_warning", "partially_evaluated"})
    if not me:
        raise InterpretabilityInputInvalidException(
            f"No completed MetricEvaluation found for task '{task_id}'. "
            "At least one model must be evaluated before interpretability analysis."
        )

    if not me.best_model_id or not me.best_trial_id:
        raise InterpretabilityInputInvalidException(
            "MetricEvaluation has no best_model_id or best_trial_id. "
            "Cannot determine which model to analyze."
        )

    # 2. PipelineExecution - model artifacts and predictions
    pe = None
    if me.pipeline_execution_id:
        pe = session.get(PipelineExecution, me.pipeline_execution_id)
    if not pe:
        pe = _get_latest(session, PipelineExecution, task_id)
    if not pe:
        warnings_list.append("No PipelineExecution found; artifact paths may be incomplete.")

    # 3. PipelineGeneration - feature columns and matrix path
    pg = None
    if me.pipeline_generation_id:
        pg = session.get(PipelineGeneration, me.pipeline_generation_id)
    if not pg:
        pg = _get_latest(session, PipelineGeneration, task_id)
    if not pg:
        warnings_list.append("No PipelineGeneration found; feature columns may be incomplete.")

    # 4. FeaturePreprocessing - model_ready_matrix_path and feature_lineage
    fp = _get_latest_completed(session, FeaturePreprocessing, task_id,
                               status_field="status",
                               valid_statuses={"preprocessed", "preprocessed_with_warning", "success"})
    if not fp:
        warnings_list.append("No FeaturePreprocessing found; feature lineage unavailable.")

    # 5. IterationDecision - stop rationale for LLM context
    itd = _get_latest(session, IterationDecision, task_id)
    # Only use if decision is STOP (i.e., this is the final model)
    if itd and itd.decision != "stop":
        itd = None

    # 6. TaskInterpretation - material domain context
    ti = _get_latest(session, TaskInterpretation, task_id)

    # 7. TaskSpecification - dataset description, target name
    # TaskSpecification uses `id` as the task identifier (no separate task_id column).
    ts = session.get(TaskSpecification, task_id)

    logger.info(
        "Built interpretability context for task %s: me=%s pe=%s pg=%s fp=%s",
        task_id, me.id, pe.id if pe else None, pg.id if pg else None, fp.id if fp else None,
    )

    return InterpretabilityContext(
        task_id=task_id,
        metric_evaluation=me,
        pipeline_execution=pe,
        pipeline_generation=pg,
        feature_preprocessing=fp,
        iteration_decision=itd,
        task_interpretation=ti,
        task_specification=ts,
        warnings=warnings_list,
    )


def _get_latest(session: Session, model_class, task_id: str):
    """Get the latest record of a given model class for a task."""
    from sqlmodel import select, col
    stmt = (select(model_class)
            .where(col(model_class.task_id) == task_id)
            .order_by(col(model_class.created_at).desc())
            .limit(1))
    return session.exec(stmt).first()


def _get_latest_completed(session: Session, model_class, task_id: str,
                          status_field: str = "status",
                          valid_statuses: set = None):
    """Get the latest record with a valid completed status."""
    from sqlmodel import select, col
    stmt = (select(model_class)
            .where(col(model_class.task_id) == task_id))
    if valid_statuses:
        status_col = getattr(model_class, status_field)
        stmt = stmt.where(col(status_col).in_(valid_statuses))
    stmt = stmt.order_by(col(model_class.created_at).desc()).limit(1)
    return session.exec(stmt).first()
