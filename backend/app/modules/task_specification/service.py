from sqlmodel import Session
from app.modules.task_specification.model import TaskSpecification
from app.modules.task_specification.schemas import (
    TaskSpecificationCreateRequest,
    TaskSpecificationUpdateRequest,
    TaskSpecificationResponse,
    ValidationResultResponse,
)
from app.modules.task_specification.normalizer import normalize_fields
from app.modules.task_specification.validator import validate
from app.modules.task_specification.builder import build_task_specification
from app.modules.task_specification.repository import TaskSpecificationRepository
from app.shared.common.exceptions import NotFoundException
from datetime import datetime
import uuid


class TaskSpecificationService:

    def __init__(self):
        self.repository = TaskSpecificationRepository()

    def create_task(self, session: Session, request: TaskSpecificationCreateRequest) -> TaskSpecificationResponse:
        task_id = f"task_{uuid.uuid4().hex[:8]}"

        raw_data = request.model_dump()
        normalized_data = normalize_fields(raw_data)

        validation_result = validate(normalized_data)

        task_spec_dict = build_task_specification(
            raw_data=raw_data,
            normalized_data=normalized_data,
            validation_result=validation_result,
            task_id=task_id,
        )

        task_spec_model = TaskSpecification(
            id=task_id,
            task_name=normalized_data.get("task_name"),
            task_type=normalized_data.get("task_type"),
            prediction_target=normalized_data.get("prediction_target"),
            dataset_description=normalized_data.get("dataset_description"),
            input_type=normalized_data.get("input_type"),
            target_column=normalized_data.get("target_column"),
            evaluation_metric=normalized_data.get("evaluation_metric"),
            status=validation_result.get("status", "received"),
            task_spec_json=task_spec_dict,
            created_at=task_spec_dict["created_at"],
            updated_at=task_spec_dict["updated_at"],
        )

        created_task = self.repository.create(session, task_spec_model)

        return TaskSpecificationResponse(
            task_id=created_task.id,
            task_name=created_task.task_name,
            task_description=task_spec_dict.get("task_description"),
            material_system=task_spec_dict.get("material_system"),
            prediction_target=created_task.prediction_target,
            task_type=created_task.task_type,
            dataset_description=created_task.dataset_description,
            input_type=created_task.input_type,
            target_column=created_task.target_column,
            evaluation_metric=created_task.evaluation_metric,
            user_priority=task_spec_dict.get("user_priority", []),
            constraints=task_spec_dict.get("constraints", []),
            status=created_task.status,
            missing_fields=validation_result.get("missing_fields", []),
            validation_messages=validation_result.get("validation_messages", []),
            created_at=created_task.created_at,
            updated_at=created_task.updated_at,
        )

    def get_task(self, session: Session, task_id: str) -> TaskSpecificationResponse:
        task = self.repository.get_by_id(session, task_id)
        if not task:
            raise NotFoundException(f"Task specification with id {task_id} not found.")

        task_spec_json = task.task_spec_json or {}

        return TaskSpecificationResponse(
            task_id=task.id,
            task_name=task.task_name,
            task_description=task_spec_json.get("task_description"),
            material_system=task_spec_json.get("material_system"),
            prediction_target=task.prediction_target,
            task_type=task.task_type,
            dataset_description=task.dataset_description,
            input_type=task.input_type,
            target_column=task.target_column,
            evaluation_metric=task.evaluation_metric,
            user_priority=task_spec_json.get("user_priority", []),
            constraints=task_spec_json.get("constraints", []),
            status=task.status,
            missing_fields=task_spec_json.get("missing_fields", []),
            validation_messages=task_spec_json.get("validation_messages", []),
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    def update_task(self, session: Session, task_id: str, request: TaskSpecificationUpdateRequest) -> TaskSpecificationResponse:
        existing_task = self.repository.get_by_id(session, task_id)
        if not existing_task:
            raise NotFoundException(f"Task specification with id {task_id} not found.")

        existing_json = existing_task.task_spec_json or {}

        update_data = request.model_dump(exclude_unset=True)

        merged_data = {
            "task_name": update_data.get("task_name", existing_task.task_name),
            "task_description": update_data.get("task_description", existing_json.get("task_description")),
            "material_system": update_data.get("material_system", existing_json.get("material_system")),
            "prediction_target": update_data.get("prediction_target", existing_task.prediction_target),
            "task_type": update_data.get("task_type", existing_task.task_type),
            "dataset_description": update_data.get("dataset_description", existing_task.dataset_description),
            "input_type": update_data.get("input_type", existing_task.input_type),
            "target_column": update_data.get("target_column", existing_task.target_column),
            "evaluation_metric": update_data.get("evaluation_metric", existing_task.evaluation_metric),
            "user_priority": update_data.get("user_priority", existing_json.get("user_priority", [])),
            "constraints": update_data.get("constraints", existing_json.get("constraints", [])),
        }

        normalized_data = normalize_fields(merged_data)

        validation_result = validate(normalized_data)

        task_spec_dict = build_task_specification(
            raw_data=merged_data,
            normalized_data=normalized_data,
            validation_result=validation_result,
            task_id=task_id,
            created_at=existing_task.created_at,
            updated_at=datetime.now(),
        )

        existing_task.task_name = normalized_data.get("task_name")
        existing_task.task_type = normalized_data.get("task_type")
        existing_task.prediction_target = normalized_data.get("prediction_target")
        existing_task.dataset_description = normalized_data.get("dataset_description")
        existing_task.input_type = normalized_data.get("input_type")
        existing_task.target_column = normalized_data.get("target_column")
        existing_task.evaluation_metric = normalized_data.get("evaluation_metric")
        existing_task.status = validation_result.get("status", "updated")
        existing_task.task_spec_json = task_spec_dict
        existing_task.updated_at = task_spec_dict["updated_at"]

        updated_task = self.repository.update(session, task_id, existing_task)

        return TaskSpecificationResponse(
            task_id=updated_task.id,
            task_name=updated_task.task_name,
            task_description=task_spec_dict.get("task_description"),
            material_system=task_spec_dict.get("material_system"),
            prediction_target=updated_task.prediction_target,
            task_type=updated_task.task_type,
            dataset_description=updated_task.dataset_description,
            input_type=updated_task.input_type,
            target_column=updated_task.target_column,
            evaluation_metric=updated_task.evaluation_metric,
            user_priority=task_spec_dict.get("user_priority", []),
            constraints=task_spec_dict.get("constraints", []),
            status=updated_task.status,
            missing_fields=validation_result.get("missing_fields", []),
            validation_messages=validation_result.get("validation_messages", []),
            created_at=updated_task.created_at,
            updated_at=updated_task.updated_at,
        )

    def validate_task(self, session: Session, task_id: str) -> ValidationResultResponse:
        task = self.repository.get_by_id(session, task_id)
        if not task:
            raise NotFoundException(f"Task specification with id {task_id} not found.")

        task_spec_json = task.task_spec_json or {}

        normalized_data = {
            "task_name": task.task_name,
            "task_description": task_spec_json.get("task_description"),
            "material_system": task_spec_json.get("material_system"),
            "prediction_target": task.prediction_target,
            "task_type": task.task_type,
            "dataset_description": task.dataset_description,
            "input_type": task.input_type,
            "target_column": task.target_column,
            "evaluation_metric": task.evaluation_metric,
            "user_priority": task_spec_json.get("user_priority", []),
            "constraints": task_spec_json.get("constraints", []),
        }

        validation_result = validate(normalized_data)

        return ValidationResultResponse(
            status=validation_result.get("status"),
            missing_fields=validation_result.get("missing_fields", []),
            validation_messages=validation_result.get("validation_messages", []),
            warnings=validation_result.get("warnings", []),
        )
