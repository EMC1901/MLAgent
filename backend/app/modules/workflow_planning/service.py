import logging
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

from sqlmodel import Session

from app.shared.database.connection import engine
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
    PreprocessingIntent,
    WorkflowRationale,
    ExecutionHints,
    SelectedFeatureAction,
    RejectedFeatureAction,
    DecisionRationale,
    InputModalityAssessment,
    FallbackStrategy,
    FeatureGroupExpectation,
    ModelStrategy,
    ValidationStrategy,
    EvaluationStrategy,
    HPOStrategy,
    InterpretabilityStrategy,
    PipelineGenerationInput,
    RequiredComponents,
    FeatureStrategyResponse,
    FeatureStrategyRationaleResponse,
    ModelStrategyResponse,
    PreprocessingIntentResponse,
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

    @staticmethod
    @contextmanager
    def _new_session() -> Iterator[Session]:
        """Yield a fresh DB session for post-LLM writes.

        The request-scoped session is closed before the long-running LLM call
        to avoid idle-in-transaction connection drops.  Use this context
        manager for all DB writes that happen after the LLM returns.
        """
        with Session(engine) as s:
            yield s

    def _build_plan_model(self, plan_dict: dict, planning_mode: str) -> WorkflowPlan:
        """Construct a WorkflowPlan ORM model from a built plan dict."""
        return WorkflowPlan(
            id=plan_dict["workflow_plan_id"],
            task_id=plan_dict["task_id"],
            interpretation_id=plan_dict["interpretation_id"],
            dataset_profile_id=plan_dict["dataset_profile_id"],
            status=plan_dict["status"],
            planning_mode=planning_mode,
            task_type=(plan_dict.get("task_summary") or {}).get("task_type"),
            input_modality=(plan_dict.get("task_summary") or {}).get("input_modality"),
            primary_metric=(plan_dict.get("evaluation_strategy") or {}).get("primary_metric"),
            feature_type=(plan_dict.get("feature_strategy") or {}).get("feature_type"),
            validation_strategy=(plan_dict.get("validation_strategy") or {}).get("split_strategy"),
            hpo_enabled=(plan_dict.get("hpo_strategy") or {}).get("enabled", False),
            interpretability_enabled=(plan_dict.get("interpretability_strategy") or {}).get("enabled", False),
            confidence_score=plan_dict["confidence_score"],
            plan_json=plan_dict,
            llm_request_json=plan_dict.get("llm_request"),
            llm_response_json=plan_dict.get("llm_response"),
            fe_registry_snapshot_version=plan_dict.get("fe_registry_snapshot_version"),
            feature_strategy_json=plan_dict.get("feature_strategy"),
            model_strategy_json=plan_dict.get("model_strategy"),
            preprocessing_intent_json=plan_dict.get("preprocessing_intent"),
            workflow_rationale_json=plan_dict.get("workflow_rationale"),
            error_message=None,
            created_at=datetime.fromisoformat(plan_dict["created_at"]),
            updated_at=datetime.fromisoformat(plan_dict["updated_at"]),
        )

    def _save_failed_plan(
        self,
        task_id: str,
        context: dict,
        planning_mode: str,
        llm_request_json: dict | None,
        llm_response_json: dict | None,
        error_message: str,
    ):
        """Persist a failed plan record using a fresh session."""
        with self._new_session() as ws:
            failed_plan = WorkflowPlan(
                id=f"plan_{uuid.uuid4().hex[:8]}",
                task_id=task_id,
                interpretation_id=context.get("interpretation_id"),
                dataset_profile_id=context.get("dataset_profile_id"),
                status=WorkflowPlanStatus.FAILED,
                planning_mode=planning_mode,
                llm_request_json=llm_request_json,
                llm_response_json=llm_response_json,
                error_message=error_message,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.plan_repo.create(ws, failed_plan)

    def create_plan(
        self, session: Session, task_id: str, request: WorkflowPlanCreateRequest
    ) -> WorkflowPlanResponse:
        # ── Phase 1: read everything from the request-scoped session ──
        context = build_workflow_planning_context(session, task_id)
        system_prompt, user_message = build_prompt(context)
        llm_request_fallback = {
            "provider": self.llm_adapter.llm_client.provider,
            "model": self.llm_adapter.llm_client.model,
            "system_prompt": system_prompt,
            "user_message": user_message,
        }

        # ── Phase 2: release DB session before long-running LLM call ──
        session.close()

        # ── Phase 3: LLM call (no DB session held) ──
        logger.info("Workflow planning LLM call starting for task %s", task_id)
        try:
            llm_result = self.llm_adapter.generate(system_prompt, user_message)
        except WorkflowPlanningLLMCallException:
            logger.error("Workflow planning LLM call failed for task %s", task_id)
            self._save_failed_plan(
                task_id, context, "llm_guided",
                llm_request_fallback, None, "LLM call failed.",
            )
            raise

        request_info = llm_result["request_info"]
        raw_response = llm_result["raw_response"]
        logger.info("Workflow planning LLM call completed for task %s", task_id)

        llm_request_json = {
            "provider": request_info["provider"],
            "model": request_info["model"],
            "system_prompt": system_prompt,
            "user_message": user_message,
        }
        llm_response_json = {"raw": raw_response}

        # ── Phase 4: parse, validate, persist with a fresh session ──
        try:
            parsed_plan = parse_llm_response(raw_response)
        except WorkflowPlanParseException:
            self._save_failed_plan(
                task_id, context, "llm_guided",
                llm_request_json, llm_response_json, "LLM output parse error.",
            )
            raise

        validation_result = validate_workflow_plan(parsed_plan)
        if not validation_result["is_valid"]:
            self._save_failed_plan(
                task_id, context, "llm_guided",
                llm_request_json, llm_response_json,
                "; ".join(validation_result["errors"]),
            )
            raise WorkflowPlanValidationException("; ".join(validation_result["errors"]))

        warnings = parsed_plan.get("planning_warnings", [])
        assumptions = parsed_plan.get("planning_assumptions", [])
        plan_status = WorkflowPlanStatus.PLANNED_WITH_WARNING if (warnings or assumptions) else WorkflowPlanStatus.PLANNED

        plan_dict = build_workflow_plan(
            task_id=task_id,
            interpretation_id=context["interpretation_id"],
            dataset_profile_id=context["dataset_profile_id"],
            validated_plan=parsed_plan,
            llm_request=llm_request_json,
            llm_response=llm_response_json,
            status=plan_status,
        )

        plan_model = self._build_plan_model(plan_dict, planning_mode="llm_guided")

        with self._new_session() as ws:
            created = self.plan_repo.create(ws, plan_model)

        logger.info("Workflow plan %s created for task %s", created.id, task_id)
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

    def get_feature_strategy(self, session: Session, plan_id: str) -> FeatureStrategyResponse:
        plan = self.plan_repo.get_by_id(session, plan_id)
        if not plan:
            raise WorkflowPlanNotFoundException(f"Workflow plan with id {plan_id} not found.")
        plan_json = plan.plan_json or {}
        fs_raw = plan_json.get("feature_strategy") or {}
        feature_strategy_data = FeatureStrategy(**fs_raw) if fs_raw else FeatureStrategy()
        return FeatureStrategyResponse(
            workflow_plan_id=plan.id or "",
            feature_strategy=feature_strategy_data,
            fe_registry_snapshot_version=plan.fe_registry_snapshot_version,
        )

    def get_feature_strategy_rationale(self, session: Session, plan_id: str) -> FeatureStrategyRationaleResponse:
        plan = self.plan_repo.get_by_id(session, plan_id)
        if not plan:
            raise WorkflowPlanNotFoundException(f"Workflow plan with id {plan_id} not found.")
        plan_json = plan.plan_json or {}
        fs_raw = plan_json.get("feature_strategy") or {}
        selected_actions = fs_raw.get("selected_feature_actions", [])
        rationales = []
        for action in selected_actions:
            dr = action.get("decision_rationale", {})
            rationales.append(DecisionRationale(
                reason=dr.get("reason", ""),
                evidence=dr.get("evidence", []),
                material_science_basis=dr.get("material_science_basis", ""),
                expected_benefit=dr.get("expected_benefit", ""),
                risk=dr.get("risk", ""),
                fallback=dr.get("fallback", ""),
            ))
        rejected = [RejectedFeatureAction(**ra) for ra in fs_raw.get("rejected_feature_actions", [])]
        return FeatureStrategyRationaleResponse(
            workflow_plan_id=plan.id or "",
            rationales=rationales,
            rejected_rationales=rejected,
        )

    def get_preprocessing_intent(self, session: Session, plan_id: str) -> PreprocessingIntentResponse:
        plan = self.plan_repo.get_by_id(session, plan_id)
        if not plan:
            raise WorkflowPlanNotFoundException(f"Workflow plan with id {plan_id} not found.")
        plan_json = plan.plan_json or {}
        intent_raw = plan_json.get("preprocessing_intent") or {}
        intent = PreprocessingIntent(**intent_raw) if intent_raw else PreprocessingIntent()
        return PreprocessingIntentResponse(
            workflow_plan_id=plan.id or "",
            preprocessing_intent=intent,
        )

    def get_model_strategy(self, session: Session, plan_id: str) -> ModelStrategyResponse:
        plan = self.plan_repo.get_by_id(session, plan_id)
        if not plan:
            raise WorkflowPlanNotFoundException(f"Workflow plan with id {plan_id} not found.")
        plan_json = plan.plan_json or {}
        ms_raw = plan_json.get("model_strategy") or {}
        model_strategy_data = ModelStrategy(**ms_raw) if ms_raw else ModelStrategy()
        return ModelStrategyResponse(
            workflow_plan_id=plan.id or "",
            model_strategy=model_strategy_data,
        )

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

        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
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
            "preprocessing_intent": revised_plan.get("preprocessing_intent", {}),
            "model_strategy": revised_plan.get("model_strategy", {}),
            "validation_strategy": revised_plan.get("validation_strategy", {}),
            "evaluation_strategy": revised_plan.get("evaluation_strategy", {}),
            "hpo_strategy": revised_plan.get("hpo_strategy", {}),
            "interpretability_strategy": revised_plan.get("interpretability_strategy", {}),
            "iteration_guidance": revised_plan.get("iteration_guidance", {}),
            "pipeline_generation_input": revised_plan.get("pipeline_generation_input", {}),
            "workflow_rationale": revised_plan.get("workflow_rationale", {}),
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

        plan_model = WorkflowPlan(
            id=plan_id,
            task_id=task_id,
            interpretation_id=interpretation_id,
            dataset_profile_id=dataset_profile_id,
            status=WorkflowPlanStatus.PLANNED,
            planning_mode="refinement_adopted",
            plan_json=plan_json,
            fe_registry_snapshot_version=revised_plan.get("fe_registry_snapshot_version"),
            feature_strategy_json=revised_plan.get("feature_strategy"),
            model_strategy_json=revised_plan.get("model_strategy"),
            preprocessing_intent_json=revised_plan.get("preprocessing_intent"),
            workflow_rationale_json=revised_plan.get("workflow_rationale"),
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        created = self.plan_repo.create(session, plan_model)
        logger.info("Adopted revised plan %s for task %s", plan_id, task_id)
        return self._to_response(created)

    def rerun_with_iteration_guidance(
        self, session: Session, task_id: str, iteration_guidance: dict,
    ) -> WorkflowPlanResponse:
        logger.info("Rerunning WP LLM with iteration_guidance for task %s", task_id)

        # ── Phase 1: read everything from the request-scoped session ──
        context = build_workflow_planning_context(session, task_id)
        system_prompt, user_message = build_prompt(context, iteration_guidance=iteration_guidance)
        llm_request_fallback = {
            "provider": self.llm_adapter.llm_client.provider,
            "model": self.llm_adapter.llm_client.model,
            "system_prompt": system_prompt,
            "user_message": user_message,
        }

        # ── Phase 2: release DB session before long-running LLM call ──
        session.close()

        # ── Phase 3: LLM call (no DB session held) ──
        try:
            llm_result = self.llm_adapter.generate(system_prompt, user_message)
        except WorkflowPlanningLLMCallException:
            self._save_failed_plan(
                task_id, context, "iteration_rerun",
                llm_request_fallback, None,
                "LLM call failed during iteration rerun.",
            )
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

        # ── Phase 4: parse, validate, persist with a fresh session ──
        try:
            parsed_plan = parse_llm_response(raw_response)
        except WorkflowPlanParseException:
            self._save_failed_plan(
                task_id, context, "iteration_rerun",
                llm_request_json, llm_response_json,
                "LLM output parse error during iteration rerun.",
            )
            raise

        validation_result = validate_workflow_plan(parsed_plan)
        if not validation_result["is_valid"]:
            self._save_failed_plan(
                task_id, context, "iteration_rerun",
                llm_request_json, llm_response_json,
                "; ".join(validation_result["errors"]),
            )
            raise WorkflowPlanValidationException("; ".join(validation_result["errors"]))

        warnings = parsed_plan.get("planning_warnings", [])
        assumptions = parsed_plan.get("planning_assumptions", [])
        plan_status = WorkflowPlanStatus.PLANNED_WITH_WARNING if (warnings or assumptions) else WorkflowPlanStatus.PLANNED

        plan_dict = build_workflow_plan(
            task_id=task_id,
            interpretation_id=context["interpretation_id"],
            dataset_profile_id=context["dataset_profile_id"],
            validated_plan=parsed_plan,
            llm_request=llm_request_json,
            llm_response=llm_response_json,
            status=plan_status,
        )

        plan_model = self._build_plan_model(plan_dict, planning_mode="iteration_rerun")

        with self._new_session() as ws:
            created = self.plan_repo.create(ws, plan_model)

        logger.info("WP iteration rerun complete — plan %s for task %s", created.id, task_id)
        return self._to_response(created)

    def _check_task_exists(self, session: Session, task_id: str):
        task_spec = self.task_repo.get_by_id(session, task_id)
        if not task_spec:
            from app.shared.common.exceptions import NotFoundException
            raise NotFoundException(f"Task specification with id {task_id} not found.")

    def _to_response(self, plan: WorkflowPlan) -> WorkflowPlanResponse:
        plan_json = plan.plan_json or {}

        task_summary_raw = plan_json.get("task_summary") or {}
        task_summary = TaskSummary(**task_summary_raw) if task_summary_raw else TaskSummary()

        data_strategy_raw = plan_json.get("data_strategy") or {}
        target_handling_raw = data_strategy_raw.get("target_handling") or {}
        data_strategy = DataStrategy(
            input_columns=data_strategy_raw.get("input_columns", []),
            target_column=data_strategy_raw.get("target_column"),
            required_cleaning_steps=data_strategy_raw.get("required_cleaning_steps", []),
            target_handling=TargetHandling(**target_handling_raw) if target_handling_raw else TargetHandling(),
            duplicate_handling=data_strategy_raw.get("duplicate_handling", "none"),
            missing_value_strategy=data_strategy_raw.get("missing_value_strategy", "no_missing_values_detected"),
        )

        feature_strategy_raw = plan_json.get("feature_strategy") or {}
        feature_strategy = FeatureStrategy(**feature_strategy_raw) if feature_strategy_raw else FeatureStrategy()

        preprocessing_intent_raw = plan_json.get("preprocessing_intent") or {}
        preprocessing_intent = PreprocessingIntent(**preprocessing_intent_raw) if preprocessing_intent_raw else PreprocessingIntent()

        workflow_rationale_raw = plan_json.get("workflow_rationale") or {}
        workflow_rationale = WorkflowRationale(**workflow_rationale_raw) if workflow_rationale_raw else WorkflowRationale()

        model_strategy_raw = plan_json.get("model_strategy") or {}
        model_strategy = ModelStrategy(**model_strategy_raw) if model_strategy_raw else ModelStrategy()

        validation_strategy_raw = plan_json.get("validation_strategy") or {}
        validation_strategy = ValidationStrategy(**validation_strategy_raw) if validation_strategy_raw else ValidationStrategy()

        evaluation_strategy_raw = plan_json.get("evaluation_strategy") or {}
        evaluation_strategy = EvaluationStrategy(**evaluation_strategy_raw) if evaluation_strategy_raw else EvaluationStrategy()

        hpo_strategy_raw = plan_json.get("hpo_strategy") or {}
        hpo_strategy = HPOStrategy(**hpo_strategy_raw) if hpo_strategy_raw else HPOStrategy()

        interpretability_strategy_raw = plan_json.get("interpretability_strategy") or {}
        interpretability_strategy = InterpretabilityStrategy(**interpretability_strategy_raw) if interpretability_strategy_raw else InterpretabilityStrategy()

        pipeline_input_raw = plan_json.get("pipeline_generation_input") or {}
        pipeline_generation_input = PipelineGenerationInput(
            pipeline_steps=pipeline_input_raw.get("pipeline_steps", []),
            required_components=RequiredComponents(**pipeline_input_raw.get("required_components", {})),
        )

        execution_hints_raw = plan_json.get("execution_hints") or {}
        execution_hints = ExecutionHints(**execution_hints_raw) if execution_hints_raw else None

        return WorkflowPlanResponse(
            workflow_plan_id=plan.id or "",
            task_id=plan.task_id or "",
            interpretation_id=plan.interpretation_id,
            dataset_profile_id=plan.dataset_profile_id,
            status=plan.status or WorkflowPlanStatus.PENDING,
            planning_mode=plan.planning_mode or "llm_guided",
            task_summary=task_summary,
            data_strategy=data_strategy,
            feature_strategy=feature_strategy,
            preprocessing_intent=preprocessing_intent,
            model_strategy=model_strategy,
            validation_strategy=validation_strategy,
            evaluation_strategy=evaluation_strategy,
            hpo_strategy=hpo_strategy,
            interpretability_strategy=interpretability_strategy,
            pipeline_generation_input=pipeline_generation_input,
            workflow_rationale=workflow_rationale,
            execution_hints=execution_hints,
            fe_registry_snapshot_version=plan.fe_registry_snapshot_version,
            planning_warnings=plan_json.get("planning_warnings", []),
            planning_assumptions=plan_json.get("planning_assumptions", []),
            llm_reasoning_summary=plan_json.get("llm_reasoning_summary"),
            confidence_score=plan.confidence_score,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )
