"""Context Builder — validates upstream PipelineGeneration readiness."""

from typing import Optional
from sqlmodel import Session
from app.modules.pipeline_generation.model import PipelineGeneration
from app.modules.pipeline_generation.repository import PipelineGenerationRepository
from app.modules.pipeline_execution.exceptions import (
    PipelineGenerationRequiredException,
    PipelineGenerationNotReadyException,
)


def build_execution_context(
    session: Session,
    task_id: str,
    pipeline_generation_id: Optional[str] = None,
) -> PipelineGeneration:
    """Validate and retrieve the upstream PipelineGeneration.

    Args:
        session: DB session.
        task_id: The task ID.
        pipeline_generation_id: Optional specific PG to use; latest ready one if None.

    Returns:
        PipelineGeneration record that is ready for execution.

    Raises:
        PipelineGenerationRequiredException: No PG found.
        PipelineGenerationNotReadyException: PG exists but not ready.
    """
    repo = PipelineGenerationRepository()

    pg: Optional[PipelineGeneration] = None
    if pipeline_generation_id:
        pg = repo.get_by_id(session, pipeline_generation_id)
        if pg is None:
            raise PipelineGenerationRequiredException(
                f"PipelineGeneration '{pipeline_generation_id}' not found."
            )
    else:
        pg = repo.get_latest_by_task_id(session, task_id)

    if pg is None:
        raise PipelineGenerationRequiredException(
            f"No PipelineGeneration found for task '{task_id}'. "
            "Run Pipeline Generation first."
        )

    # Validate status
    allowed_statuses = {"generated", "generated_with_warning"}
    if pg.status not in allowed_statuses:
        raise PipelineGenerationNotReadyException(
            f"PipelineGeneration status is '{pg.status}', "
            f"expected one of {allowed_statuses}."
        )

    # Validate ready_for_execution
    if not pg.ready_for_execution:
        raise PipelineGenerationNotReadyException(
            "PipelineGeneration.ready_for_execution is false. "
            "Pipeline must pass system validation and safety checks before execution."
        )

    # Validate execution_input_json exists
    if not pg.execution_input_json:
        raise PipelineGenerationNotReadyException(
            "PipelineGeneration.execution_input_json is empty or missing."
        )

    return pg
