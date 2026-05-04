import logging
from app.modules.pipeline_generation.schemas import ExecutionInput, ExecutionConstraints
from app.modules.pipeline_generation.exceptions import ExecutionInputBuildException

logger = logging.getLogger(__name__)


def build_execution_input(
    context: dict,
    pipeline_generation_id: str,
    pipeline_bundle_id: str,
    pipeline_specs: list,
    trial_plan,
    validation_result,
    safety_check_result,
) -> ExecutionInput:
    """Build the ExecutionInput that downstream Pipeline Execution module will consume."""

    if not pipeline_specs:
        raise ExecutionInputBuildException("No pipeline specs available for execution input.")

    validation_valid = validation_result.is_valid if validation_result else False
    safety_safe = safety_check_result.is_safe if safety_check_result else False

    specs = [s if isinstance(s, dict) else s.model_dump() for s in pipeline_specs]

    ready = bool(
        validation_valid
        and safety_safe
        and context.get("model_ready_matrix_path")
        and context.get("feature_columns")
        and len(specs) > 0
    )

    eval_plan = context.get("evaluation_plan", {})
    validation_plan = context.get("validation_plan", {})

    return ExecutionInput(
        pipeline_generation_id=pipeline_generation_id,
        pipeline_bundle_id=pipeline_bundle_id,
        task_id=context.get("task_id", ""),
        task_type=context.get("task_type"),
        model_ready_matrix_path=context.get("model_ready_matrix_path"),
        preprocessor_artifact_path=context.get("preprocessor_artifact_path"),
        target_column=context.get("target_column"),
        feature_columns=context.get("feature_columns", []),
        pipeline_specs=[s if isinstance(s, dict) else s.model_dump() for s in pipeline_specs],
        trial_plan=trial_plan.model_dump() if trial_plan and hasattr(trial_plan, "model_dump") else trial_plan,
        validation_plan=validation_plan if isinstance(validation_plan, dict) else {},
        evaluation_plan=eval_plan if isinstance(eval_plan, dict) else {},
        execution_constraints=ExecutionConstraints(
            max_runtime_seconds=3600,
            max_memory_mb=4096,
        ),
        ready_for_execution=ready,
    )
