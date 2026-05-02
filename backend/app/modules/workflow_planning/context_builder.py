from sqlmodel import Session
from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.task_interpretation.repository import TaskInterpretationRepository
from app.modules.dataset_profile.repository import DatasetProfileRepository
from app.modules.workflow_planning.exceptions import UpstreamNotReadyException


def build_workflow_planning_context(session: Session, task_id: str) -> dict:
    task_repo = TaskSpecificationRepository()
    interp_repo = TaskInterpretationRepository()
    profile_repo = DatasetProfileRepository()

    task_spec = task_repo.get_by_id(session, task_id)
    if not task_spec:
        raise UpstreamNotReadyException(
            f"Task specification with id {task_id} not found.",
            "TASK_NOT_FOUND",
        )

    if task_spec.status not in ("valid", "valid_with_warning"):
        raise UpstreamNotReadyException(
            f"Task {task_id} status is '{task_spec.status}'. "
            "Only 'valid' or 'valid_with_warning' tasks can proceed to workflow planning.",
            "TASK_NOT_READY",
        )

    interp = interp_repo.get_latest_by_task_id(session, task_id)
    if not interp:
        raise UpstreamNotReadyException(
            f"No interpretation found for task {task_id}. "
            "Run task interpretation before workflow planning.",
            "INTERPRETATION_REQUIRED",
        )

    if interp.status not in ("interpreted", "interpreted_with_warning"):
        raise UpstreamNotReadyException(
            f"Interpretation for task {task_id} status is '{interp.status}'. "
            "Only 'interpreted' or 'interpreted_with_warning' interpretations can proceed.",
            "INTERPRETATION_NOT_READY",
        )

    profile = profile_repo.get_latest_by_task_id(session, task_id)
    if not profile:
        raise UpstreamNotReadyException(
            f"No dataset profile found for task {task_id}. "
            "Run dataset profiling before workflow planning.",
            "DATASET_PROFILE_REQUIRED",
        )

    if profile.status not in ("profiled", "profiled_with_warning"):
        raise UpstreamNotReadyException(
            f"Dataset profile for task {task_id} status is '{profile.status}'. "
            "Only 'profiled' or 'profiled_with_warning' profiles can proceed.",
            "DATASET_PROFILE_NOT_READY",
        )

    if not profile.is_usable_for_ml:
        raise UpstreamNotReadyException(
            f"Dataset for task {task_id} is not usable for machine learning.",
            "DATASET_NOT_USABLE_FOR_ML",
        )

    profile_json = profile.profile_json or {}
    workflow_planning_input = profile_json.get("workflow_planning_input")
    if not workflow_planning_input:
        raise UpstreamNotReadyException(
            f"No workflow_planning_input found in dataset profile for task {task_id}.",
            "WORKFLOW_PLANNING_INPUT_MISSING",
        )

    interp_json = interp.interpretation_json or {}
    task_spec_json = task_spec.task_spec_json or {}

    context = {
        "task_id": task_id,
        "interpretation_id": interp.id,
        "dataset_profile_id": profile.id,
        "task_context": {
            "task_name": task_spec.task_name,
            "task_description": task_spec_json.get("task_description"),
            "material_system": task_spec_json.get("material_system"),
            "task_type": task_spec.task_type,
            "input_type": task_spec.input_type,
            "prediction_target": task_spec.prediction_target,
            "target_column": task_spec.target_column,
            "evaluation_metric": task_spec.evaluation_metric,
            "user_priority": task_spec_json.get("user_priority", []),
            "constraints": task_spec_json.get("constraints", []),
        },
        "interpretation_context": {
            "interpreted_task_type": interp.interpreted_task_type,
            "interpreted_input_modality": interp.interpreted_input_modality,
            "interpreted_material_domain": interp.interpreted_material_domain,
            "interpreted_prediction_target": interp_json.get("interpreted_prediction_target"),
            "modeling_intent": interp_json.get("modeling_intent"),
            "planning_hint": interp_json.get("planning_hint"),
            "constraint_interpretation": interp_json.get("constraint_interpretation"),
            "recommended_defaults": interp_json.get("recommended_defaults"),
            "ambiguities": interp_json.get("ambiguities", []),
            "warnings": interp_json.get("warnings", []),
            "confidence_score": interp.confidence_score,
        },
        "data_context": {
            "dataset_source": profile_json.get("dataset_source"),
            "dataset_schema": profile_json.get("dataset_schema"),
            "modality_check": profile_json.get("modality_check"),
            "target_profile": profile_json.get("target_profile"),
            "data_quality": profile_json.get("data_quality"),
            "profiling_summary": profile_json.get("profiling_summary"),
            "workflow_planning_input": workflow_planning_input,
        },
    }

    return context
