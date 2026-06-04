from typing import Optional
from app.modules.iteration_decision.model import IterationDecision
from app.modules.iteration_decision.schemas import (
    IterationDecisionResponse,
    LLMDecisionOutput,
    SystemChecks,
    EvidenceBundle,
    ArtifactManifest,
    IterationPlan,
    RevisedWorkflowPlan,
    IterationRerunPlan,
    StopRationale,
)
from app.modules.iteration_decision.enums import DecisionStatus


def build_response(
    record: IterationDecision,
    llm_output: Optional[LLMDecisionOutput] = None,
    evidence_bundle: Optional[EvidenceBundle] = None,
    system_checks: Optional[SystemChecks] = None,
    iteration_plan: Optional[IterationPlan] = None,
    revised_workflow_plan: Optional[RevisedWorkflowPlan] = None,
    rerun_plan: Optional[IterationRerunPlan] = None,
    stop_rationale: Optional[StopRationale] = None,
    artifact_manifest: Optional[ArtifactManifest] = None,
    warnings: Optional[list] = None,
) -> IterationDecisionResponse:
    return IterationDecisionResponse(
        iteration_decision_id=record.id,
        task_id=record.task_id,
        metric_evaluation_id=record.metric_evaluation_id,
        iteration_index=record.iteration_index or 0,
        status=record.status or DecisionStatus.DECIDING,
        decision=record.decision or (llm_output.decision if llm_output and llm_output.decision else None),
        decision_confidence=record.decision_confidence or (llm_output.confidence if llm_output and llm_output.confidence else None),
        reasoning=llm_output.reasoning if llm_output else None,
        evidence_basis=llm_output.evidence_basis if llm_output else [],
        iteration_plan=iteration_plan,
        revised_workflow_plan=revised_workflow_plan,
        iteration_rerun_plan=rerun_plan,
        ready_for_iteration=record.ready_for_iteration or False,
        stop_rationale=stop_rationale,
        evidence_bundle=evidence_bundle,
        system_checks=system_checks,
        artifact_manifest=artifact_manifest,
        warnings=warnings or [],
        error_message=record.error_message,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
