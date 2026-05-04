import logging
import uuid
from datetime import datetime
from sqlmodel import Session

from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.model_search_context.model import ModelSearchContext
from app.modules.model_search_context.repository import ModelSearchContextRepository
from app.modules.model_search_context.schemas import (
    ModelSearchContextCreateRequest,
    ModelSearchContextResponse,
)
from app.modules.model_search_context.context_builder import build_model_search_context
from app.modules.model_search_context.dataset_profile_analyzer import analyze_effective_dataset
from app.modules.model_search_context.feature_group_analyzer import analyze_feature_groups
from app.modules.model_search_context.preprocessing_analyzer import analyze_preprocessing
from app.modules.model_search_context.llm_context_builder import build_llm_context
from app.modules.model_search_context.llm_strategy_advisor import LLMStrategyAdvisor
from app.modules.model_search_context.llm_response_parser import parse_llm_response
from app.modules.model_search_context.llm_advice_validator import validate_llm_advice
from app.modules.model_search_context.strategy_merger import merge_strategies
from app.modules.model_search_context.builder import (
    build_model_search_context_response,
    build_context_json,
)
from app.modules.model_search_context.enums import ModelSearchContextStatus, UpdateMode
from app.modules.model_search_context.exceptions import (
    ModelSearchContextNotFoundException,
    UpstreamNotReadyException,
    LLMCallException,
    LLMOutputParseException,
    LLMAdviceValidationException,
)

logger = logging.getLogger(__name__)


class ModelSearchContextService:

    def __init__(self):
        self.task_repo = TaskSpecificationRepository()
        self.msc_repo = ModelSearchContextRepository()
        self.llm_advisor = LLMStrategyAdvisor()

    def create_model_search_context(
        self, session: Session, task_id: str, request: ModelSearchContextCreateRequest,
    ) -> ModelSearchContextResponse:
        msc_id = f"msc_{uuid.uuid4().hex[:8]}"
        all_warnings = []
        all_errors = []

        # --- 1. Build upstream context ---
        try:
            context = build_model_search_context(session, task_id)
        except UpstreamNotReadyException:
            failed = ModelSearchContext(
                id=msc_id,
                task_id=task_id,
                status=ModelSearchContextStatus.BLOCKED,
                error_message="Upstream modules not ready for model search.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.msc_repo.create(session, failed)
            raise

        task_ctx = context.get("task_context", {})
        plan_ctx = context.get("plan_context", {})
        task_type = task_ctx.get("task_type", "regression")
        target_column = task_ctx.get("target_column", "")
        primary_metric = task_ctx.get("primary_metric") or "MAE"

        # --- 2. Analyze effective dataset profile ---
        dataset_result = analyze_effective_dataset(context)

        # --- 3. Analyze feature groups ---
        feature_group_result = analyze_feature_groups(context)

        # --- 4. Analyze preprocessing execution ---
        preprocessing_result = analyze_preprocessing(context)

        # --- 5. Get original strategies from plan ---
        original_model_strategy = plan_ctx.get("model_strategy", {})
        original_hpo_strategy = plan_ctx.get("hpo_strategy", {})
        original_validation_strategy = plan_ctx.get("validation_strategy", {})
        original_evaluation_strategy = plan_ctx.get("evaluation_strategy", {})

        # --- 6. Build LLM context and call LLM ---
        llm_used = request.use_llm_advisor
        llm_request_json = {}
        llm_response_json = {}
        llm_advice = {}
        llm_confidence_score = 0.0

        if llm_used:
            system_prompt, user_message = build_llm_context(
                task_type=task_type,
                target_column=target_column,
                primary_metric=primary_metric,
                dataset_profile_result=dataset_result,
                feature_group_result=feature_group_result,
                preprocessing_result=preprocessing_result,
                original_model_strategy=original_model_strategy,
                original_hpo_strategy=original_hpo_strategy,
                original_validation_strategy=original_validation_strategy,
            )

            llm_request_json = {
                "system_prompt": system_prompt,
                "user_message": user_message,
            }

            try:
                llm_result = self.llm_advisor.generate(system_prompt, user_message)
            except LLMCallException:
                failed = ModelSearchContext(
                    id=msc_id,
                    task_id=task_id,
                    workflow_plan_id=context.get("workflow_plan_id"),
                    feature_engineering_id=context.get("feature_engineering_id"),
                    feature_preprocessing_id=context.get("feature_preprocessing_id"),
                    status=ModelSearchContextStatus.FAILED,
                    update_mode=UpdateMode.LLM_GUIDED_WITH_SYSTEM_VALIDATION,
                    task_type=task_type,
                    target_column=target_column,
                    n_samples=dataset_result.get("n_samples"),
                    n_final_features=dataset_result.get("n_final_features"),
                    primary_metric=primary_metric,
                    llm_used=True,
                    llm_request_json=llm_request_json,
                    error_message="LLM call failed.",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                self.msc_repo.create(session, failed)
                raise

            llm_response_json = {"raw": llm_result["raw_response"]}

            # --- 7. Parse LLM response ---
            try:
                llm_advice = parse_llm_response(llm_result["raw_response"])
            except LLMOutputParseException:
                failed = ModelSearchContext(
                    id=msc_id,
                    task_id=task_id,
                    workflow_plan_id=context.get("workflow_plan_id"),
                    feature_engineering_id=context.get("feature_engineering_id"),
                    feature_preprocessing_id=context.get("feature_preprocessing_id"),
                    status=ModelSearchContextStatus.FAILED,
                    update_mode=UpdateMode.LLM_GUIDED_WITH_SYSTEM_VALIDATION,
                    task_type=task_type,
                    target_column=target_column,
                    n_samples=dataset_result.get("n_samples"),
                    n_final_features=dataset_result.get("n_final_features"),
                    primary_metric=primary_metric,
                    llm_used=True,
                    llm_request_json=llm_request_json,
                    llm_response_json=llm_response_json,
                    error_message="LLM output parse error.",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                self.msc_repo.create(session, failed)
                raise

            llm_confidence_score = float(llm_advice.get("confidence_score", 0.0))

            # --- 8. Validate LLM advice ---
            validation_result = validate_llm_advice(llm_advice, task_type)
            if not validation_result["is_valid"]:
                all_warnings.append(
                    f"LLM advice partially rejected: {validation_result['rejected_suggestions']}"
                )

            if validation_result.get("warnings"):
                all_warnings.extend(validation_result["warnings"])

            validated_advice = validation_result["validated_advice"]
        else:
            validated_advice = {}
            validation_result = {
                "is_valid": True,
                "rejected_suggestions": [],
                "warnings": [],
                "fallback_applied": False,
                "validated_advice": {},
                "validation_result": None,
            }

        # --- 9. Merge strategies ---
        merge_result = merge_strategies(
            original_model_strategy=original_model_strategy,
            original_hpo_strategy=original_hpo_strategy,
            original_validation_strategy=original_validation_strategy,
            original_evaluation_strategy=original_evaluation_strategy,
            validated_llm_advice=validated_advice,
            dataset_analysis=dataset_result,
            feature_group_analysis=feature_group_result,
            preprocessing_analysis=preprocessing_result,
            adjust_model=request.adjust_model_strategy,
            adjust_hpo=request.adjust_hpo_strategy,
            adjust_validation=request.adjust_validation_strategy,
            adjust_evaluation=request.adjust_evaluation_strategy,
        )

        strategy_adjustment = merge_result.get("strategy_adjustment")

        # --- 10. Determine status ---
        if all_errors:
            status = ModelSearchContextStatus.FAILED
        elif all_warnings:
            status = ModelSearchContextStatus.UPDATED_WITH_WARNING
        else:
            status = ModelSearchContextStatus.UPDATED

        # --- 11. Build response ---
        response = build_model_search_context_response(
            context_id=msc_id,
            context=context,
            dataset_result=dataset_result,
            feature_group_result=feature_group_result,
            preprocessing_result=preprocessing_result,
            merge_result=merge_result,
            validation_result=validation_result,
            llm_advice=validated_advice if llm_used else {},
            llm_confidence_score=llm_confidence_score,
            warnings=all_warnings,
            errors=all_errors,
            status=status,
        )

        # --- 12. Persist ---
        msc_model = ModelSearchContext(
            id=msc_id,
            task_id=context["task_id"],
            workflow_plan_id=context.get("workflow_plan_id"),
            feature_engineering_id=context.get("feature_engineering_id"),
            feature_preprocessing_id=context.get("feature_preprocessing_id"),
            status=status,
            update_mode=UpdateMode.LLM_GUIDED_WITH_SYSTEM_VALIDATION,
            task_type=task_type,
            target_column=target_column,
            n_samples=dataset_result.get("n_samples"),
            n_final_features=dataset_result.get("n_final_features"),
            primary_metric=primary_metric,
            model_strategy_adjusted=strategy_adjustment.model_strategy_adjusted if strategy_adjustment else False,
            hpo_strategy_adjusted=strategy_adjustment.hpo_strategy_adjusted if strategy_adjustment else False,
            llm_used=llm_used,
            llm_confidence_score=llm_confidence_score,
            ready_for_model_search_plan=response.model_search_context_input.ready_for_model_search_plan,
            context_json=build_context_json(response),
            llm_request_json=llm_request_json if llm_request_json else None,
            llm_response_json=llm_response_json if llm_response_json else None,
            error_message=None if not all_errors else "; ".join(all_errors),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.msc_repo.create(session, msc_model)

        return response

    def get_model_search_context(
        self, session: Session, msc_id: str,
    ) -> ModelSearchContextResponse:
        msc = self.msc_repo.get_by_id(session, msc_id)
        if not msc:
            raise ModelSearchContextNotFoundException(
                f"Model search context with id {msc_id} not found."
            )
        return self._to_response(msc)

    def get_latest_by_task_id(
        self, session: Session, task_id: str,
    ) -> ModelSearchContextResponse:
        self._check_task_exists(session, task_id)
        msc = self.msc_repo.get_latest_by_task_id(session, task_id)
        if not msc:
            raise ModelSearchContextNotFoundException(
                f"No model search context found for task {task_id}."
            )
        return self._to_response(msc)

    def rerun_model_search_context(
        self, session: Session, task_id: str, request: ModelSearchContextCreateRequest,
    ) -> ModelSearchContextResponse:
        return self.create_model_search_context(session, task_id, request)

    def _check_task_exists(self, session: Session, task_id: str):
        task_spec = self.task_repo.get_by_id(session, task_id)
        if not task_spec:
            from app.shared.common.exceptions import NotFoundException
            raise NotFoundException(f"Task specification with id {task_id} not found.")

    def _to_response(self, msc: ModelSearchContext) -> ModelSearchContextResponse:
        if msc.context_json:
            try:
                return ModelSearchContextResponse(**msc.context_json)
            except Exception:
                pass

        return ModelSearchContextResponse(
            context_id=msc.id or "",
            task_id=msc.task_id or "",
            workflow_plan_id=msc.workflow_plan_id,
            feature_engineering_id=msc.feature_engineering_id,
            feature_preprocessing_id=msc.feature_preprocessing_id,
            status=msc.status or ModelSearchContextStatus.PENDING,
            update_mode=msc.update_mode,
            error_message=msc.error_message,
            confidence_score=msc.llm_confidence_score,
            created_at=msc.created_at,
            updated_at=msc.updated_at,
        )
