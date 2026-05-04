import logging
import uuid
from datetime import datetime
from sqlmodel import Session

from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.model_search.model import ModelSearchPlan
from app.modules.model_search.repository import ModelSearchPlanRepository
from app.modules.model_search.schemas import (
    ModelSearchPlanCreateRequest,
    ModelSearchPlanResponse,
    ModelSearchPlanSummaryResponse,
)
from app.modules.model_search.context_builder import build_model_search_context
from app.modules.model_search.llm_prompt_builder import build_llm_model_search_prompt
from app.modules.model_search.llm_model_search_advisor import LLMModelSearchAdvisor
from app.modules.model_search.llm_response_parser import parse_llm_model_search_response
from app.modules.model_search.llm_advice_validator import validate_llm_advice
from app.modules.model_search.candidate_model_selector import select_candidate_models
from app.modules.model_search.hpo_plan_builder import build_hpo_plan
from app.modules.model_search.search_space_builder import build_search_space_plan
from app.modules.model_search.trial_allocator import allocate_trials
from app.modules.model_search.validation_plan_builder import build_validation_plan
from app.modules.model_search.evaluation_plan_builder import build_evaluation_plan
from app.modules.model_search.pipeline_input_builder import build_pipeline_generation_input
from app.modules.model_search.builder import build_model_search_plan_response, build_plan_json
from app.modules.model_search.enums import ModelSearchPlanStatus
from app.modules.model_search.exceptions import (
    ModelSearchPlanNotFoundException,
    ModelSearchContextRequiredException,
    ModelSearchContextNotReadyException,
    ModelReadyInputNotReadyException,
    LLMModelSearchCallException,
    LLMModelSearchParseException,
    LLMModelSearchValidationException,
)

logger = logging.getLogger(__name__)


class ModelSearchService:

    def __init__(self):
        self.task_repo = TaskSpecificationRepository()
        self.plan_repo = ModelSearchPlanRepository()
        self.llm_advisor = LLMModelSearchAdvisor()

    def create_model_search_plan(
        self, session: Session, task_id: str, request: ModelSearchPlanCreateRequest,
    ) -> ModelSearchPlanResponse:
        plan_id = f"msp_{uuid.uuid4().hex[:8]}"
        all_warnings = []
        all_errors = []

        # --- 1. Build upstream context ---
        try:
            context = build_model_search_context(session, task_id)
        except (
            ModelSearchContextRequiredException,
            ModelSearchContextNotReadyException,
            ModelReadyInputNotReadyException,
        ):
            failed = ModelSearchPlan(
                id=plan_id,
                task_id=task_id,
                status=ModelSearchPlanStatus.BLOCKED,
                error_message="Upstream model search context not ready.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.plan_repo.create(session, failed)
            raise

        task_type = context.get("task_type", "regression")
        primary_metric = context.get("primary_metric", "MAE")
        n_samples = context.get("n_samples", 0)
        n_features = context.get("n_features", 0)

        # --- 2. Build LLM prompt and call LLM ---
        llm_used = request.use_llm_advisor
        llm_request_json = {}
        llm_response_json = {}
        llm_advice = {}
        llm_confidence_score = 0.0

        if llm_used:
            system_prompt, user_message = build_llm_model_search_prompt(context)
            llm_request_json = {
                "system_prompt": system_prompt,
                "user_message": user_message,
            }

            try:
                llm_result = self.llm_advisor.generate(system_prompt, user_message)
            except LLMModelSearchCallException:
                failed = ModelSearchPlan(
                    id=plan_id,
                    task_id=task_id,
                    model_search_context_id=context.get("model_search_context_id"),
                    feature_preprocessing_id=context.get("feature_preprocessing_id"),
                    workflow_plan_id=context.get("workflow_plan_id"),
                    status=ModelSearchPlanStatus.FAILED,
                    task_type=task_type,
                    target_column=context.get("target_column"),
                    primary_metric=primary_metric,
                    n_samples=n_samples,
                    n_features=n_features,
                    llm_used=True,
                    llm_request_json=llm_request_json,
                    error_message="LLM model search call failed.",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                self.plan_repo.create(session, failed)
                raise

            llm_response_json = {"raw": llm_result["raw_response"]}

            # --- 3. Parse LLM response ---
            try:
                llm_advice = parse_llm_model_search_response(llm_result["raw_response"])
            except LLMModelSearchParseException:
                failed = ModelSearchPlan(
                    id=plan_id,
                    task_id=task_id,
                    model_search_context_id=context.get("model_search_context_id"),
                    feature_preprocessing_id=context.get("feature_preprocessing_id"),
                    workflow_plan_id=context.get("workflow_plan_id"),
                    status=ModelSearchPlanStatus.FAILED,
                    task_type=task_type,
                    target_column=context.get("target_column"),
                    primary_metric=primary_metric,
                    n_samples=n_samples,
                    n_features=n_features,
                    llm_used=True,
                    llm_request_json=llm_request_json,
                    llm_response_json=llm_response_json,
                    error_message="LLM model search output parse error.",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                self.plan_repo.create(session, failed)
                raise

            llm_confidence_score = float(llm_advice.get("confidence_score", 0.0))

            # --- 4. Validate LLM advice ---
            validation_result = validate_llm_advice(
                llm_advice,
                context.get("allowed_model_families", []),
                context.get("allowed_hpo_methods", []),
            )

            if not validation_result["is_valid"]:
                all_warnings.append(
                    "LLM advice partially rejected: "
                    + ", ".join(validation_result.get("rejected_models", []))
                )

            if validation_result.get("warnings"):
                all_warnings.extend(validation_result["warnings"])

            validated_advice = validation_result["validated_advice"]
        else:
            validated_advice = {}
            validation_result = {
                "is_valid": True,
                "rejected_models": [],
                "rejected_hpo_methods": [],
                "fallback_applied": False,
                "warnings": [],
                "validated_advice": {},
                "validation_result": None,
            }

        # --- 5. Select candidate models ---
        candidate_model_data = select_candidate_models(
            llm_advice=validated_advice,
            allowed_model_families=context.get("allowed_model_families", []),
            task_type=task_type,
            use_llm_advisor=llm_used,
            include_models=request.include_models,
            exclude_models=request.exclude_models,
        )

        # --- 6. Build HPO plan ---
        candidate_models_dicts = candidate_model_data.get("candidate_models", [])
        baseline_models_dicts = candidate_model_data.get("baseline_models", [])

        hpo_plan = build_hpo_plan(
            llm_advice=validated_advice if llm_used else {},
            updated_hpo_strategy=context.get("updated_hpo_strategy", {}),
            n_samples=n_samples,
            n_features=n_features,
            candidate_models=[m if isinstance(m, dict) else m.model_dump() for m in candidate_models_dicts],
            baseline_models=[m if isinstance(m, dict) else m.model_dump() for m in baseline_models_dicts],
            preferred_search_method=request.preferred_search_method,
            max_total_trials_override=request.max_total_trials_override,
        )

        # --- 7. Build search space plan ---
        search_space_profile = validated_advice.get("search_space_profile", {}) if llm_used else {}
        hpo_candidate_models = [
            m if isinstance(m, dict) else m.model_dump() for m in candidate_models_dicts
        ]
        # Add baseline models with HPO enabled
        for b in baseline_models_dicts:
            bd = b if isinstance(b, dict) else b.model_dump()
            if bd.get("hpo_enabled"):
                hpo_candidate_models.append(bd)

        search_space_plan = build_search_space_plan(
            candidate_models=hpo_candidate_models,
            task_type=task_type,
            search_space_profile=search_space_profile,
        )

        # --- 8. Build validation plan ---
        validation_plan = build_validation_plan(
            context.get("updated_validation_strategy", {}),
        )

        # --- 9. Build evaluation plan ---
        evaluation_plan = build_evaluation_plan(
            primary_metric=primary_metric,
            task_type=task_type,
            updated_evaluation_strategy=context.get("updated_evaluation_strategy", {}),
        )

        # --- 10. Determine status ---
        if all_errors:
            status = ModelSearchPlanStatus.FAILED
        elif all_warnings:
            status = ModelSearchPlanStatus.PLANNED_WITH_WARNING
        else:
            status = ModelSearchPlanStatus.PLANNED

        # --- 11. Build response ---
        response = build_model_search_plan_response(
            plan_id=plan_id,
            context=context,
            candidate_model_plan_data={
                "baseline_models": [m if isinstance(m, dict) else m.model_dump() for m in candidate_model_data.get("baseline_models", [])],
                "candidate_models": [m if isinstance(m, dict) else m.model_dump() for m in candidate_model_data.get("candidate_models", [])],
                "excluded_models": [m if isinstance(m, dict) else m.model_dump() for m in candidate_model_data.get("excluded_models", [])],
            },
            hpo_plan=hpo_plan,
            search_space_plan=search_space_plan,
            validation_plan=validation_plan,
            evaluation_plan=evaluation_plan,
            validation_result=validation_result,
            llm_advice=validated_advice if llm_used else {},
            llm_confidence_score=llm_confidence_score,
            llm_used=llm_used,
            warnings=all_warnings,
            errors=all_errors,
            status=status,
        )

        # --- 12. Persist ---
        plan_model = ModelSearchPlan(
            id=plan_id,
            task_id=context["task_id"],
            model_search_context_id=context.get("model_search_context_id"),
            feature_preprocessing_id=context.get("feature_preprocessing_id"),
            workflow_plan_id=context.get("workflow_plan_id"),
            status=status,
            planning_mode=response.planning_mode,
            task_type=task_type,
            target_column=context.get("target_column"),
            primary_metric=primary_metric,
            n_samples=n_samples,
            n_features=n_features,
            n_candidate_models=len(candidate_model_data.get("candidate_models", [])),
            hpo_enabled=hpo_plan.enabled if hpo_plan else False,
            hpo_method=hpo_plan.search_method if hpo_plan else None,
            max_total_trials=hpo_plan.max_total_trials if hpo_plan else None,
            ready_for_pipeline_generation=response.pipeline_generation_input.ready_for_pipeline_generation,
            llm_used=llm_used,
            llm_confidence_score=llm_confidence_score,
            plan_json=build_plan_json(response),
            llm_request_json=llm_request_json if llm_request_json else None,
            llm_response_json=llm_response_json if llm_response_json else None,
            error_message=None if not all_errors else "; ".join(all_errors),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.plan_repo.create(session, plan_model)

        return response

    def get_model_search_plan(
        self, session: Session, plan_id: str,
    ) -> ModelSearchPlanResponse:
        plan = self.plan_repo.get_by_id(session, plan_id)
        if not plan:
            raise ModelSearchPlanNotFoundException(
                f"Model search plan with id {plan_id} not found."
            )
        return self._to_response(plan)

    def get_latest_by_task_id(
        self, session: Session, task_id: str,
    ) -> ModelSearchPlanResponse:
        self._check_task_exists(session, task_id)
        plan = self.plan_repo.get_latest_by_task_id(session, task_id)
        if not plan:
            raise ModelSearchPlanNotFoundException(
                f"No model search plan found for task {task_id}."
            )
        return self._to_response(plan)

    def rerun_model_search_plan(
        self, session: Session, task_id: str, request: ModelSearchPlanCreateRequest,
    ) -> ModelSearchPlanResponse:
        return self.create_model_search_plan(session, task_id, request)

    def get_plan_summary(
        self, session: Session, plan_id: str,
    ) -> ModelSearchPlanSummaryResponse:
        plan = self.plan_repo.get_by_id(session, plan_id)
        if not plan:
            raise ModelSearchPlanNotFoundException(
                f"Model search plan with id {plan_id} not found."
            )
        plan_json = plan.plan_json or {}
        return ModelSearchPlanSummaryResponse(
            model_search_plan_id=plan.id or "",
            task_id=plan.task_id or "",
            status=plan.status or "",
            task_type=plan.task_type,
            primary_metric=plan.primary_metric,
            n_candidate_models=plan.n_candidate_models or 0,
            hpo_enabled=plan.hpo_enabled or False,
            hpo_method=plan.hpo_method,
            max_total_trials=plan.max_total_trials or 0,
            ready_for_pipeline_generation=plan.ready_for_pipeline_generation or False,
            n_warnings=len(plan_json.get("warnings", [])),
            n_errors=len(plan_json.get("errors", [])),
        )

    def _check_task_exists(self, session: Session, task_id: str):
        task_spec = self.task_repo.get_by_id(session, task_id)
        if not task_spec:
            from app.shared.common.exceptions import NotFoundException
            raise NotFoundException(f"Task specification with id {task_id} not found.")

    def _to_response(self, plan: ModelSearchPlan) -> ModelSearchPlanResponse:
        if plan.plan_json:
            try:
                return ModelSearchPlanResponse(**plan.plan_json)
            except Exception:
                pass

        return ModelSearchPlanResponse(
            model_search_plan_id=plan.id or "",
            task_id=plan.task_id or "",
            model_search_context_id=plan.model_search_context_id,
            feature_preprocessing_id=plan.feature_preprocessing_id,
            workflow_plan_id=plan.workflow_plan_id,
            status=plan.status or ModelSearchPlanStatus.PENDING,
            planning_mode=plan.planning_mode,
            error_message=plan.error_message,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )
