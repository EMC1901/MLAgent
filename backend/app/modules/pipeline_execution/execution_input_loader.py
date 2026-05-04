"""Execution Input Loader — loads and validates execution_input_json."""

from app.modules.pipeline_execution.exceptions import ExecutionInputInvalidException
from app.modules.pipeline_generation.schemas import (
    ExecutionInput,
    PipelineSpec,
    TrialPlan,
)


def load_execution_input(execution_input_raw: dict) -> ExecutionInput:
    """Parse and validate execution_input_json.

    Args:
        execution_input_raw: Raw dict from PipelineGeneration.execution_input_json.

    Returns:
        Validated ExecutionInput object.

    Raises:
        ExecutionInputInvalidException if required fields are missing or invalid.
    """
    if not execution_input_raw:
        raise ExecutionInputInvalidException("execution_input_json is empty.")

    try:
        ei = ExecutionInput(**execution_input_raw)
    except Exception as e:
        raise ExecutionInputInvalidException(
            f"Failed to parse execution_input_json: {e}"
        )

    # Required fields
    if not ei.pipeline_generation_id:
        raise ExecutionInputInvalidException("Missing pipeline_generation_id.")
    if not ei.task_id:
        raise ExecutionInputInvalidException("Missing task_id.")

    # Pipeline specs
    if not ei.pipeline_specs:
        raise ExecutionInputInvalidException("pipeline_specs is empty.")

    for i, spec in enumerate(ei.pipeline_specs):
        if not spec.pipeline_spec_id:
            raise ExecutionInputInvalidException(
                f"pipeline_specs[{i}] missing pipeline_spec_id."
            )
        if not spec.model_id:
            raise ExecutionInputInvalidException(
                f"pipeline_specs[{i}] missing model_id."
            )
        if not spec.execution_ready:
            raise ExecutionInputInvalidException(
                f"pipeline_specs[{i}] ({spec.pipeline_spec_id}) "
                f"has execution_ready=false."
            )

    # Validation plan
    if not ei.validation_plan:
        raise ExecutionInputInvalidException("validation_plan is empty.")
    if not ei.validation_plan.get("split_strategy"):
        raise ExecutionInputInvalidException(
            "validation_plan missing split_strategy."
        )

    # Evaluation plan
    if not ei.evaluation_plan:
        raise ExecutionInputInvalidException("evaluation_plan is empty.")
    if not ei.evaluation_plan.get("primary_metric"):
        raise ExecutionInputInvalidException(
            "evaluation_plan missing primary_metric."
        )

    # Feature/target
    if not ei.feature_columns:
        raise ExecutionInputInvalidException("feature_columns is empty.")
    if not ei.target_column:
        raise ExecutionInputInvalidException("target_column is missing.")

    # Trial plan
    if not ei.trial_plan:
        raise ExecutionInputInvalidException("trial_plan is missing.")

    if not ei.ready_for_execution:
        raise ExecutionInputInvalidException(
            "ready_for_execution is false in execution_input."
        )

    return ei
