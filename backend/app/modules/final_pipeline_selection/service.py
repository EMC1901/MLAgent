import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Session

from app.modules.final_pipeline_selection.model import FinalPipelineSelection
from app.modules.final_pipeline_selection.repository import FinalPipelineSelectionRepository
from app.modules.final_pipeline_selection.schemas import (
    FinalPipelineSelectionCreateRequest,
    FinalPipelineSelectionResponse,
)
from app.modules.final_pipeline_selection.enums import (
    FinalPipelineSelectionStatus,
    CandidateStatus,
)

from app.modules.final_pipeline_selection.context_builder import build_final_selection_context
from app.modules.final_pipeline_selection.selection_input_loader import (
    load_final_pipeline_selection_input,
)
from app.modules.final_pipeline_selection.candidate_collector import collect_candidate_experiments
from app.modules.final_pipeline_selection.candidate_validator import validate_candidates
from app.modules.final_pipeline_selection.selection_policy_builder import build_selection_policy
from app.modules.final_pipeline_selection.constraint_checker import check_constraints
from app.modules.final_pipeline_selection.candidate_scorer import score_candidates
from app.modules.final_pipeline_selection.final_ranker import rank_candidates, select_final_pipeline
from app.modules.final_pipeline_selection.artifact_resolver import resolve_final_artifacts
from app.modules.final_pipeline_selection.selection_reason_builder import build_system_selection_reason
from app.modules.final_pipeline_selection.llm_selection_prompt_builder import (
    build_llm_selection_explanation_context,
)
from app.modules.final_pipeline_selection.llm_selection_explainer import LLMSelectionExplainer
from app.modules.final_pipeline_selection.llm_selection_explanation_parser import (
    parse_llm_selection_explanation,
)
from app.modules.final_pipeline_selection.llm_selection_explanation_validator import (
    validate_llm_selection_explanation,
)
from app.modules.final_pipeline_selection.llm_selection_explanation_normalizer import (
    normalize_llm_selection_explanation,
)
from app.modules.final_pipeline_selection.interpretability_input_builder import (
    build_interpretability_analysis_input,
)
from app.modules.final_pipeline_selection.final_selection_artifact_manager import (
    save_selection_artifacts,
)
from app.modules.final_pipeline_selection.builder import build_response

from app.modules.final_pipeline_selection.exceptions import (
    FinalPipelineSelectionNotFoundException,
    CandidateValidationException,
    FinalRankingException,
)

logger = logging.getLogger(__name__)


class FinalPipelineSelectionService:

    def __init__(self):
        self.repo = FinalPipelineSelectionRepository()
        self.llm_explainer = LLMSelectionExplainer()

    def create_final_selection(
        self,
        session: Session,
        task_id: str,
        request: FinalPipelineSelectionCreateRequest,
    ) -> FinalPipelineSelectionResponse:
        warnings_list: list = []

        # Step 1: Build context & validate upstream WorkflowRefinement
        wr = build_final_selection_context(
            session, task_id, request.workflow_refinement_id
        )

        # If not force_rerun, check for existing selection
        if not request.force_rerun:
            existing = self.repo.get_latest_by_task_id(session, task_id)
            if existing and existing.workflow_refinement_id == wr.id and existing.status in (
                FinalPipelineSelectionStatus.SELECTED,
                FinalPipelineSelectionStatus.SELECTED_WITH_WARNING,
            ):
                return self.get_final_selection(session, existing.id)

        # Step 2: Load final_pipeline_selection_input
        selection_input = load_final_pipeline_selection_input(wr)

        # Step 3: Collect candidates
        candidates, metric_evals, pipeline_execs = collect_candidate_experiments(
            session, selection_input
        )

        # Step 4: Validate candidates
        candidates = validate_candidates(
            candidates,
            require_model_artifact=request.require_model_artifact,
            require_prediction_artifact=request.require_prediction_artifact,
        )

        # Step 5: Build selection policy
        policy = build_selection_policy(request, selection_input.selection_policy)

        # Step 6: Check constraints
        constraint_result = check_constraints(
            candidates, policy, selection_input.constraints
        )

        # Determine task metadata for scoring
        best_me = _get_best_metric_evaluation(metric_evals, selection_input)
        metric_direction = best_me.metric_direction if best_me else "minimize"
        primary_metric = best_me.primary_metric if best_me else ""
        task_type = best_me.task_type if best_me else ""
        target_column = best_me.target_column if best_me else ""

        # Step 7: Score candidates
        candidates = score_candidates(candidates, policy, metric_direction)

        # Early check for zero eligible candidates
        eligible_now = [c for c in candidates if c.candidate_status == CandidateStatus.ELIGIBLE]
        if not eligible_now:
            rejected_info = [
                f"{c.candidate_id or '?'}({c.model_id or '?'}): {c.rejection_reason}"
                for c in candidates if c.candidate_status == CandidateStatus.REJECTED
            ]
            error_msg = (
                f"No eligible candidates remain after scoring/constraints. "
                f"Total: {len(candidates)}, rejected: {len(rejected_info)}. "
                f"Rejections: {'; '.join(rejected_info[:5])}"
            )
            logger.error(error_msg)
            return _build_failed_response(
                session, task_id, wr.id, policy, error_msg, warnings_list
            )

        # Step 8: Rank and select final
        try:
            candidates = rank_candidates(candidates, selection_input.current_best_trial_id)
            final_pipeline = select_final_pipeline(candidates)
        except Exception as e:
            logger.error("Ranking/selection failed: %s", str(e))
            return _build_failed_response(
                session, task_id, wr.id, policy, str(e), warnings_list
            )

        # Record the sources
        source_me_id = final_pipeline.source_metric_evaluation_id
        source_pe_id = final_pipeline.source_pipeline_execution_id
        source_pg_id = final_pipeline.source_pipeline_generation_id

        # Step 9: Resolve artifacts
        try:
            artifact_manifest = resolve_final_artifacts(session, final_pipeline, request)
        except Exception as e:
            logger.warning("Artifact resolution issue: %s", str(e))
            artifact_manifest = None
            warnings_list.append(f"Artifact resolution: {str(e)}")

        # Step 10: Build system selection reason
        system_reason = build_system_selection_reason(
            final_pipeline, candidates, policy, primary_metric
        )

        # Step 11-13: LLM explanation
        llm_explanation = None
        llm_raw_request = None
        llm_raw_response = None
        llm_used = False
        llm_confidence = None

        if request.use_llm_explainer:
            try:
                # Build prompt context
                prompt_ctx = build_llm_selection_explanation_context(
                    final_pipeline=final_pipeline,
                    candidates=candidates,
                    policy=policy,
                    system_reason=system_reason,
                    constraint_result=constraint_result,
                    artifact_manifest=artifact_manifest,
                    task_type=task_type,
                    target_column=target_column,
                    primary_metric=primary_metric,
                    metric_direction=metric_direction,
                )
                llm_raw_request = prompt_ctx

                # Call LLM
                llm_result = self.llm_explainer.explain(
                    prompt_ctx["system_prompt"], prompt_ctx["user_message"]
                )
                raw_response = llm_result.get("raw_response", "")
                llm_raw_response = raw_response

                # Parse
                llm_explanation = parse_llm_selection_explanation(raw_response)

                # Validate
                validation = validate_llm_selection_explanation(llm_explanation, raw_response)

                if validation.is_valid:
                    # Normalize
                    llm_explanation = normalize_llm_selection_explanation(llm_explanation)
                    llm_used = True
                    llm_confidence = llm_explanation.confidence_level if llm_explanation else None
                else:
                    logger.warning("LLM explanation validation failed: %s", validation.issues)
                    llm_explanation = None
                    warnings_list.append(
                        f"LLM explanation validation failed: {'; '.join(validation.issues)}"
                    )

            except Exception as e:
                logger.error("LLM explanation failed: %s", str(e))
                warnings_list.append(f"LLM explanation failed: {str(e)}")

        # Step 12: Build interpretability analysis input
        interpretability_input = None
        ready_for_ia = False
        if artifact_manifest:
            try:
                selected_final = None
                for c in candidates:
                    if c.is_final_selected:
                        selected_final = c
                        break
                primary_val = selected_final.primary_metric_value if selected_final else None

                interpretability_input = build_interpretability_analysis_input(
                    session=session,
                    final_pipeline=final_pipeline,
                    artifact_manifest=artifact_manifest,
                    system_reason=system_reason,
                    task_id=task_id,
                    final_selection_id="",  # Will be replaced after persist
                    task_type=task_type,
                    target_column=target_column,
                    primary_metric=primary_metric,
                    primary_metric_value=primary_val,
                )
                ready_for_ia = True
            except Exception as e:
                logger.warning("Interpretability input build failed: %s", str(e))
                warnings_list.append(f"Interpretability input: {str(e)}")

        # Determine status
        status = FinalPipelineSelectionStatus.SELECTED
        if warnings_list:
            status = FinalPipelineSelectionStatus.SELECTED_WITH_WARNING

        # Persist
        fps_id = f"fps_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        selected_final = None
        for c in candidates:
            if c.is_final_selected:
                selected_final = c
                break

        record = FinalPipelineSelection(
            id=fps_id,
            task_id=task_id,
            workflow_refinement_id=wr.id,
            metric_evaluation_id=source_me_id,
            pipeline_execution_id=source_pe_id,
            pipeline_generation_id=source_pg_id,
            status=status,
            selection_profile=policy.selection_profile,
            final_pipeline_spec_id=final_pipeline.final_pipeline_spec_id,
            final_model_id=final_pipeline.final_model_id,
            final_model_family=final_pipeline.final_model_family,
            final_trial_id=final_pipeline.final_trial_id,
            primary_metric=primary_metric,
            primary_metric_value=selected_final.primary_metric_value if selected_final else None,
            selection_score=selected_final.selection_score if selected_final else None,
            ready_for_interpretability_analysis=ready_for_ia,
            llm_used=llm_used,
            llm_confidence_level=llm_confidence,
            selection_json=_safe_dump(final_pipeline),
            candidate_ranking_json=_safe_dump(candidates),
            system_selection_reason_json=_safe_dump(system_reason),
            llm_selection_explanation_json=_safe_dump(llm_explanation),
            candidate_difference_summary_json=_safe_dump(
                llm_explanation.candidate_difference_summary if llm_explanation else None
            ),
            human_review_notes_json=_safe_dump(
                llm_explanation.human_review_notes if llm_explanation else None
            ),
            risk_notes_json=_safe_dump(
                llm_explanation.risk_notes if llm_explanation else None
            ),
            interpretability_analysis_input_json=_safe_dump(interpretability_input),
            artifact_manifest_json=_safe_dump(artifact_manifest),
            llm_request_json=_safe_dump(llm_raw_request),
            llm_response_json=_safe_dump({"raw_response": llm_raw_response} if llm_raw_response else None),
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        record = self.repo.create(session, record)

        # Update interpretability input with real ID
        if interpretability_input:
            interpretability_input.final_pipeline_selection_id = fps_id
            record.interpretability_analysis_input_json = _safe_dump(interpretability_input)
            record = self.repo.update(session, record)

        # Save artifacts
        final_selection_result = _safe_dump(record)
        save_selection_artifacts(
            final_selection_id=fps_id,
            final_selection_result=final_selection_result if isinstance(final_selection_result, dict) else {},
            candidate_ranking=candidates,
            selection_policy=policy,
            constraint_check_result=constraint_result,
            system_selection_reason=system_reason,
            llm_explanation=llm_explanation,
            final_artifact_manifest=artifact_manifest,
            interpretability_input=interpretability_input,
        )

        return build_response(
            record=record,
            final_pipeline=final_pipeline,
            candidate_ranking=candidates,
            selection_policy=policy,
            constraint_check_result=constraint_result,
            system_selection_reason=system_reason,
            llm_selection_explanation=llm_explanation,
            candidate_difference_summary=(
                llm_explanation.candidate_difference_summary if llm_explanation else None
            ),
            human_review_notes=(
                llm_explanation.human_review_notes if llm_explanation else None
            ),
            risk_notes=llm_explanation.risk_notes if llm_explanation else None,
            final_artifact_manifest=artifact_manifest,
            interpretability_analysis_input=interpretability_input,
            warnings=warnings_list,
            metric_direction=metric_direction,
            secondary_metrics=selected_final.hyperparameters if selected_final else {},
        )

    def get_final_selection(
        self, session: Session, fps_id: str
    ) -> FinalPipelineSelectionResponse:
        record = self.repo.get_by_id(session, fps_id)
        if not record:
            raise FinalPipelineSelectionNotFoundException(
                f"FinalPipelineSelection {fps_id} not found."
            )
        return self._record_to_response(record)

    def get_latest_by_task_id(
        self, session: Session, task_id: str
    ) -> FinalPipelineSelectionResponse:
        record = self.repo.get_latest_by_task_id(session, task_id)
        if not record:
            raise FinalPipelineSelectionNotFoundException(
                f"No FinalPipelineSelection found for task {task_id}."
            )
        return self._record_to_response(record)

    def rerun_final_selection(
        self, session: Session, task_id: str
    ) -> FinalPipelineSelectionResponse:
        request = FinalPipelineSelectionCreateRequest(force_rerun=True)
        return self.create_final_selection(session, task_id, request)

    def get_candidate_ranking(
        self, session: Session, fps_id: str
    ) -> dict:
        record = self.repo.get_by_id(session, fps_id)
        if not record:
            raise FinalPipelineSelectionNotFoundException(
                f"FinalPipelineSelection {fps_id} not found."
            )
        return record.candidate_ranking_json or {}

    def get_llm_explanation(
        self, session: Session, fps_id: str
    ) -> dict:
        record = self.repo.get_by_id(session, fps_id)
        if not record:
            raise FinalPipelineSelectionNotFoundException(
                f"FinalPipelineSelection {fps_id} not found."
            )
        return record.llm_selection_explanation_json or {}

    def get_artifact_manifest(
        self, session: Session, fps_id: str
    ) -> dict:
        record = self.repo.get_by_id(session, fps_id)
        if not record:
            raise FinalPipelineSelectionNotFoundException(
                f"FinalPipelineSelection {fps_id} not found."
            )
        return record.artifact_manifest_json or {}

    def get_interpretability_analysis_input(
        self, session: Session, fps_id: str
    ) -> dict:
        record = self.repo.get_by_id(session, fps_id)
        if not record:
            raise FinalPipelineSelectionNotFoundException(
                f"FinalPipelineSelection {fps_id} not found."
            )
        return record.interpretability_analysis_input_json or {}

    def _record_to_response(self, record: FinalPipelineSelection) -> FinalPipelineSelectionResponse:
        return build_response(
            record=record,
            candidate_ranking=_deserialize_candidates(record.candidate_ranking_json),
            system_selection_reason=_deserialize_obj(
                record.system_selection_reason_json
            ),
            llm_selection_explanation=_deserialize_obj(
                record.llm_selection_explanation_json
            ),
            final_artifact_manifest=_deserialize_obj(
                record.artifact_manifest_json
            ),
            interpretability_analysis_input=_deserialize_obj(
                record.interpretability_analysis_input_json
            ),
        )


def _build_failed_response(
    session: Session,
    task_id: str,
    wr_id: str,
    policy,
    error_message: str,
    warnings_list: list,
) -> FinalPipelineSelectionResponse:
    """Build and persist a response for a failed selection."""
    now = datetime.now(timezone.utc)
    fps_id = f"fps_{uuid.uuid4().hex[:8]}"

    record = FinalPipelineSelection(
        id=fps_id,
        task_id=task_id,
        workflow_refinement_id=wr_id,
        status=FinalPipelineSelectionStatus.FAILED,
        selection_profile=policy.selection_profile if policy else "balanced",
        error_message=error_message,
        created_at=now,
        updated_at=now,
    )
    repo = FinalPipelineSelectionRepository()
    record = repo.create(session, record)

    return FinalPipelineSelectionResponse(
        final_pipeline_selection_id=record.id,
        task_id=task_id,
        workflow_refinement_id=wr_id,
        status=FinalPipelineSelectionStatus.FAILED,
        selection_profile=policy.selection_profile if policy else "balanced",
        error_message=error_message,
        warnings=warnings_list,
        created_at=now,
        updated_at=now,
    )


def _get_best_metric_evaluation(metric_evals, selection_input):
    if selection_input.best_metric_evaluation_id:
        for me in metric_evals:
            if me.id == selection_input.best_metric_evaluation_id:
                return me
    return metric_evals[0] if metric_evals else None


def _safe_dump(obj) -> Optional[dict]:
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, list):
        return [_safe_dump(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _safe_dump(v) for k, v in obj.items()}
    return obj


def _deserialize_obj(data):
    if data is None:
        return None
    return data


def _deserialize_candidates(data):
    if data is None:
        return None
    if isinstance(data, list):
        from app.modules.final_pipeline_selection.schemas import CandidateSelectionItem
        return [CandidateSelectionItem(**item) if isinstance(item, dict) else item for item in data]
    return data
