import logging
from typing import Optional
from sqlmodel import Session

from app.modules.interpretability_analysis.model import InterpretabilityAnalysis
from app.modules.interpretability_analysis.repository import InterpretabilityAnalysisRepository
from app.modules.final_output.exceptions import (
    InterpretabilityAnalysisRequiredException,
    InterpretabilityAnalysisNotReadyException,
)

logger = logging.getLogger(__name__)


class FinalOutputContext:
    def __init__(self, interpretability_analysis: InterpretabilityAnalysis):
        self.interpretability_analysis = interpretability_analysis


def build_final_output_context(
    session: Session,
    task_id: str,
    interpretability_analysis_id: Optional[str] = None,
) -> InterpretabilityAnalysis:
    ia_repo = InterpretabilityAnalysisRepository()

    if interpretability_analysis_id:
        ia = ia_repo.get_by_id(session, interpretability_analysis_id)
        if not ia:
            raise InterpretabilityAnalysisRequiredException(
                f"InterpretabilityAnalysis {interpretability_analysis_id} not found."
            )
        if ia.task_id != task_id:
            raise InterpretabilityAnalysisRequiredException(
                "InterpretabilityAnalysis does not belong to the given task."
            )
    else:
        ia = ia_repo.get_latest_by_task_id(session, task_id)

    if not ia:
        raise InterpretabilityAnalysisRequiredException(
            "No InterpretabilityAnalysis found for this task. Run Interpretability Analysis first."
        )

    valid_statuses = {"analyzed", "analyzed_with_warning"}
    if ia.status not in valid_statuses:
        raise InterpretabilityAnalysisNotReadyException(
            f"InterpretabilityAnalysis status is '{ia.status}', expected one of {valid_statuses}."
        )

    if not ia.ready_for_final_output:
        raise InterpretabilityAnalysisNotReadyException(
            "InterpretabilityAnalysis.ready_for_final_output is not true."
        )

    if not ia.final_output_input_json:
        raise InterpretabilityAnalysisNotReadyException(
            "InterpretabilityAnalysis.final_output_input_json is missing."
        )

    return ia
