import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Session

from app.modules.workflow_refinement.model import WorkflowRefinement
from app.modules.workflow_refinement.repository import WorkflowRefinementRepository
from app.modules.workflow_refinement.schemas import (
    WorkflowRefinementCreateRequest,
    WorkflowRefinementResponse,
)
from app.modules.workflow_refinement.enums import (
    WorkflowRefinementStatus,
    WorkflowRefinementDecision,
)
from app.modules.workflow_refinement.exceptions import (
    WorkflowRefinementNotFoundException,
)

from app.modules.workflow_refinement.context_builder import build_workflow_refinement_context
from app.modules.workflow_refinement.refinement_input_loader import load_closed_loop_refinement_input
from app.modules.workflow_refinement.experiment_history_collector import collect_experiment_history
from app.modules.workflow_refinement.workflow_refinement_context_builder import (
    build_llm_workflow_refinement_context,
)
from app.modules.workflow_refinement.llm_prompt_builder import build_llm_prompt
from app.modules.workflow_refinement.llm_workflow_refiner import LLMWorkflowRefiner
from app.modules.workflow_refinement.llm_response_parser import parse_llm_response
from app.modules.workflow_refinement.workflow_refinement_validator import (
    validate_workflow_refinement_decision,
    scan_for_forbidden_content,
)
from app.modules.workflow_refinement.workflow_refinement_normalizer import (
    normalize_workflow_refinement_result,
)
from app.modules.workflow_refinement.revised_workflow_plan_validator import (
    validate_revised_workflow_plan,
)
from app.modules.workflow_refinement.workflow_plan_delta_builder import build_workflow_plan_delta
from app.modules.workflow_refinement.iteration_rerun_plan_builder import build_iteration_rerun_plan
from app.modules.workflow_refinement.final_selection_input_builder import build_final_selection_input
from app.modules.workflow_refinement.refinement_artifact_manager import save_refinement_artifacts
from app.modules.workflow_refinement.builder import build_response

logger = logging.getLogger(__name__)


class WorkflowRefinementService:

    def __init__(self):
        self.repo = WorkflowRefinementRepository()
        self.llm_refiner = LLMWorkflowRefiner()

    def create_workflow_refinement(
        self,
        session: Session,
        task_id: str,
        request: WorkflowRefinementCreateRequest,
    ) -> WorkflowRefinementResponse:
        warnings_list: list = []

        # Step 1: Build context & validate upstream ResultDiagnosis
        rd = build_workflow_refinement_context(
            session, task_id, request.result_diagnosis_id
        )

        # If not force_rerun, check for existing refinement
        if not request.force_rerun:
            existing = self.repo.get_latest_by_task_id(session, task_id)
            if existing and existing.result_diagnosis_id == rd.id and existing.status in (
                WorkflowRefinementStatus.DECIDED,
                WorkflowRefinementStatus.DECIDED_WITH_WARNING,
            ):
                return self.get_workflow_refinement(session, existing.id)

        # Determine iteration index
        iteration_index = request.current_iteration_index
        if iteration_index is None:
            prev = self.repo.get_latest_by_task_id(session, task_id)
            iteration_index = (prev.iteration_index or -1) + 1 if prev else 0

        # Create record
        wr_id = f"wr_{uuid.uuid4().hex[:8]}"
        record = WorkflowRefinement(
            id=wr_id,
            task_id=task_id,
            result_diagnosis_id=rd.id,
            metric_evaluation_id=rd.metric_evaluation_id,
            pipeline_execution_id=rd.pipeline_execution_id,
            source_workflow_plan_id=None,
            iteration_index=iteration_index,
            status=WorkflowRefinementStatus.DECIDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.repo.create(session, record)

        try:
            # Step 2: Load closed_loop_refinement_input
            cl_input = load_closed_loop_refinement_input(rd)

            # Step 3: Collect experiment history
            history = collect_experiment_history(session, task_id)

            # Step 4: Build LLM refinement context
            llm_context = build_llm_workflow_refinement_context(
                session, task_id, rd, cl_input, history, request.decision_profile,
            )

            # Steps 5-6: Build prompt and call LLM
            prompt = build_llm_prompt(llm_context)
            llm_result = self.llm_refiner.refine(
                prompt["system_prompt"], prompt["user_message"],
            )
            record.llm_request_json = prompt
            record.llm_response_json = {"raw_response": llm_result["raw_response"]}

            # Step 7: Parse LLM response
            parsed = parse_llm_response(llm_result["raw_response"])

            # Step 8: Validate decision
            is_valid, validation_issues = validate_workflow_refinement_decision(parsed)

            # Step 8b: Safety scan for forbidden content
            safety_issues = scan_for_forbidden_content(parsed)
            safety_passed = len(safety_issues) == 0

            if not safety_passed:
                warnings_list.append(
                    f"Safety scan found forbidden content: {'; '.join(safety_issues[:5])}"
                )

            if not is_valid and not safety_passed:
                record.status = WorkflowRefinementStatus.FAILED
                record.error_message = f"Validation: {'; '.join(validation_issues[:5])}. Safety: {'; '.join(safety_issues[:5])}"
                record.updated_at = datetime.now(timezone.utc)
                self.repo.update(session, record)
                return build_response(
                    record=record,
                    warnings=warnings_list,
                    validation_result={
                        "is_valid": False,
                        "decision_valid": is_valid,
                        "safety_scan_passed": safety_passed,
                        "issues": validation_issues + safety_issues,
                    },
                )

            # Step 9: Normalize
            normalized = normalize_workflow_refinement_result(parsed)

            decision_obj = normalized.get("workflow_refinement_decision") or {}
            decision = decision_obj.get("decision", WorkflowRefinementDecision.ITERATE_REFINEMENT)
            reasoning = normalized.get("decision_reasoning") or {}
            evidence = normalized.get("evidence_used") or []
            llm_revised_plan = normalized.get("revised_workflow_plan")
            llm_rerun_plan = normalized.get("iteration_rerun_plan")
            llm_fpsi = normalized.get("final_pipeline_selection_input")
            recommended_rerun = decision_obj.get("recommended_rerun_from_stage")

            # Step 10: Validate revised workflow plan if present
            revised_plan_valid = None
            if decision == WorkflowRefinementDecision.ITERATE_REFINEMENT and llm_revised_plan:
                plan_validation = validate_revised_workflow_plan(llm_revised_plan)
                revised_plan_valid = plan_validation["is_valid"]
                if not revised_plan_valid:
                    warnings_list.append(
                        f"Revised workflow plan validation: {'; '.join(plan_validation['errors'][:5])}"
                    )

            # Step 11: Build workflow plan delta
            try:
                from app.modules.workflow_planning.repository import WorkflowPlanRepository
                wp_repo = WorkflowPlanRepository()
                wp = wp_repo.get_latest_by_task_id(session, task_id)
                original_plan = wp.plan_json if wp else None
                record.source_workflow_plan_id = wp.id if wp else None
            except Exception:
                original_plan = None

            plan_delta = build_workflow_plan_delta(
                original_plan, llm_revised_plan,
                (llm_revised_plan or {}).get("refinement_metadata") if llm_revised_plan else None,
            )

            # Step 12: Build iteration rerun plan or final selection input
            rerun_plan = build_iteration_rerun_plan(
                llm_rerun_plan, decision, recommended_rerun,
                (reasoning.get("final_reasoning_summary") if reasoning else ""),
            )

            # Gather best model/trial info
            best_me_id = rd.metric_evaluation_id
            best_model_id = None
            best_trial_id = None
            best_pipeline_spec_id = None
            try:
                from app.modules.metric_evaluation.repository import MetricEvaluationRepository
                me_repo = MetricEvaluationRepository()
                me = me_repo.get_latest_by_task_id(session, task_id)
                if me:
                    best_me_id = me.id
                    best_model_id = me.best_model_id
                    best_trial_id = me.best_trial_id
                    if me.evaluation_json:
                        best_pipeline_spec_id = me.evaluation_json.get("best_pipeline_spec_id")
            except Exception:
                pass

            final_selection_input = build_final_selection_input(
                wr_id, task_id, decision, llm_fpsi,
                best_me_id, best_model_id, best_trial_id, best_pipeline_spec_id,
            )

            # Step 13: Save artifacts
            artifact_manifest = save_refinement_artifacts(
                workflow_refinement_id=wr_id,
                refinement_result={"status": record.status, "decision": decision},
                llm_context=llm_context,
                llm_request=prompt,
                llm_response={"raw_response": llm_result["raw_response"]},
                revised_workflow_plan=llm_revised_plan or {},
                workflow_plan_delta=plan_delta,
                iteration_rerun_plan=rerun_plan,
                final_pipeline_selection_input=final_selection_input,
                validation_result={
                    "is_valid": is_valid,
                    "safety_scan_passed": safety_passed,
                    "revised_plan_valid": revised_plan_valid,
                    "issues": validation_issues + safety_issues,
                },
            )

            # Step 14: Update record
            record.status = WorkflowRefinementStatus.DECIDED
            if warnings_list:
                record.status = WorkflowRefinementStatus.DECIDED_WITH_WARNING
            if not is_valid or not safety_passed:
                record.status = WorkflowRefinementStatus.FAILED

            record.decision = decision
            record.decision_confidence_level = decision_obj.get("decision_confidence_level")
            record.recommended_rerun_from_stage = recommended_rerun
            record.ready_for_iteration = (
                decision == WorkflowRefinementDecision.ITERATE_REFINEMENT
                and (revised_plan_valid if revised_plan_valid is not None else True)
            )
            record.ready_for_final_pipeline_selection = (
                decision == WorkflowRefinementDecision.PROCEED_NEXT_STAGE
            )
            record.iteration_index = iteration_index
            record.workflow_refinement_json = normalized
            record.revised_workflow_plan_json = llm_revised_plan
            record.workflow_plan_delta_json = plan_delta
            record.iteration_rerun_plan_json = rerun_plan
            record.final_pipeline_selection_input_json = final_selection_input
            record.validation_result_json = {
                "is_valid": is_valid,
                "safety_scan_passed": safety_passed,
                "revised_plan_valid": revised_plan_valid,
                "issues": validation_issues + safety_issues,
            }
            record.artifact_dir = f"/app/artifacts/workflow_refinement/{wr_id}"
            record.updated_at = datetime.now(timezone.utc)

            self.repo.update(session, record)

            return build_response(
                record=record,
                llm_result=normalized,
                decision_dto=decision_obj,
                reasoning=reasoning,
                evidence=evidence,
                revised_plan=llm_revised_plan,
                plan_delta=plan_delta,
                rerun_plan=rerun_plan,
                final_selection_input=final_selection_input,
                validation_result={
                    "is_valid": is_valid,
                    "decision_valid": is_valid,
                    "safety_scan_passed": safety_passed,
                    "revised_plan_valid": revised_plan_valid,
                    "issues": validation_issues + safety_issues,
                },
                artifact_manifest=artifact_manifest,
                warnings=warnings_list,
            )

        except Exception as e:
            logger.error("Workflow refinement failed: %s", str(e))
            record.status = WorkflowRefinementStatus.FAILED
            record.error_message = str(e)
            record.updated_at = datetime.now(timezone.utc)
            self.repo.update(session, record)
            return build_response(
                record=record,
                warnings=warnings_list,
            )

    def get_workflow_refinement(
        self, session: Session, wr_id: str
    ) -> WorkflowRefinementResponse:
        record = self.repo.get_by_id(session, wr_id)
        if not record:
            raise WorkflowRefinementNotFoundException(
                f"WorkflowRefinement '{wr_id}' not found."
            )
        return self._record_to_response(record)

    def get_latest_by_task_id(
        self, session: Session, task_id: str
    ) -> WorkflowRefinementResponse:
        record = self.repo.get_latest_by_task_id(session, task_id)
        if not record:
            raise WorkflowRefinementNotFoundException(
                f"No WorkflowRefinement found for task '{task_id}'."
            )
        return self._record_to_response(record)

    def rerun_workflow_refinement(
        self, session: Session, task_id: str
    ) -> WorkflowRefinementResponse:
        request = WorkflowRefinementCreateRequest(force_rerun=True)
        return self.create_workflow_refinement(session, task_id, request)

    def get_revised_workflow_plan(
        self, session: Session, wr_id: str
    ) -> dict:
        record = self.repo.get_by_id(session, wr_id)
        if not record:
            raise WorkflowRefinementNotFoundException(
                f"WorkflowRefinement '{wr_id}' not found."
            )
        return record.revised_workflow_plan_json or {}

    def get_iteration_rerun_plan(
        self, session: Session, wr_id: str
    ) -> dict:
        record = self.repo.get_by_id(session, wr_id)
        if not record:
            raise WorkflowRefinementNotFoundException(
                f"WorkflowRefinement '{wr_id}' not found."
            )
        return record.iteration_rerun_plan_json or {}

    def get_final_pipeline_selection_input(
        self, session: Session, wr_id: str
    ) -> dict:
        record = self.repo.get_by_id(session, wr_id)
        if not record:
            raise WorkflowRefinementNotFoundException(
                f"WorkflowRefinement '{wr_id}' not found."
            )
        return record.final_pipeline_selection_input_json or {}

    def _record_to_response(self, record: WorkflowRefinement) -> WorkflowRefinementResponse:
        wr_json = record.workflow_refinement_json or {}
        decision_obj = (wr_json.get("workflow_refinement_decision") if isinstance(wr_json, dict) else None)
        reasoning = (wr_json.get("decision_reasoning") if isinstance(wr_json, dict) else None)
        evidence = (wr_json.get("evidence_used") if isinstance(wr_json, dict) else None)

        return build_response(
            record=record,
            llm_result=wr_json if isinstance(wr_json, dict) else None,
            decision_dto=decision_obj,
            reasoning=reasoning,
            evidence=evidence if isinstance(evidence, list) else None,
            revised_plan=record.revised_workflow_plan_json,
            plan_delta=record.workflow_plan_delta_json,
            rerun_plan=record.iteration_rerun_plan_json,
            final_selection_input=record.final_pipeline_selection_input_json,
            validation_result=record.validation_result_json,
        )
