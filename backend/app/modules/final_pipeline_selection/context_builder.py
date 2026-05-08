import logging
from typing import Optional
from sqlmodel import Session

from app.modules.workflow_refinement.model import WorkflowRefinement
from app.modules.workflow_refinement.repository import WorkflowRefinementRepository
from app.modules.workflow_refinement.enums import (
    WorkflowRefinementDecision,
)
from app.modules.metric_evaluation.model import MetricEvaluation
from app.modules.pipeline_execution.model import PipelineExecution
from app.modules.pipeline_generation.model import PipelineGeneration
from app.modules.task_specification.model import TaskSpecification
from app.modules.final_pipeline_selection.exceptions import (
    WorkflowRefinementRequiredException,
    WorkflowRefinementNotReadyException,
    WorkflowRefinementDecisionInvalidException,
)

logger = logging.getLogger(__name__)


class FinalSelectionContext:
    def __init__(
        self,
        workflow_refinement: WorkflowRefinement,
        metric_evaluations: list,
        pipeline_executions: list,
        pipeline_generations: list,
        task_spec: Optional[TaskSpecification] = None,
    ):
        self.workflow_refinement = workflow_refinement
        self.metric_evaluations = metric_evaluations
        self.pipeline_executions = pipeline_executions
        self.pipeline_generations = pipeline_generations
        self.task_spec = task_spec


def build_final_selection_context(
    session: Session,
    task_id: str,
    workflow_refinement_id: Optional[str] = None,
) -> WorkflowRefinement:
    wr_repo = WorkflowRefinementRepository()

    if workflow_refinement_id:
        wr = wr_repo.get_by_id(session, workflow_refinement_id)
        if not wr:
            raise WorkflowRefinementRequiredException(
                f"WorkflowRefinement {workflow_refinement_id} not found."
            )
        if wr.task_id != task_id:
            raise WorkflowRefinementRequiredException(
                "WorkflowRefinement does not belong to the given task."
            )
    else:
        wr = wr_repo.get_latest_by_task_id(session, task_id)

    if not wr:
        raise WorkflowRefinementRequiredException(
            "No WorkflowRefinement found for this task."
        )

    if wr.decision != WorkflowRefinementDecision.PROCEED_NEXT_STAGE:
        raise WorkflowRefinementDecisionInvalidException(
            f"WorkflowRefinement decision is '{wr.decision}', expected '{WorkflowRefinementDecision.PROCEED_NEXT_STAGE}'."
        )

    if not wr.ready_for_final_pipeline_selection:
        raise WorkflowRefinementNotReadyException(
            "WorkflowRefinement is not ready for final pipeline selection."
        )

    if not wr.final_pipeline_selection_input_json:
        raise WorkflowRefinementNotReadyException(
            "WorkflowRefinement.final_pipeline_selection_input_json is missing."
        )

    return wr
