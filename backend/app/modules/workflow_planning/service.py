import logging
from sqlmodel import Session
from datetime import datetime

from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.task_interpretation.repository import TaskInterpretationRepository
from app.modules.dataset_profile.repository import DatasetProfileRepository
from app.modules.workflow_planning.model import WorkflowPlan
from app.modules.workflow_planning.repository import WorkflowPlanRepository
from app.modules.workflow_planning.schemas import (
    WorkflowPlanCreateRequest,
    WorkflowPlanResponse,
    TaskSummary,
    DataStrategy,
    TargetHandling,
    FeatureStrategy,
    ModelStrategy,
    ValidationStrategy,
    EvaluationStrategy,
    HPOStrategy,
    InterpretabilityStrategy,
    PipelineGenerationInput,
    RequiredComponents,
)
from app.modules.workflow_planning.context_builder import build_workflow_planning_context
from app.modules.workflow_planning.prompt_builder import build_prompt
from app.modules.workflow_planning.llm_client_adapter import WorkflowPlanningLLMAdapter
from app.modules.workflow_planning.parser import parse_llm_response
from app.modules.workflow_planning.validator import validate_workflow_plan
from app.modules.workflow_planning.builder import build_workflow_plan
from app.modules.workflow_planning.enums import WorkflowPlanStatus
from app.modules.workflow_planning.exceptions import (
    WorkflowPlanNotFoundException,
    UpstreamNotReadyException,
    WorkflowPlanningLLMCallException,
    WorkflowPlanParseException,
    WorkflowPlanValidationException,
)

logger = logging.getLogger(__name__)


class WorkflowPlanningService:

    def __init__(self):
        self.task_repo = TaskSpecificationRepository()
        self.plan_repo = WorkflowPlanRepository()
        self.llm_adapter = WorkflowPlanningLLMAdapter()

    def create_plan(
        self, session: Session, task_id: str, request: WorkflowPlanCreateRequest
    ) -> WorkflowPlanResponse:
        context = build_workflow_planning_context(session, task_id)

        system_prompt, user_message = build_prompt(context)

        llm_request_fallback = {
            "provider": self.llm_adapter.llm_client.provider,
            "model": self.llm_adapter.llm_client.model,
            "system_prompt": system_prompt,
            "user_message": user_message,
        }

        try:
            llm_result = self.llm_adapter.generate(system_prompt, user_message)
        except WorkflowPlanningLLMCallException:
            failed_plan = WorkflowPlan(
                id=f"plan_{__import__('uuid').uuid4().hex[:8]}",
                task_id=task_id,
                interpretation_id=context.get("interpretation_id"),
                dataset_profile_id=context.get("dataset_profile_id"),
                status=WorkflowPlanStatus.FAILED,
                planning_mode="llm_guided",
                llm_request_json=llm_request_fallback,
                error_message="LLM call failed.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.plan_repo.create(session, failed_plan)
            raise

        request_info = llm_result["request_info"]
        raw_response = llm_result["raw_response"]

        llm_request_json = {
            "provider": request_info["provider"],
            "model": request_info["model"],
            "system_prompt": system_prompt,
            "user_message": user_message,
        }
        llm_response_json = {"raw": raw_response}

        try:
            parsed_plan = parse_llm_response(raw_response)
        except WorkflowPlanParseException:
            failed_plan = WorkflowPlan(
                id=f"plan_{__import__('uuid').uuid4().hex[:8]}",
                task_id=task_id,
                interpretation_id=context.get("interpretation_id"),
                dataset_profile_id=context.get("dataset_profile_id"),
                status=WorkflowPlanStatus.FAILED,
                planning_mode="llm_guided",
                llm_request_json=llm_request_json,
                llm_response_json=llm_response_json,
                error_message="LLM output parse error.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.plan_repo.create(session, failed_plan)
            raise

        validation_result = validate_workflow_plan(parsed_plan)
        if not validation_result["is_valid"]:
            failed_plan = WorkflowPlan(
                id=f"plan_{__import__('uuid').uuid4().hex[:8]}",
                task_id=task_id,
                interpretation_id=context.get("interpretation_id"),
                dataset_profile_id=context.get("dataset_profile_id"),
                status=WorkflowPlanStatus.FAILED,
                planning_mode="llm_guided",
                llm_request_json=llm_request_json,
                llm_response_json=llm_response_json,
                error_message="; ".join(validation_result["errors"]),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.plan_repo.create(session, failed_plan)
            raise WorkflowPlanValidationException("; ".join(validation_result["errors"]))

        warnings = parsed_plan.get("planning_warnings", [])
        assumptions = parsed_plan.get("planning_assumptions", [])
        status = WorkflowPlanStatus.PLANNED_WITH_WARNING if (warnings or assumptions) else WorkflowPlanStatus.PLANNED

        plan_dict = build_workflow_plan(
            task_id=task_id,
            interpretation_id=context["interpretation_id"],
            dataset_profile_id=context["dataset_profile_id"],
            validated_plan=parsed_plan,
            llm_request=llm_request_json,
            llm_response=llm_response_json,
            status=status,
        )

        task_summary = plan_dict.get("task_summary", {})
        data_strategy = plan_dict.get("data_strategy", {})
        feature_strategy = plan_dict.get("feature_strategy", {})
        validation_strategy = plan_dict.get("validation_strategy", {})
        evaluation_strategy = plan_dict.get("evaluation_strategy", {})
        hpo_strategy = plan_dict.get("hpo_strategy", {})
        interpretability_strategy = plan_dict.get("interpretability_strategy", {})

        plan_model = WorkflowPlan(
            id=plan_dict["workflow_plan_id"],
            task_id=plan_dict["task_id"],
            interpretation_id=plan_dict["interpretation_id"],
            dataset_profile_id=plan_dict["dataset_profile_id"],
            status=plan_dict["status"],
            planning_mode=plan_dict["planning_mode"],
            task_type=task_summary.get("task_type"),
            input_modality=task_summary.get("input_modality"),
            primary_metric=evaluation_strategy.get("primary_metric"),
            feature_type=feature_strategy.get("feature_type"),
            validation_strategy=validation_strategy.get("split_strategy"),
            hpo_enabled=hpo_strategy.get("enabled", False),
            interpretability_enabled=interpretability_strategy.get("enabled", False),
            confidence_score=plan_dict["confidence_score"],
            plan_json=plan_dict,
            llm_request_json=llm_request_json,
            llm_response_json=llm_response_json,
            error_message=None,
            created_at=datetime.fromisoformat(plan_dict["created_at"]),
            updated_at=datetime.fromisoformat(plan_dict["updated_at"]),
        )

        created = self.plan_repo.create(session, plan_model)
        return self._to_response(created)

    def get_plan(self, session: Session, plan_id: str) -> WorkflowPlanResponse:
        plan = self.plan_repo.get_by_id(session, plan_id)
        if not plan:
            raise WorkflowPlanNotFoundException(
                f"Workflow plan with id {plan_id} not found."
            )
        return self._to_response(plan)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> WorkflowPlanResponse:
        self._check_task_exists(session, task_id)
        plan = self.plan_repo.get_latest_by_task_id(session, task_id)
        if not plan:
            raise WorkflowPlanNotFoundException(
                f"No workflow plan found for task {task_id}."
            )
        return self._to_response(plan)

    def rerun_plan(
        self, session: Session, task_id: str, request: WorkflowPlanCreateRequest
    ) -> WorkflowPlanResponse:
        return self.create_plan(session, task_id, request)

    def adopt_revised_plan(
        self, session: Session, task_id: str, revised_plan: dict
    ) -> WorkflowPlanResponse:
        self._check_task_exists(session, task_id)

        interp_repo = TaskInterpretationRepository()
        profile_repo = DatasetProfileRepository()

        interp = interp_repo.get_latest_by_task_id(session, task_id)
        profile = profile_repo.get_latest_by_task_id(session, task_id)

        interpretation_id = interp.id if interp else None
        dataset_profile_id = profile.id if profile else None

        plan_id = f"plan_{__import__('uuid').uuid4().hex[:8]}"
        now = datetime.now()

        plan_json = {
            "workflow_plan_id": plan_id,
            "task_id": task_id,
            "interpretation_id": interpretation_id,
            "dataset_profile_id": dataset_profile_id,
            "status": WorkflowPlanStatus.PLANNED,
            "planning_mode": "refinement_adopted",
            "task_summary": revised_plan.get("task_summary", {}),
            "data_strategy": revised_plan.get("data_strategy", {}),
            "feature_strategy": revised_plan.get("feature_strategy", {}),
            "model_strategy": revised_plan.get("model_strategy", {}),
            "validation_strategy": revised_plan.get("validation_strategy", {}),
            "evaluation_strategy": revised_plan.get("evaluation_strategy", {}),
            "hpo_strategy": revised_plan.get("hpo_strategy", {}),
            "interpretability_strategy": revised_plan.get("interpretability_strategy", {}),
            "pipeline_generation_input": revised_plan.get("pipeline_generation_input", {}),
            "planning_warnings": revised_plan.get("planning_warnings", []),
            "planning_assumptions": revised_plan.get("planning_assumptions", []),
            "llm_reasoning_summary": revised_plan.get("llm_reasoning_summary", ""),
            "confidence_score": revised_plan.get("confidence_score", 0.0),
            "refinement_metadata": revised_plan.get("refinement_metadata"),
            "llm_request": {},
            "llm_response": {},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        task_summary = plan_json.get("task_summary", {})
        feature_strategy = plan_json.get("feature_strategy", {})
        validation_strategy = plan_json.get("validation_strategy", {})
        evaluation_strategy = plan_json.get("evaluation_strategy", {})
        hpo_strategy = plan_json.get("hpo_strategy", {})
        interpretability_strategy = plan_json.get("interpretability_strategy", {})

        plan_model = WorkflowPlan(
            id=plan_id,
            task_id=task_id,
            interpretation_id=interpretation_id,
            dataset_profile_id=dataset_profile_id,
            status=WorkflowPlanStatus.PLANNED,
            planning_mode="refinement_adopted",
            task_type=task_summary.get("task_type"),
            input_modality=task_summary.get("input_modality"),
            primary_metric=evaluation_strategy.get("primary_metric"),
            feature_type=feature_strategy.get("feature_type"),
            validation_strategy=validation_strategy.get("split_strategy"),
            hpo_enabled=hpo_strategy.get("enabled", False),
            interpretability_enabled=interpretability_strategy.get("enabled", False),
            confidence_score=plan_json.get("confidence_score"),
            plan_json=plan_json,
            llm_request_json=None,
            llm_response_json=None,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        created = self.plan_repo.create(session, plan_model)
        logger.info(
            "Adopted revised plan %s for task %s from refinement", plan_id, task_id
        )
        return self._to_response(created)

    def _check_task_exists(self, session: Session, task_id: str):
        task_spec = self.task_repo.get_by_id(session, task_id)
        if not task_spec:
            from app.shared.common.exceptions import NotFoundException
            raise NotFoundException(f"Task specification with id {task_id} not found.")

    def _to_response(self, plan: WorkflowPlan) -> WorkflowPlanResponse:
        plan_json = plan.plan_json or {}

        task_summary_raw = plan_json.get("task_summary") or {}
        task_summary = TaskSummary(
            task_type=task_summary_raw.get("task_type"),
            input_modality=task_summary_raw.get("input_modality"),
            prediction_target=task_summary_raw.get("prediction_target"),
            material_domain=task_summary_raw.get("material_domain"),
            primary_goal=task_summary_raw.get("primary_goal"),
        )

        data_strategy_raw = plan_json.get("data_strategy") or {}
        target_handling_raw = data_strategy_raw.get("target_handling") or {}
        data_strategy = DataStrategy(
            input_columns=data_strategy_raw.get("input_columns", []),
            target_column=data_strategy_raw.get("target_column"),
            required_cleaning_steps=data_strategy_raw.get("required_cleaning_steps", []),
            target_handling=TargetHandling(
                requires_transformation_check=target_handling_raw.get("requires_transformation_check", False),
                recommended_transformation=target_handling_raw.get("recommended_transformation", "none"),
            ),
            duplicate_handling=data_strategy_raw.get("duplicate_handling", "none"),
            missing_value_strategy=data_strategy_raw.get("missing_value_strategy", "no_missing_values_detected"),
        )

        feature_strategy_raw = plan_json.get("feature_strategy") or {}
        feature_strategy = FeatureStrategy(
            feature_type=feature_strategy_raw.get("feature_type"),
            executable_featurizers=feature_strategy_raw.get("executable_featurizers", []),
            semantic_featurizers=feature_strategy_raw.get("semantic_featurizers", []),
            unsupported_future_featurizers=feature_strategy_raw.get("unsupported_future_featurizers", []),
            recommended_featurizers=feature_strategy_raw.get("recommended_featurizers", []),
            requires_structure_features=feature_strategy_raw.get("requires_structure_features", False),
            feature_selection_required=feature_strategy_raw.get("feature_selection_required", False),
            feature_scaling_required=feature_strategy_raw.get("feature_scaling_required", False),
        )

        model_strategy_raw = plan_json.get("model_strategy") or {}
        model_strategy = ModelStrategy(
            candidate_model_families=model_strategy_raw.get("candidate_model_families", []),
            baseline_models=model_strategy_raw.get("baseline_models", []),
            preferred_model_bias=model_strategy_raw.get("preferred_model_bias", "balance_accuracy_and_interpretability"),
            excluded_model_families=model_strategy_raw.get("excluded_model_families", []),
        )

        validation_strategy_raw = plan_json.get("validation_strategy") or {}
        validation_strategy = ValidationStrategy(
            split_strategy=validation_strategy_raw.get("split_strategy", "k_fold_cross_validation"),
            n_splits=validation_strategy_raw.get("n_splits", 5),
            test_size=validation_strategy_raw.get("test_size"),
            random_state=validation_strategy_raw.get("random_state", 42),
            stratification_required=validation_strategy_raw.get("stratification_required", False),
        )

        evaluation_strategy_raw = plan_json.get("evaluation_strategy") or {}
        evaluation_strategy = EvaluationStrategy(
            primary_metric=evaluation_strategy_raw.get("primary_metric"),
            secondary_metrics=evaluation_strategy_raw.get("secondary_metrics", []),
            metric_direction=evaluation_strategy_raw.get("metric_direction", "minimize"),
        )

        hpo_strategy_raw = plan_json.get("hpo_strategy") or {}
        hpo_strategy = HPOStrategy(
            enabled=hpo_strategy_raw.get("enabled", True),
            search_method=hpo_strategy_raw.get("search_method", "random_search"),
            budget_level=hpo_strategy_raw.get("budget_level", "medium"),
            max_trials=hpo_strategy_raw.get("max_trials", 30),
        )

        interpretability_strategy_raw = plan_json.get("interpretability_strategy") or {}
        interpretability_strategy = InterpretabilityStrategy(
            enabled=interpretability_strategy_raw.get("enabled", True),
            methods=interpretability_strategy_raw.get("methods", []),
            priority=interpretability_strategy_raw.get("priority", "medium"),
        )

        pipeline_input_raw = plan_json.get("pipeline_generation_input") or {}
        required_components_raw = pipeline_input_raw.get("required_components") or {}
        pipeline_generation_input = PipelineGenerationInput(
            pipeline_steps=pipeline_input_raw.get("pipeline_steps", []),
            required_components=RequiredComponents(
                data_cleaner=required_components_raw.get("data_cleaner", False),
                featurizer=required_components_raw.get("featurizer", False),
                model_trainer=required_components_raw.get("model_trainer", False),
                evaluator=required_components_raw.get("evaluator", False),
            ),
        )

        return WorkflowPlanResponse(
            workflow_plan_id=plan.id,
            task_id=plan.task_id or "",
            interpretation_id=plan.interpretation_id,
            dataset_profile_id=plan.dataset_profile_id,
            status=plan.status or WorkflowPlanStatus.PENDING,
            planning_mode=plan.planning_mode or "llm_guided",
            task_summary=task_summary,
            data_strategy=data_strategy,
            feature_strategy=feature_strategy,
            model_strategy=model_strategy,
            validation_strategy=validation_strategy,
            evaluation_strategy=evaluation_strategy,
            hpo_strategy=hpo_strategy,
            interpretability_strategy=interpretability_strategy,
            pipeline_generation_input=pipeline_generation_input,
            planning_warnings=plan_json.get("planning_warnings", []),
            planning_assumptions=plan_json.get("planning_assumptions", []),
            llm_reasoning_summary=plan_json.get("llm_reasoning_summary"),
            confidence_score=plan.confidence_score,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )
