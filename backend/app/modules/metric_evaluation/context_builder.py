from typing import Optional
from sqlmodel import Session
from app.modules.pipeline_execution.model import PipelineExecution
from app.modules.pipeline_execution.repository import PipelineExecutionRepository
from app.modules.metric_evaluation.exceptions import (
    PipelineExecutionRequiredException,
    PipelineExecutionNotReadyException,
)


def build_metric_evaluation_context(
    session: Session,
    task_id: str,
    pipeline_execution_id: Optional[str] = None,
) -> PipelineExecution:
    pe_repo = PipelineExecutionRepository()

    if pipeline_execution_id:
        pe = pe_repo.get_by_id(session, pipeline_execution_id)
    else:
        pe = pe_repo.get_latest_by_task_id(session, task_id)

    if not pe:
        raise PipelineExecutionRequiredException(
            f"No PipelineExecution found for task '{task_id}'. "
            "Run Pipeline Execution and Training first."
        )

    allowed_statuses = ("completed", "completed_with_warning", "partially_failed")
    if pe.status not in allowed_statuses:
        raise PipelineExecutionNotReadyException(
            f"PipelineExecution '{pe.id}' status is '{pe.status}'. "
            f"Expected one of: {', '.join(allowed_statuses)}."
        )

    if not pe.ready_for_metric_evaluation:
        raise PipelineExecutionNotReadyException(
            f"PipelineExecution '{pe.id}' is not ready for metric evaluation. "
            "Ensure at least 1 completed trial with prediction artifacts exists."
        )

    return pe
