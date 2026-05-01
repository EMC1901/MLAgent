import logging
from sqlmodel import Session
from datetime import datetime
from typing import Optional

from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.task_interpretation.model import TaskInterpretation
from app.modules.task_interpretation.repository import TaskInterpretationRepository
from app.modules.task_interpretation.schemas import (
    TaskInterpretationCreateRequest,
    TaskInterpretationResponse,
    TaskInterpretationSummaryResponse,
    InterpretedPredictionTarget,
    ModelingIntent,
    DatasetIntent,
    PlanningHint,
    ConstraintInterpretation,
    RecommendedDefaults,
    AmbiguityItem,
)
from app.modules.task_interpretation.task_spec_adapter import adapt_task_spec
from app.modules.task_interpretation.prompt_builder import build_prompt
from app.modules.task_interpretation.llm_client import LLMClient
from app.modules.task_interpretation.parser import parse_llm_response
from app.modules.task_interpretation.validator import validate_interpretation
from app.modules.task_interpretation.builder import build_interpretation
from app.modules.task_interpretation.exceptions import (
    TaskNotReadyException,
    LLMCallException,
    LLMOutputParseException,
    LLMOutputValidationException,
    InterpretationNotFoundException,
)

logger = logging.getLogger(__name__)


class TaskInterpretationService:

    def __init__(self):
        self.task_repo = TaskSpecificationRepository()
        self.interp_repo = TaskInterpretationRepository()
        self.llm_client = LLMClient()

    def create_interpretation(
        self, session: Session, task_id: str, request: TaskInterpretationCreateRequest
    ) -> TaskInterpretationResponse:
        task_spec = self.task_repo.get_by_id(session, task_id)
        if not task_spec:
            from app.shared.common.exceptions import NotFoundException
            raise NotFoundException(f"Task specification with id {task_id} not found.")

        context = adapt_task_spec(task_spec)

        system_prompt, user_message = build_prompt(context)

        llm_request = {
            "provider": self.llm_client.provider,
            "model": self.llm_client.model,
            "system_prompt": system_prompt,
            "user_message": user_message,
        }

        try:
            raw_response = self.llm_client.generate(system_prompt, user_message)
        except LLMCallException:
            failed_interp = TaskInterpretation(
                id=f"interp_{__import__('uuid').uuid4().hex[:8]}",
                task_id=task_id,
                status="failed",
                llm_request_json=llm_request,
                error_message="LLM call failed.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.interp_repo.create(session, failed_interp)
            raise

        llm_output = parse_llm_response(raw_response)

        validation_result = validate_interpretation(llm_output)
        if not validation_result["is_valid"]:
            failed_interp = TaskInterpretation(
                id=f"interp_{__import__('uuid').uuid4().hex[:8]}",
                task_id=task_id,
                status="failed",
                llm_request_json=llm_request,
                llm_response_json={"raw": raw_response},
                error_message="; ".join(validation_result["errors"]),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.interp_repo.create(session, failed_interp)
            raise LLMOutputValidationException("; ".join(validation_result["errors"]))

        interpretation_dict = build_interpretation(task_id, llm_output, llm_request, raw_response)

        interp_model = TaskInterpretation(
            id=interpretation_dict["interpretation_id"],
            task_id=interpretation_dict["task_id"],
            status=interpretation_dict["status"],
            interpreted_task_type=interpretation_dict["interpreted_task_type"],
            interpreted_input_modality=interpretation_dict["interpreted_input_modality"],
            interpreted_material_domain=interpretation_dict["interpreted_material_domain"],
            confidence_score=interpretation_dict["confidence_score"],
            interpretation_json=interpretation_dict,
            llm_request_json=llm_request,
            llm_response_json={"raw": raw_response},
            created_at=datetime.fromisoformat(interpretation_dict["created_at"]),
            updated_at=datetime.fromisoformat(interpretation_dict["updated_at"]),
        )

        created = self.interp_repo.create(session, interp_model)

        return self._to_response(created)

    def get_interpretation(
        self, session: Session, interpretation_id: str
    ) -> TaskInterpretationResponse:
        interp = self.interp_repo.get_by_id(session, interpretation_id)
        if not interp:
            raise InterpretationNotFoundException(
                f"Task interpretation with id {interpretation_id} not found."
            )
        return self._to_response(interp)

    def get_latest_by_task_id(
        self, session: Session, task_id: str
    ) -> TaskInterpretationResponse:
        self._check_task_exists(session, task_id)
        interp = self.interp_repo.get_latest_by_task_id(session, task_id)
        if not interp:
            raise InterpretationNotFoundException(
                f"No interpretation found for task {task_id}."
            )
        return self._to_response(interp)

    def rerun_interpretation(
        self, session: Session, task_id: str, request: TaskInterpretationCreateRequest
    ) -> TaskInterpretationResponse:
        return self.create_interpretation(session, task_id, request)

    def _check_task_exists(self, session: Session, task_id: str):
        task_spec = self.task_repo.get_by_id(session, task_id)
        if not task_spec:
            from app.shared.common.exceptions import NotFoundException
            raise NotFoundException(f"Task specification with id {task_id} not found.")

    def _to_response(self, interp: TaskInterpretation) -> TaskInterpretationResponse:
        interp_json = interp.interpretation_json or {}

        pred_target_raw = interp_json.get("interpreted_prediction_target") or {}
        interpreted_prediction_target = InterpretedPredictionTarget(
            raw_target=pred_target_raw.get("raw_target"),
            normalized_target=pred_target_raw.get("normalized_target"),
            target_category=pred_target_raw.get("target_category"),
            target_unit=pred_target_raw.get("target_unit"),
            target_description=pred_target_raw.get("target_description"),
        )

        modeling_raw = interp_json.get("modeling_intent") or {}
        modeling_intent = ModelingIntent(
            primary_goal=modeling_raw.get("primary_goal"),
            secondary_goals=modeling_raw.get("secondary_goals", []),
            optimization_direction=modeling_raw.get("optimization_direction"),
            preferred_metric=modeling_raw.get("preferred_metric"),
        )

        dataset_raw = interp_json.get("dataset_intent") or {}
        dataset_intent = DatasetIntent(
            dataset_reference=dataset_raw.get("dataset_reference"),
            expected_input_columns=dataset_raw.get("expected_input_columns", []),
            expected_target_column=dataset_raw.get("expected_target_column"),
            requires_structure_file=dataset_raw.get("requires_structure_file", False),
            dataset_loading_hint=dataset_raw.get("dataset_loading_hint"),
        )

        planning_raw = interp_json.get("planning_hint") or {}
        planning_hint = PlanningHint(
            task_family=planning_raw.get("task_family"),
            input_representation=planning_raw.get("input_representation"),
            requires_feature_engineering=planning_raw.get("requires_feature_engineering", False),
            requires_model_interpretability=planning_raw.get("requires_model_interpretability", False),
            suggested_metric_direction=planning_raw.get("suggested_metric_direction"),
        )

        constraint_raw = interp_json.get("constraint_interpretation") or {}
        constraint_interpretation = ConstraintInterpretation(
            hard_constraints=constraint_raw.get("hard_constraints", []),
            soft_constraints=constraint_raw.get("soft_constraints", []),
            potential_conflicts=constraint_raw.get("potential_conflicts", []),
        )

        defaults_raw = interp_json.get("recommended_defaults") or {}
        recommended_defaults = RecommendedDefaults(
            evaluation_metric=defaults_raw.get("evaluation_metric"),
            validation_strategy=defaults_raw.get("validation_strategy"),
            baseline_requirement=defaults_raw.get("baseline_requirement", False),
        )

        ambiguities = [
            AmbiguityItem(field=a.get("field"), message=a.get("message"), severity=a.get("severity"))
            for a in interp_json.get("ambiguities", [])
        ]

        return TaskInterpretationResponse(
            interpretation_id=interp.id,
            task_id=interp.task_id,
            status=interp.status,
            interpreted_task_type=interp.interpreted_task_type,
            interpreted_input_modality=interp.interpreted_input_modality,
            interpreted_material_domain=interp.interpreted_material_domain,
            interpreted_prediction_target=interpreted_prediction_target,
            modeling_intent=modeling_intent,
            dataset_intent=dataset_intent,
            planning_hint=planning_hint,
            constraint_interpretation=constraint_interpretation,
            recommended_defaults=recommended_defaults,
            ambiguities=ambiguities,
            warnings=interp_json.get("warnings", []),
            llm_reasoning_summary=interp_json.get("llm_reasoning_summary"),
            confidence_score=interp.confidence_score,
            created_at=interp.created_at,
            updated_at=interp.updated_at,
        )
