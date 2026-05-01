from app.modules.task_specification.model import TaskSpecification
from app.modules.task_interpretation.exceptions import TaskNotReadyException
from typing import Dict, Any


def adapt_task_spec(task_spec: TaskSpecification) -> Dict[str, Any]:
    status = task_spec.status
    if status not in ("valid", "valid_with_warning"):
        raise TaskNotReadyException(
            f"Task status is '{status}'. Only valid or valid_with_warning tasks can be interpreted."
        )

    task_spec_json = task_spec.task_spec_json or {}

    context = {
        "task_id": task_spec.id,
        "task_summary": {
            "task_name": task_spec.task_name,
            "task_description": task_spec_json.get("task_description"),
            "material_system": task_spec_json.get("material_system"),
        },
        "ml_task": {
            "task_type": task_spec.task_type,
            "prediction_target": task_spec.prediction_target,
            "target_column": task_spec.target_column,
            "evaluation_metric": task_spec.evaluation_metric,
        },
        "data_context": {
            "dataset_description": task_spec.dataset_description,
            "input_type": task_spec.input_type,
        },
        "user_intent": {
            "user_priority": task_spec_json.get("user_priority", []),
            "constraints": task_spec_json.get("constraints", []),
        },
    }

    return context
