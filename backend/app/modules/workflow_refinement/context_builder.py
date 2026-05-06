import logging
from typing import Optional
from sqlmodel import Session

from app.modules.result_diagnosis.model import ResultDiagnosis
from app.modules.result_diagnosis.repository import ResultDiagnosisRepository
from app.modules.workflow_refinement.exceptions import (
    ResultDiagnosisRequiredException,
    ResultDiagnosisNotReadyException,
    WorkflowRefinementContextBuildException,
)

logger = logging.getLogger(__name__)


def build_workflow_refinement_context(
    session: Session,
    task_id: str,
    result_diagnosis_id: Optional[str] = None,
) -> ResultDiagnosis:
    """Validate ResultDiagnosis exists and is ready for closed-loop refinement."""
    rd_repo = ResultDiagnosisRepository()

    rd: Optional[ResultDiagnosis] = None
    if result_diagnosis_id:
        rd = rd_repo.get_by_id(session, result_diagnosis_id)
        if not rd:
            raise ResultDiagnosisRequiredException(
                f"ResultDiagnosis '{result_diagnosis_id}' not found."
            )
    else:
        rd = rd_repo.get_latest_by_task_id(session, task_id)
        if not rd:
            raise ResultDiagnosisRequiredException(
                f"No ResultDiagnosis found for task '{task_id}'. "
                "Run Result Diagnosis before Workflow Refinement."
            )

    if rd.status not in ("diagnosed", "diagnosed_with_warning", "fallback_diagnosed"):
        raise ResultDiagnosisNotReadyException(
            f"ResultDiagnosis '{rd.id}' status is '{rd.status}'. "
            "Must be diagnosed, diagnosed_with_warning, or fallback_diagnosed."
        )

    if not rd.ready_for_closed_loop_refinement:
        raise ResultDiagnosisNotReadyException(
            f"ResultDiagnosis '{rd.id}' is not ready for closed-loop refinement. "
            "Set ready_for_closed_loop_refinement=true first."
        )

    return rd
