import logging
from typing import Optional
from sqlmodel import Session

from app.modules.final_pipeline_selection.model import FinalPipelineSelection
from app.modules.final_pipeline_selection.repository import FinalPipelineSelectionRepository
from app.modules.metric_evaluation.model import MetricEvaluation
from app.modules.metric_evaluation.repository import MetricEvaluationRepository
from app.modules.pipeline_execution.model import PipelineExecution
from app.modules.pipeline_execution.repository import PipelineExecutionRepository
from app.modules.task_specification.model import TaskSpecification
from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.interpretability_analysis.exceptions import (
    FinalPipelineSelectionRequiredException,
    FinalPipelineSelectionNotReadyException,
)

logger = logging.getLogger(__name__)


class InterpretabilityContext:
    def __init__(
        self,
        final_pipeline_selection: FinalPipelineSelection,
        metric_evaluations: Optional[list] = None,
        pipeline_executions: Optional[list] = None,
        task_spec: Optional[TaskSpecification] = None,
    ):
        self.final_pipeline_selection = final_pipeline_selection
        self.metric_evaluations = metric_evaluations or []
        self.pipeline_executions = pipeline_executions or []
        self.task_spec = task_spec


def build_interpretability_context(
    session: Session,
    task_id: str,
    final_pipeline_selection_id: Optional[str] = None,
) -> FinalPipelineSelection:
    fps_repo = FinalPipelineSelectionRepository()

    if final_pipeline_selection_id:
        fps = fps_repo.get_by_id(session, final_pipeline_selection_id)
        if not fps:
            raise FinalPipelineSelectionRequiredException(
                f"FinalPipelineSelection {final_pipeline_selection_id} not found."
            )
        if fps.task_id != task_id:
            raise FinalPipelineSelectionRequiredException(
                "FinalPipelineSelection does not belong to the given task."
            )
    else:
        fps = fps_repo.get_latest_by_task_id(session, task_id)

    if not fps:
        raise FinalPipelineSelectionRequiredException(
            "No FinalPipelineSelection found for this task. Run Final Pipeline Selection first."
        )

    valid_statuses = {"selected", "selected_with_warning"}
    if fps.status not in valid_statuses:
        raise FinalPipelineSelectionNotReadyException(
            f"FinalPipelineSelection status is '{fps.status}', expected one of {valid_statuses}."
        )

    if not fps.ready_for_interpretability_analysis:
        raise FinalPipelineSelectionNotReadyException(
            "FinalPipelineSelection.ready_for_interpretability_analysis is not true."
        )

    if not fps.interpretability_analysis_input_json:
        raise FinalPipelineSelectionNotReadyException(
            "FinalPipelineSelection.interpretability_analysis_input_json is missing."
        )

    return fps
