import logging
from typing import Dict, Any
from app.modules.result_diagnosis.model import ResultDiagnosis
from app.modules.workflow_refinement.exceptions import WorkflowRefinementInputInvalidException

logger = logging.getLogger(__name__)


def load_closed_loop_refinement_input(rd: ResultDiagnosis) -> Dict[str, Any]:
    """Load and validate the closed_loop_refinement_input_json from ResultDiagnosis."""
    cl_input = rd.closed_loop_refinement_input_json
    if not cl_input:
        raise WorkflowRefinementInputInvalidException(
            f"ResultDiagnosis '{rd.id}' has no closed_loop_refinement_input_json."
        )

    required_fields = [
        "should_refine",
        "refinement_focus",
    ]
    for field in required_fields:
        if field not in cl_input:
            logger.warning(
                "closed_loop_refinement_input_json missing field '%s' for rd=%s",
                field,
                rd.id,
            )

    return cl_input
