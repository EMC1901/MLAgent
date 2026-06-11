import logging
import uuid
from datetime import datetime
from sqlmodel import Session

from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.pipeline_generation.model import PipelineGeneration
from app.modules.pipeline_generation.repository import PipelineGenerationRepository
from app.modules.pipeline_generation.schemas import (
    PipelineGenerationCreateRequest,
    PipelineGenerationResponse,
    PipelineGenerationSummaryResponse,
)
from app.modules.pipeline_generation.context_builder import build_pipeline_generation_context
from app.modules.pipeline_generation.artifact_resolver import resolve_artifacts
from app.modules.pipeline_generation.component_binder import bind_components
from app.modules.pipeline_generation.pipeline_spec_builder import build_pipeline_specs
from app.modules.pipeline_generation.trial_plan_builder import build_trial_plan
from app.modules.pipeline_generation.pipeline_validator import validate_pipeline_bundle
from app.modules.pipeline_generation.safety_checker import check_pipeline_safety
from app.modules.pipeline_generation.llm_review_prompt_builder import build_llm_review_prompt
from app.modules.pipeline_generation.llm_pipeline_reviewer import LLMPipelineReviewer
from app.modules.pipeline_generation.llm_review_parser import parse_llm_review_response
from app.modules.pipeline_generation.llm_review_validator import validate_llm_review
from app.modules.pipeline_generation.llm_review_normalizer import normalize_llm_review
from app.modules.pipeline_generation.execution_input_builder import build_execution_input
from app.modules.pipeline_generation.builder import (
    build_pipeline_bundle,
    build_pipeline_generation_response,
)
from app.modules.pipeline_generation.enums import PipelineGenerationStatus
from app.modules.pipeline_generation.exceptions import (
    PipelineGenerationNotFoundException,
    ModelSearchContextRequiredException,
    ModelSearchContextNotReadyException,
    PipelineGenerationInputMissingException,
    ArtifactResolveException,
    ComponentBindingException,
    PipelineSpecBuildException,
    PipelineValidationException,
    PipelineSafetyException,
    LLMPipelineReviewException,
    ExecutionInputBuildException,
)

logger = logging.getLogger(__name__)


class PipelineGenerationService:

    def __init__(self):
        self.task_repo = TaskSpecificationRepository()
        self.repo = PipelineGenerationRepository()
        self.llm_reviewer = LLMPipelineReviewer()

    def create_pipeline_generation(
        self, session: Session, task_id: str, request: PipelineGenerationCreateRequest,
    ) -> PipelineGenerationResponse:
        pg_id = f"pg_{uuid.uuid4().hex[:8]}"
        bundle_id = f"bundle_{uuid.uuid4().hex[:8]}"
        all_warnings = []
        all_errors = []

        # --- 1. Build upstream context ---
        try:
            context = build_pipeline_generation_context(session, task_id)
        except (
            ModelSearchContextRequiredException,
            ModelSearchContextNotReadyException,
            PipelineGenerationInputMissingException,
        ) as e:
            failed = PipelineGeneration(
                id=pg_id,
                task_id=task_id,
                status=PipelineGenerationStatus.FAILED,
                error_message=str(e.message),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.repo.create(session, failed)
            raise

        # --- 2. Resolve artifacts ---
        try:
            artifact_manifest = resolve_artifacts(context)
        except ArtifactResolveException as e:
            all_errors.append(f"Artifact resolve: {e.message}")
            failed = PipelineGeneration(
                id=pg_id,
                task_id=task_id,
                model_search_context_id=context.get("model_search_context_id"),
                feature_preprocessing_id=context.get("feature_preprocessing_id"),
                status=PipelineGenerationStatus.FAILED,
                task_type=context.get("task_type"),
                target_column=context.get("target_column"),
                primary_metric=context.get("primary_metric"),
                error_message=e.message,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.repo.create(session, failed)
            raise

        # --- 3. Bind components ---
        try:
            component_binding_result = bind_components(context)
        except ComponentBindingException as e:
            all_errors.append(f"Component binding: {e.message}")
            raise

        if component_binding_result.errors:
            all_warnings.extend(component_binding_result.errors)

        # --- 4. Build pipeline specs ---
        include_baselines = request.include_baselines
        include_hpo = request.include_hpo_candidates

        try:
            pipeline_specs = build_pipeline_specs(
                context,
                include_baselines=include_baselines,
                include_hpo=include_hpo,
            )
        except PipelineSpecBuildException as e:
            all_errors.append(f"Pipeline spec build: {e.message}")
            failed = PipelineGeneration(
                id=pg_id,
                task_id=task_id,
                model_search_context_id=context.get("model_search_context_id"),
                feature_preprocessing_id=context.get("feature_preprocessing_id"),
                status=PipelineGenerationStatus.FAILED,
                task_type=context.get("task_type"),
                target_column=context.get("target_column"),
                primary_metric=context.get("primary_metric"),
                error_message=e.message,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.repo.create(session, failed)
            raise

        # --- 5. Build trial plan ---
        trial_plan = build_trial_plan(context, pipeline_specs)

        # --- 6. Validate pipeline ---
        validation_result = validate_pipeline_bundle(
            context, pipeline_specs, trial_plan, artifact_manifest, component_binding_result,
        )
        if validation_result.warnings:
            all_warnings.extend(validation_result.warnings)
        if validation_result.errors:
            all_errors.extend(validation_result.errors)

        # --- 7. Safety check ---
        safety_check_result = check_pipeline_safety(
            context, pipeline_specs, None,
        )
        if safety_check_result.errors:
            all_errors.extend(safety_check_result.errors)
        if safety_check_result.warnings:
            all_warnings.extend(safety_check_result.warnings)

        # --- 8. Optional LLM advisory review ---
        llm_advisory_review = None
        llm_request_json = None
        llm_response_json = None
        llm_confidence_score = 0.0
        llm_review_used = request.use_llm_reviewer

        if request.use_llm_reviewer:
            try:
                iteration_guidance = context.get("iteration_guidance")
                prompt_data = build_llm_review_prompt(
                    context, pipeline_specs, trial_plan, validation_result,
                    iteration_guidance=iteration_guidance,
                )
                llm_request_json = {
                    "system_prompt": prompt_data["system_prompt"],
                    "user_message": prompt_data["user_message"],
                }
                llm_result = self.llm_reviewer.review(
                    prompt_data["system_prompt"],
                    prompt_data["user_message"],
                )
                llm_response_json = {"raw": llm_result["raw_response"]}

                # Parse raw LLM JSON
                parsed_data = parse_llm_review_response(llm_result["raw_response"])

                # Validate (code scan, forbidden fields check)
                llm_validation = validate_llm_review(parsed_data, pipeline_specs)
                if not llm_validation["is_valid"]:
                    all_warnings.append(
                        f"LLM advisory review partially rejected: "
                        + "; ".join(llm_validation["errors"])
                    )
                if llm_validation.get("warnings"):
                    all_warnings.extend(llm_validation["warnings"])

                # Normalize to standard LLMAdvisoryReview
                llm_advisory_review = normalize_llm_review(parsed_data)

                # Map confidence_level to numeric for DB column
                level_map = {"low": 0.3, "medium": 0.6, "high": 0.9}
                llm_confidence_score = level_map.get(
                    llm_advisory_review.confidence_level, 0.0
                )

                if llm_advisory_review.normalization_notes:
                    all_warnings.extend(llm_advisory_review.normalization_notes)

            except LLMPipelineReviewException as e:
                all_warnings.append(f"LLM advisory review skipped: {e.message}")
                llm_review_used = False

        # --- 9. Build execution input ---
        try:
            execution_input = build_execution_input(
                context, pg_id, bundle_id,
                pipeline_specs, trial_plan,
                validation_result, safety_check_result,
            )
        except ExecutionInputBuildException as e:
            all_errors.append(f"Execution input build: {e.message}")
            execution_input = None

        # --- 10. Build pipeline bundle ---
        pipeline_bundle = build_pipeline_bundle(
            bundle_id, context, pipeline_specs, trial_plan,
        )

        # --- 11. Build response ---
        response = build_pipeline_generation_response(
            pg_id=pg_id,
            context=context,
            pipeline_bundle=pipeline_bundle,
            pipeline_specs=pipeline_specs,
            trial_plan=trial_plan,
            component_binding_result=component_binding_result,
            artifact_manifest=artifact_manifest,
            validation_result=validation_result,
            safety_check_result=safety_check_result,
            llm_advisory_review=llm_advisory_review,
            execution_input=execution_input,
            use_llm_reviewer=llm_review_used,
            warnings=all_warnings,
            errors=all_errors,
        )

        # --- 12. Persist ---
        n_baseline = sum(1 for s in pipeline_specs if hasattr(s, 'pipeline_role') and s.pipeline_role == "baseline")
        n_hpo = sum(1 for s in pipeline_specs if hasattr(s, 'hpo_enabled') and s.hpo_enabled)

        record = PipelineGeneration(
            id=pg_id,
            task_id=context.get("task_id"),
            model_search_context_id=context.get("model_search_context_id"),
            feature_preprocessing_id=context.get("feature_preprocessing_id"),
            status=response.status,
            generation_mode=response.generation_mode,
            task_type=context.get("task_type"),
            target_column=context.get("target_column"),
            primary_metric=context.get("primary_metric"),
            n_pipeline_specs=len(pipeline_specs),
            n_baseline_specs=n_baseline,
            n_hpo_specs=n_hpo,
            hpo_enabled=trial_plan.hpo_enabled if trial_plan else False,
            ready_for_execution=response.ready_for_execution,
            llm_review_used=llm_review_used,
            llm_confidence_score=llm_confidence_score,
            pipeline_json=response.model_dump(mode='json'),
            execution_input_json=execution_input.model_dump(mode='json') if execution_input else None,
            llm_request_json=llm_request_json,
            llm_response_json=llm_response_json,
            error_message=response.error_message,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.repo.create(session, record)

        return response

    def get_pipeline_generation(
        self, session: Session, pg_id: str,
    ) -> PipelineGenerationResponse:
        record = self.repo.get_by_id(session, pg_id)
        if not record:
            raise PipelineGenerationNotFoundException(
                f"Pipeline generation with id {pg_id} not found."
            )
        return self._to_response(record)

    def get_latest_by_task_id(
        self, session: Session, task_id: str,
    ) -> PipelineGenerationResponse:
        self._check_task_exists(session, task_id)
        record = self.repo.get_latest_by_task_id(session, task_id)
        if not record:
            raise PipelineGenerationNotFoundException(
                f"No pipeline generation found for task {task_id}."
            )
        return self._to_response(record)

    def rerun_pipeline_generation(
        self, session: Session, task_id: str,
    ) -> PipelineGenerationResponse:
        request = PipelineGenerationCreateRequest(force_rerun=True)
        return self.create_pipeline_generation(session, task_id, request)

    def get_summary(
        self, session: Session, pg_id: str,
    ) -> PipelineGenerationSummaryResponse:
        record = self.repo.get_by_id(session, pg_id)
        if not record:
            raise PipelineGenerationNotFoundException(
                f"Pipeline generation with id {pg_id} not found."
            )
        pipeline_json = record.pipeline_json or {}
        return PipelineGenerationSummaryResponse(
            pipeline_generation_id=record.id or "",
            task_id=record.task_id or "",
            status=record.status or "",
            n_pipeline_specs=record.n_pipeline_specs or 0,
            n_baseline_specs=record.n_baseline_specs or 0,
            n_hpo_specs=record.n_hpo_specs or 0,
            hpo_enabled=record.hpo_enabled or False,
            ready_for_execution=record.ready_for_execution or False,
            warnings=pipeline_json.get("warnings", []),
            created_at=record.created_at,
        )

    def get_execution_input(
        self, session: Session, pg_id: str,
    ) -> dict:
        record = self.repo.get_by_id(session, pg_id)
        if not record:
            raise PipelineGenerationNotFoundException(
                f"Pipeline generation with id {pg_id} not found."
            )
        if not record.execution_input_json:
            raise PipelineGenerationNotFoundException(
                "Execution input not available for this pipeline generation."
            )
        return record.execution_input_json

    def _check_task_exists(self, session: Session, task_id: str):
        task_spec = self.task_repo.get_by_id(session, task_id)
        if not task_spec:
            from app.shared.common.exceptions import NotFoundException
            raise NotFoundException(f"Task specification with id {task_id} not found.")

    def _to_response(self, record: PipelineGeneration) -> PipelineGenerationResponse:
        if record.pipeline_json:
            try:
                return PipelineGenerationResponse(**record.pipeline_json)
            except Exception:
                pass

        return PipelineGenerationResponse(
            pipeline_generation_id=record.id or "",
            task_id=record.task_id or "",
            model_search_context_id=record.model_search_context_id,
            feature_preprocessing_id=record.feature_preprocessing_id,
            status=record.status or "pending",
            generation_mode=record.generation_mode,
            n_pipeline_specs=record.n_pipeline_specs or 0,
            n_baseline_specs=record.n_baseline_specs or 0,
            n_hpo_specs=record.n_hpo_specs or 0,
            error_message=record.error_message,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
