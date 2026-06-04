from typing import Dict, Any
from datetime import datetime


def build_task_specification(
    normalized_data: Dict[str, Any],
    validation_result: Dict[str, Any],
    task_id: str,
    created_at: datetime = None,
    updated_at: datetime = None,
) -> Dict[str, Any]:
    _created_at = (created_at or datetime.now()).isoformat()
    _updated_at = (updated_at or datetime.now()).isoformat()

    task_spec = {
        "task_id": task_id,
        "task_name": normalized_data.get("task_name"),
        "task_description": normalized_data.get("task_description"),
        "material_system": normalized_data.get("material_system"),
        "prediction_target": normalized_data.get("prediction_target"),
        "task_type": normalized_data.get("task_type"),
        "dataset_description": normalized_data.get("dataset_description"),
        "input_type": normalized_data.get("input_type"),
        "target_column": normalized_data.get("target_column"),
        "evaluation_metric": normalized_data.get("evaluation_metric"),
        "user_priority": normalized_data.get("user_priority", []),
        "constraints": normalized_data.get("constraints", []),
        "status": validation_result.get("status", "valid"),
        "missing_fields": validation_result.get("missing_fields", []),
        "validation_messages": validation_result.get("validation_messages", []),
        "created_at": _created_at,
        "updated_at": _updated_at,
    }

    return task_spec
