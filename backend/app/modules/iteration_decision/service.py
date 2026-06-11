import uuid
import logging
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Optional
from sqlmodel import Session

from app.modules.iteration_decision.model import IterationDecision
from app.modules.iteration_decision.repository import IterationDecisionRepository
from app.modules.iteration_decision.schemas import (
    IterationDecisionCreateRequest,
    IterationDecisionResponse,
    IterationDecisionSummary,
    EvidenceBundle,
)
from app.modules.iteration_decision.enums import DecisionStatus, Decision

from app.modules.iteration_decision.context.metrics_context import gather_metrics_context
from app.modules.iteration_decision.context.upstream_context import gather_upstream_context
from app.modules.iteration_decision.context.history_context import gather_history_context

from app.modules.iteration_decision.evidence.ml_evidence import extract_ml_evidence
from app.modules.iteration_decision.evidence.materials_evidence import extract_materials_evidence
from app.modules.iteration_decision.evidence.workflow_evidence import extract_workflow_evidence
from app.modules.iteration_decision.evidence.history_evidence import extract_history_evidence

from app.modules.iteration_decision.rules.ml_rules import run_ml_rules
from app.modules.iteration_decision.rules.materials_rules import run_materials_rules
from app.modules.iteration_decision.rules.guard_rules import run_guard_rules

from app.modules.iteration_decision.llm.prompt_builder import SYSTEM_PROMPT, build_user_message
from app.modules.iteration_decision.llm.decision_context_builder import build_decision_context
from app.modules.iteration_decision.llm.decision_maker import LLMDecisionMaker
from app.modules.iteration_decision.llm.response_parser import parse_response
from app.modules.iteration_decision.llm.decision_validator import validate_decision
from app.modules.iteration_decision.llm.decision_normalizer import normalize_decision

from app.modules.iteration_decision.plan.iteration_plan_builder import build_iteration_plan
from app.modules.iteration_decision.plan.conflict_detector import detect_conflicts
from app.modules.iteration_decision.plan.plan_validator import (
    validate_iteration_plan, validate_revised_workflow_plan, validate_rerun_plan,
)

from app.modules.iteration_decision.artifacts.artifact_manager import save_decision_artifacts
from app.modules.iteration_decision.builder import build_response
from app.modules.iteration_decision.exceptions import (
    IterationDecisionNotFoundException,
)

logger = logging.getLogger(__name__)


class IterationDecisionService:

    def __init__(self):
        self.repo = IterationDecisionRepository()
        self.llm = LLMDecisionMaker()

    def create_decision(
        self,
        session: Session,
        task_id: str,
        request: IterationDecisionCreateRequest,
    ) -> IterationDecisionResponse:
        warnings_list: list = []
        started_at = time.time()

        logger.info("=== Iteration Decision — task=%s force_rerun=%s ===",
                     task_id, request.force_rerun)

        # ---- Phase 1: Gather context (zero LLM) ----
        logger.info("[1/7] Gathering context ...")
        t0 = time.time()
        metrics = gather_metrics_context(session, task_id, request.metric_evaluation_id)
        upstream = gather_upstream_context(session, task_id)
        history = gather_history_context(session, task_id)
        logger.info("[1/7] Done — metrics=ok upstream=%d modules history=%d iterations (%.1fs)",
                     upstream.get("_module_count", 0), history.get("n_iterations_completed", 0),
                     time.time() - t0)

        # ---- Phase 0: Pre-check ----
        logger.info("[0/7] Pre-check: checking existing decisions ...")
        if not request.force_rerun:
            existing = self.repo.get_latest_by_task_id(session, task_id)
            if existing and existing.metric_evaluation_id == metrics["metric_evaluation_id"] and existing.status in (
                DecisionStatus.DECIDED, DecisionStatus.DECIDED_WITH_WARNING, DecisionStatus.FALLBACK,
            ):
                logger.info("[0/7] Done — found recent decision id=%s, returning cached", existing.id)
                return self.get_decision(session, existing.id)

        # Determine iteration index
        iteration_index = request.current_iteration_index
        if iteration_index is None:
            prev = self.repo.get_latest_by_task_id(session, task_id)
            iteration_index = (prev.iteration_index or 0) + 1 if prev else 0

        logger.info("[0/7] Done — starting iteration #%d", iteration_index)

        # Create record
        id_ = f"id_{uuid.uuid4().hex[:8]}"
        record = IterationDecision(
            id=id_,
            task_id=task_id,
            metric_evaluation_id=metrics["metric_evaluation_id"],
            pipeline_execution_id=metrics.get("pipeline_execution_id"),
            iteration_index=iteration_index,
            status=DecisionStatus.DECIDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.repo.create(session, record)

        try:
            # ---- Phase 2: Extract evidence (zero LLM) ----
            logger.info("[2/7] Extracting evidence ...")
            t0 = time.time()
            evidence_ml = extract_ml_evidence(metrics)
            evidence_materials = extract_materials_evidence(upstream, metrics)
            evidence_workflow = extract_workflow_evidence(upstream)
            evidence_history = extract_history_evidence(history)
            logger.info("[2/7] Done — ML=%d materials=%d workflow=%d history=%d (%.1fs)",
                         len(evidence_ml), len(evidence_materials), len(evidence_workflow),
                         len(evidence_history), time.time() - t0)

            evidence_bundle = EvidenceBundle(
                ml_performance=evidence_ml,
                materials=evidence_materials,
                workflow_quality=evidence_workflow,
                history_trends=evidence_history,
            )

            # ---- Phase 3: System rule checks (zero LLM) ----
            logger.info("[3/7] Running system rule checks ...")
            t0 = time.time()
            ml_checks = run_ml_rules(metrics, evidence_ml)
            materials_checks = run_materials_rules(upstream, metrics)
            guard_checks = run_guard_rules(history, request.max_iterations)

            # Merge checks
            system_checks = ml_checks
            system_checks.physics_constraint_violated = materials_checks.physics_constraint_violated
            system_checks.feature_materials_relevance_low = materials_checks.feature_materials_relevance_low
            system_checks.chemical_space_coverage_low = materials_checks.chemical_space_coverage_low
            system_checks.small_sample_warning = materials_checks.small_sample_warning
            system_checks.feature_count_low = materials_checks.feature_count_low
            system_checks.many_features_dropped = materials_checks.many_features_dropped
            system_checks.max_iterations_reached = guard_checks.max_iterations_reached
            system_checks.no_improvement_trend = guard_checks.no_improvement_trend
            system_checks.repeated_root_cause = guard_checks.repeated_root_cause
            system_checks.warnings.extend(materials_checks.warnings)
            system_checks.warnings.extend(guard_checks.warnings)

            triggered = [k for k, v in system_checks.model_dump().items() if v is True and k != "warnings" and k != "additional_checks"]
            logger.info("[3/7] Done — %d rules triggered (%s) (%.1fs)",
                         len(triggered), ", ".join(triggered[:5]) or "none", time.time() - t0)

            # ---- Phase 4: Build compact LLM context ----
            logger.info("[4/7] Building compact LLM context ...")
            t0 = time.time()
            llm_context = build_decision_context(
                upstream=upstream,
                metrics=metrics,
                system_checks=system_checks,
                history=history,
                evidence_ml=evidence_ml,
                evidence_materials=evidence_materials,
                evidence_workflow=evidence_workflow,
                evidence_history=evidence_history,
                task_id=task_id,
                iteration_index=iteration_index,
            )
            logger.info("[4/7] Done — compact context built (%.1fs)", time.time() - t0)

            # ---- Phase 5: LLM decision (the single LLM call) ----
            logger.info("[5/7] Calling LLM for iteration decision ...")
            t0 = time.time()
            user_message = build_user_message(llm_context)
            llm_result = self.llm.decide(SYSTEM_PROMPT, user_message)
            logger.info("[5/7] LLM responded in %.1fs", time.time() - t0)
            record.llm_request_json = {"system_prompt": SYSTEM_PROMPT, "user_message": user_message}
            record.llm_response_json = {"raw_response": llm_result["raw_response"]}

            parsed = parse_response(llm_result["raw_response"])
            is_valid, validation_issues = validate_decision(parsed)

            if not is_valid:
                logger.warning("[5/7] Validation failed — %d issue(s), using rule-based fallback",
                               len(validation_issues))
                warnings_list.append(f"LLM decision validation: {'; '.join(validation_issues[:5])}")
                parsed = _rule_based_fallback(system_checks, history, request)
                record.status = DecisionStatus.FALLBACK

            normalized = normalize_decision(parsed)
            logger.info("[5/7] Done — decision=%s confidence=%s (%.1fs total)",
                         normalized.decision, normalized.confidence, time.time() - t0)

            # ---- Phase 6: Build plans (system, from LLM output) ----
            logger.info("[6/7] Building iteration plans ...")
            t0 = time.time()
            iteration_plan = None
            revised_plan = None
            rerun_plan = None
            stop_rationale = None
            iteration_guidance = None
            conflicts = []
            if normalized.decision == Decision.ITERATE:
                current_wp = upstream.get("workflow_plan", {})
                plans = build_iteration_plan(normalized, current_wp, system_checks, history)
                revised_plan = plans["revised_workflow_plan"]
                rerun_plan = plans["iteration_rerun_plan"]
                iteration_plan = normalized.iteration_plan
                iteration_guidance = plans["iteration_guidance"]

                # Conflict detection
                if normalized.iteration_plan:
                    conflicts = detect_conflicts(normalized.iteration_plan)
                    if conflicts:
                        warnings_list.extend(conflicts)

                # Validation
                plan_valid = validate_iteration_plan(normalized.iteration_plan)
                revised_valid = validate_revised_workflow_plan(revised_plan)
                rerun_valid = validate_rerun_plan(rerun_plan)

                logger.info(
                    "[6/7] Plan validation — iteration_plan=%s revised=%s rerun=%s",
                    plan_valid["is_valid"], revised_valid["is_valid"], rerun_valid["is_valid"],
                )

                if not all([plan_valid["is_valid"], revised_valid["is_valid"], rerun_valid["is_valid"]]):
                    all_warnings = (
                        plan_valid.get("errors", []) + plan_valid.get("warnings", []) +
                        revised_valid.get("errors", []) + revised_valid.get("warnings", []) +
                        rerun_valid.get("errors", []) + rerun_valid.get("warnings", [])
                    )
                    warnings_list.extend(all_warnings)
                    logger.warning(
                        "[6/7] Validation issues — plan_errors=%s plan_warnings=%s "
                        "revised_errors=%s revised_warnings=%s rerun_errors=%s rerun_warnings=%s",
                        plan_valid.get("errors"), plan_valid.get("warnings"),
                        revised_valid.get("errors"), revised_valid.get("warnings"),
                        rerun_valid.get("errors"), rerun_valid.get("warnings"),
                    )

                record.rerun_from_stage = rerun_plan.rerun_from_stage if rerun_plan else None
                # ready_for_iteration depends on the system-built plans (revised_plan,
                # rerun_plan), not the LLM's raw iteration_plan.  The LLM's
                # iteration_plan is advisory — the system overrides rerun_from_stage
                # and builds the actual execution plan.
                record.ready_for_iteration = all([
                    revised_valid["is_valid"],
                    rerun_valid["is_valid"],
                ])

            elif normalized.decision == Decision.STOP:
                stop_rationale = normalized.stop_rationale

            logger.info("[6/7] Done — decision=%s stage_changes=%d conflicts=%d (%.1fs)",
                         normalized.decision,
                         len(normalized.iteration_plan.stage_changes) if normalized.iteration_plan else 0,
                         len(conflicts),
                         time.time() - t0)

            # ---- Phase 7: Persist and build response ----
            logger.info("[7/7] Persisting decision and building response ...")
            t0 = time.time()
            record.status = DecisionStatus.DECIDED if record.status != DecisionStatus.FALLBACK else record.status
            if warnings_list:
                record.status = DecisionStatus.DECIDED_WITH_WARNING
            record.decision = normalized.decision
            record.decision_confidence = normalized.confidence
            record.reasoning_json = normalized.reasoning.model_dump() if normalized.reasoning else None
            record.evidence_json = evidence_bundle.model_dump()
            record.system_checks_json = system_checks.model_dump()
            record.revised_workflow_plan_json = revised_plan.model_dump() if revised_plan else None
            record.iteration_plan_json = iteration_plan.model_dump() if iteration_plan else None
            record.iteration_rerun_plan_json = rerun_plan.model_dump() if rerun_plan else None
            record.stop_rationale_json = stop_rationale.model_dump() if stop_rationale else None
            record.validation_result_json = {"is_valid": is_valid, "issues": validation_issues}
            record.artifact_dir = f"/app/artifacts/iteration_decision/{id_}"
            record.updated_at = datetime.now(timezone.utc)

            self.repo.update(session, record)

            # Save artifacts
            artifact_manifest = save_decision_artifacts(
                iteration_decision_id=id_,
                decision_result={"decision": normalized.decision, "confidence": normalized.confidence},
                context=llm_context,
                evidence=evidence_bundle.model_dump(),
                system_checks=system_checks.model_dump(),
                llm_request=record.llm_request_json,
                llm_response=record.llm_response_json,
                iteration_plan=iteration_plan.model_dump() if iteration_plan else None,
                revised_workflow_plan=revised_plan.model_dump() if revised_plan else None,
                stop_output=None,
            )

            total_dur = time.time() - started_at
            logger.info("[7/7] Done — id=%s decision=%s | TOTAL %.1fs",
                         id_, normalized.decision, total_dur)

            return build_response(
                record=record,
                llm_output=normalized,
                evidence_bundle=evidence_bundle,
                system_checks=system_checks,
                iteration_plan=iteration_plan,
                revised_workflow_plan=revised_plan,
                rerun_plan=rerun_plan,
                stop_rationale=stop_rationale,
                artifact_manifest=artifact_manifest,
                warnings=warnings_list,
            )

        except Exception as e:
            total_dur = time.time() - started_at
            logger.error("[FAIL] Iteration decision failed after %.1fs: %s\n%s",
                         total_dur, str(e), traceback.format_exc())
            record.status = DecisionStatus.FAILED
            record.error_message = str(e)
            record.updated_at = datetime.now(timezone.utc)
            self.repo.update(session, record)
            return build_response(record=record, warnings=warnings_list)

    def get_decision(self, session: Session, id_: str) -> IterationDecisionResponse:
        record = self.repo.get_by_id(session, id_)
        if not record:
            raise IterationDecisionNotFoundException(f"IterationDecision '{id_}' not found.")
        return _record_to_response(record)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> IterationDecisionResponse:
        record = self.repo.get_latest_by_task_id(session, task_id)
        if not record:
            raise IterationDecisionNotFoundException(f"No IterationDecision for task '{task_id}'.")
        return _record_to_response(record)

    def rerun_decision(self, session: Session, task_id: str) -> IterationDecisionResponse:
        return self.create_decision(session, task_id, IterationDecisionCreateRequest(force_rerun=True))

    def get_summary(self, session: Session, id_: str) -> IterationDecisionSummary:
        record = self.repo.get_by_id(session, id_)
        if not record:
            raise IterationDecisionNotFoundException(f"IterationDecision '{id_}' not found.")

        rc = record.reasoning_json or {}
        primary_rc = ""
        if isinstance(rc, dict):
            root_cause = rc.get("root_cause") or {}
            if isinstance(root_cause, dict):
                primary_rc = root_cause.get("primary_root_cause", "")

        return IterationDecisionSummary(
            iteration_decision_id=record.id,
            task_id=record.task_id or "",
            iteration_index=record.iteration_index or 0,
            status=record.status or "",
            decision=record.decision,
            confidence=record.decision_confidence,
            primary_root_cause=primary_rc,
            rerun_from_stage=record.rerun_from_stage,
            ready_for_iteration=record.ready_for_iteration or False,
            ready_for_final_selection=False,
            reasoning_summary=(rc.get("final_reasoning_summary", "") if isinstance(rc, dict) else ""),
            created_at=record.created_at,
        )

    def needs_fresh_decision(self, session: Session, task_id: str) -> dict:
        existing = self.repo.get_latest_by_task_id(session, task_id)
        try:
            m = gather_metrics_context(session, task_id, None)
            latest_me_id = m["metric_evaluation_id"]
        except Exception:
            latest_me_id = None

        if not existing:
            return {"needs_fresh": True, "reason": "No existing iteration decision."}

        if latest_me_id and existing.metric_evaluation_id != latest_me_id:
            return {
                "needs_fresh": True,
                "reason": f"Existing decision ({existing.id}) is for metric_evaluation {existing.metric_evaluation_id}, latest is {latest_me_id}.",
                "existing_decision_id": existing.id,
                "latest_metric_evaluation_id": latest_me_id,
            }

        return {"needs_fresh": False, "reason": "Existing decision is up-to-date.", "existing_decision_id": existing.id}

    def get_revised_workflow_plan(self, session: Session, id_: str) -> dict:
        record = self.repo.get_by_id(session, id_)
        if not record:
            raise IterationDecisionNotFoundException(f"IterationDecision '{id_}' not found.")
        return record.revised_workflow_plan_json or {}

    def adopt_revised_plan(self, session: Session, id_: str) -> dict:
        """Adopt the revised workflow plan: validate and persist as new WorkflowPlan.

        When the iteration guidance indicates changes to workflow_planning or
        feature_engineering, we trigger a full WP LLM re-run (the only path
        that can translate natural-language guidance into structured strategy
        changes that FE can consume).  For all other stages, the revised plan
        is persisted directly with iteration_guidance — downstream LLM modules
        read it from the new WorkflowPlan.
        """
        record = self.repo.get_by_id(session, id_)
        if not record:
            raise IterationDecisionNotFoundException(f"IterationDecision '{id_}' not found.")

        if record.decision != Decision.ITERATE:
            from app.shared.common.exceptions import BusinessException
            raise BusinessException(
                f"Cannot adopt plan: decision is '{record.decision}', not 'iterate'.", "ADOPT_NOT_ALLOWED",
            )

        revised = record.revised_workflow_plan_json
        if not revised:
            from app.shared.common.exceptions import BusinessException
            raise BusinessException("No revised workflow plan to adopt.", "ADOPT_NO_REVISED_PLAN")

        # Validate
        from app.modules.iteration_decision.schemas import RevisedWorkflowPlan
        try:
            rwp = RevisedWorkflowPlan(**revised)
        except Exception as e:
            from app.shared.common.exceptions import BusinessException
            raise BusinessException(f"Revised plan invalid: {str(e)}", "ADOPT_PLAN_INVALID")

        plan_valid = validate_revised_workflow_plan(rwp)
        if not plan_valid["is_valid"]:
            from app.shared.common.exceptions import BusinessException
            raise BusinessException(f"Plan validation failed: {plan_valid['errors']}", "ADOPT_PLAN_INVALID")

        rerun_plan = record.iteration_rerun_plan_json or {}
        iteration_guidance = rwp.iteration_guidance
        needs_wp_rerun = (rerun_plan.get("rerun_from_stage") == "workflow_planning")

        from app.modules.workflow_planning.service import WorkflowPlanningService
        wp_service = WorkflowPlanningService()

        if needs_wp_rerun:
            logger.info("Adopt: triggering WP LLM re-run with iteration_guidance for task %s", record.task_id)
            wp_response = wp_service.rerun_with_iteration_guidance(
                session, record.task_id, iteration_guidance,
            )
        else:
            wp_dict = {
                "task_summary": rwp.task_summary,
                "data_strategy": rwp.data_strategy,
                "feature_strategy": rwp.feature_strategy,
                "model_strategy": rwp.model_strategy,
                "hpo_strategy": rwp.hpo_strategy,
                "validation_strategy": rwp.validation_strategy,
                "evaluation_strategy": rwp.evaluation_strategy,
                "iteration_guidance": iteration_guidance,
            }
            wp_response = wp_service.adopt_revised_plan(session, record.task_id, wp_dict)
        new_plan_id = wp_response.workflow_plan_id

        record.source_workflow_plan_id = new_plan_id
        record.status = DecisionStatus.DECIDED
        record.updated_at = datetime.now(timezone.utc)
        self.repo.update(session, record)

        return {
            "adopted": True,
            "iteration_decision_id": id_,
            "adopted_workflow_plan_id": new_plan_id,
            "needs_wp_rerun": needs_wp_rerun,
            "rerun_from_stage": record.rerun_from_stage,
            "rerun_stages": rerun_plan.get("rerun_stages", []),
            "reuse_artifacts": rerun_plan.get("reuse_artifacts", []),
            "invalidate_artifacts": rerun_plan.get("invalidate_artifacts", []),
            "reasoning": rerun_plan.get("reasoning", ""),
        }


def _rule_based_fallback(checks, history, request) -> dict:
    """Produce a fallback decision when LLM fails, based purely on system rules."""
    reasons_to_stop = []
    reasons_to_iterate = []

    if checks.max_iterations_reached:
        reasons_to_stop.append("max_iterations_reached")
    if checks.no_improvement_trend:
        reasons_to_stop.append("no_improvement_trend")
    if checks.repeated_root_cause:
        reasons_to_stop.append("repeated_root_cause")
    if checks.candidate_underperforms_baseline:
        reasons_to_iterate.append("candidate_underperforms_baseline")
    if checks.weak_baseline_improvement and not checks.max_iterations_reached:
        reasons_to_iterate.append("weak_baseline_improvement")
    if checks.feature_count_low:
        reasons_to_iterate.append("feature_count_low")
    if checks.physics_constraint_violated:
        reasons_to_iterate.append("physics_constraint_violated")

    if len(reasons_to_stop) >= len(reasons_to_iterate):
        return {
            "decision": "stop",
            "reasoning": {
                "task_completion": {"completion_level": "not_achieved", "gap_description": f"Fallback: stop due to {', '.join(reasons_to_stop)}."},
                "performance_assessment": "Fallback decision from system rules.",
                "gap_analysis": {"primary_gap": "LLM unavailable; using rule-based fallback."},
                "root_cause": {"primary_root_cause": "LLM unavailable", "dimension": "evaluation_side"},
                "improvement_potential": {"estimate": "none"},
                "final_reasoning_summary": f"Fallback STOP decision: {', '.join(reasons_to_stop)}.",
            },
            "evidence_basis": [],
            "stop_rationale": {"primary_reason": f"Fallback: {', '.join(reasons_to_stop)}.", "category": "resource_limit"},
            "confidence": "low",
        }
    else:
        return {
            "decision": "iterate",
            "reasoning": {
                "task_completion": {"completion_level": "partial"},
                "performance_assessment": "Fallback decision from system rules.",
                "gap_analysis": {"primary_gap": f"Iterate: {', '.join(reasons_to_iterate)}."},
                "root_cause": {"primary_root_cause": reasons_to_iterate[0] if reasons_to_iterate else "unknown"},
                "improvement_potential": {"estimate": "moderate"},
                "final_reasoning_summary": f"Fallback ITERATE decision: {', '.join(reasons_to_iterate)}.",
            },
            "evidence_basis": [],
            "iteration_plan": {
                "rerun_from_stage": "feature_engineering",
                "stage_changes": [{"stage": "feature_engineering", "action": "expand", "description": "Fallback: expand features.", "rationale": "System rule detected feature insufficiency."}],
                "preserved_stages": [],
                "expected_improvement": "unknown (fallback)",
                "stop_condition": "Review after one iteration.",
            },
            "confidence": "low",
        }


def _record_to_response(record: IterationDecision) -> IterationDecisionResponse:
    """Reconstruct response from persisted record."""
    from app.modules.iteration_decision.schemas import (
        LLMDecisionOutput, DecisionReasoning, EvidenceBundle, SystemChecks,
        IterationPlan, RevisedWorkflowPlan, IterationRerunPlan, StopRationale,
    )

    llm_output = None
    # Reconstruct llm_output from record fields; reasoning_json is optional
    if record.decision or record.decision_confidence or record.reasoning_json:
        try:
            reasoning = DecisionReasoning()
            if record.reasoning_json and isinstance(record.reasoning_json, dict):
                try:
                    reasoning = DecisionReasoning(**record.reasoning_json)
                except Exception:
                    pass
            llm_output = LLMDecisionOutput(
                decision=record.decision or "",
                reasoning=reasoning,
                confidence=record.decision_confidence or "medium",
            )
        except Exception:
            pass

    evidence_bundle = None
    if record.evidence_json:
        try:
            evidence_bundle = EvidenceBundle(**record.evidence_json)
        except Exception:
            pass

    system_checks = None
    if record.system_checks_json:
        try:
            system_checks = SystemChecks(**record.system_checks_json)
        except Exception:
            pass

    iteration_plan = None
    if record.iteration_plan_json:
        try:
            iteration_plan = IterationPlan(**record.iteration_plan_json)
        except Exception:
            pass
    revised_plan = None
    if record.revised_workflow_plan_json:
        try:
            revised_plan = RevisedWorkflowPlan(**record.revised_workflow_plan_json)
        except Exception:
            pass

    rerun_plan = None
    if record.iteration_rerun_plan_json:
        try:
            rerun_plan = IterationRerunPlan(**record.iteration_rerun_plan_json)
        except Exception:
            pass

    stop_rationale = None
    if record.stop_rationale_json:
        try:
            stop_rationale = StopRationale(**record.stop_rationale_json)
        except Exception:
            pass

    return build_response(
        record=record,
        llm_output=llm_output,
        evidence_bundle=evidence_bundle,
        system_checks=system_checks,
        iteration_plan=iteration_plan,
        revised_workflow_plan=revised_plan,
        rerun_plan=rerun_plan,
        stop_rationale=stop_rationale,
    )
