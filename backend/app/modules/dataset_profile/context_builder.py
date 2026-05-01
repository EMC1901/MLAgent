from sqlmodel import Session
from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.task_interpretation.repository import TaskInterpretationRepository
from app.modules.dataset_profile.exceptions import DatasetContextBuildException


def build_dataset_loading_context(session: Session, task_id: str) -> dict:
    task_repo = TaskSpecificationRepository()
    interp_repo = TaskInterpretationRepository()

    task_spec = task_repo.get_by_id(session, task_id)
    if not task_spec:
        raise DatasetContextBuildException(
            f"Task specification with id {task_id} not found."
        )

    if task_spec.status not in ("valid", "valid_with_warning"):
        raise DatasetContextBuildException(
            f"Task {task_id} status is '{task_spec.status}'. "
            "Only 'valid' or 'valid_with_warning' tasks can be profiled."
        )

    interp = interp_repo.get_latest_by_task_id(session, task_id)
    if not interp:
        raise DatasetContextBuildException(
            f"No interpretation found for task {task_id}. "
            "Run task interpretation before dataset profiling."
        )

    if interp.status not in ("interpreted", "interpreted_with_warning"):
        raise DatasetContextBuildException(
            f"Interpretation for task {task_id} status is '{interp.status}'. "
            "Only 'interpreted' or 'interpreted_with_warning' interpretations can proceed."
        )

    interp_json = interp.interpretation_json or {}
    dataset_intent = interp_json.get("dataset_intent") or {}

    if not dataset_intent:
        raise DatasetContextBuildException(
            f"No dataset_intent found in interpretation for task {task_id}."
        )

    task_spec_json = task_spec.task_spec_json or {}

    context = {
        "task_id": task_id,
        "interpretation_id": interp.id,
        "task_context": {
            "task_type": task_spec.task_type,
            "prediction_target": task_spec.prediction_target,
            "target_column": task_spec.target_column,
            "dataset_description": task_spec.dataset_description,
            "input_type": task_spec.input_type,
            "evaluation_metric": task_spec.evaluation_metric,
        },
        "interpretation_context": {
            "interpreted_task_type": interp.interpreted_task_type,
            "interpreted_input_modality": interp.interpreted_input_modality,
            "interpreted_material_domain": interp.interpreted_material_domain,
            "warnings": interp_json.get("warnings", []),
            "ambiguities": interp_json.get("ambiguities", []),
            "planning_hint": interp_json.get("planning_hint"),
        },
        "dataset_context": {
            "dataset_description": task_spec.dataset_description,
            "dataset_intent": dataset_intent,
            "expected_input_columns": dataset_intent.get("expected_input_columns", []),
            "expected_target_column": dataset_intent.get("expected_target_column"),
            "requires_structure_file": dataset_intent.get("requires_structure_file", False),
            "dataset_loading_hint": dataset_intent.get("dataset_loading_hint"),
        },
        "expected_input_modality": interp.interpreted_input_modality,
        "expected_target_column": dataset_intent.get("expected_target_column") or task_spec.target_column,
        "expected_task_type": interp.interpreted_task_type or task_spec.task_type,
    }

    return context
