import logging
from typing import Dict, Any, List, Optional

from app.modules.workflow_refinement.model import WorkflowRefinement
from app.modules.workflow_refinement.schemas import (
    WorkflowRefinementResponse,
    WorkflowRefinementDecisionDTO,
    DecisionReasoning,
    EvidenceUsed,
    RevisedWorkflowPlanResponse,
    RefinementMetadata,
    WorkflowPlanDelta,
    IterationRerunPlan,
    LLMWorkflowRefinementResult,
    WorkflowRefinementValidationResult,
    ArtifactManifest,
)

logger = logging.getLogger(__name__)


def build_response(
    record: WorkflowRefinement,
    llm_result: Optional[Dict[str, Any]] = None,
    decision_dto: Optional[Dict[str, Any]] = None,
    reasoning: Optional[Dict[str, Any]] = None,
    evidence: Optional[List[Dict[str, Any]]] = None,
    revised_plan: Optional[Dict[str, Any]] = None,
    plan_delta: Optional[Dict[str, Any]] = None,
    rerun_plan: Optional[Dict[str, Any]] = None,
    validation_result: Optional[Dict[str, Any]] = None,
    artifact_manifest: Optional[Dict[str, Any]] = None,
    warnings: Optional[List[str]] = None,
) -> WorkflowRefinementResponse:

    decision = None
    decision_confidence = None
    recommended_rerun = None
    if decision_dto:
        decision = decision_dto.get("decision")
        decision_confidence = decision_dto.get("decision_confidence_level")
        recommended_rerun = decision_dto.get("recommended_rerun_from_stage")

    evidence_used = []
    if evidence:
        for e in evidence:
            evidence_used.append(EvidenceUsed(
                evidence_id=e.get("evidence_id", ""),
                source_module=e.get("source_module", ""),
                evidence_type=e.get("evidence_type", ""),
                source_field=e.get("source_field", ""),
                value=e.get("value"),
                interpretation=e.get("interpretation", ""),
                supports_decision=e.get("supports_decision", ""),
            ))

    rwp = None
    if revised_plan:
        rmeta = revised_plan.get("refinement_metadata") or {}
        rwp = RevisedWorkflowPlanResponse(
            workflow_plan_id=revised_plan.get("workflow_plan_id"),
            status=revised_plan.get("status", "planned_by_refinement"),
            planning_mode=revised_plan.get("planning_mode", "llm_refinement"),
            task_summary=revised_plan.get("task_summary"),
            data_strategy=revised_plan.get("data_strategy"),
            feature_strategy=revised_plan.get("feature_strategy"),
            model_strategy=revised_plan.get("model_strategy"),
            validation_strategy=revised_plan.get("validation_strategy"),
            evaluation_strategy=revised_plan.get("evaluation_strategy"),
            hpo_strategy=revised_plan.get("hpo_strategy"),
            interpretability_strategy=revised_plan.get("interpretability_strategy"),
            pipeline_generation_input=revised_plan.get("pipeline_generation_input"),
            planning_warnings=revised_plan.get("planning_warnings") or [],
            planning_assumptions=revised_plan.get("planning_assumptions") or [],
            llm_reasoning_summary=revised_plan.get("llm_reasoning_summary", ""),
            confidence_score=revised_plan.get("confidence_score", 0.0),
            refinement_metadata=RefinementMetadata(
                source_workflow_plan_id=rmeta.get("source_workflow_plan_id"),
                source_result_diagnosis_id=rmeta.get("source_result_diagnosis_id"),
                changed_sections=rmeta.get("changed_sections") or [],
                preserved_sections=rmeta.get("preserved_sections") or [],
                recommended_rerun_from_stage=rmeta.get("recommended_rerun_from_stage"),
            ) if rmeta else None,
        )

    wpd = None
    if plan_delta:
        wpd = WorkflowPlanDelta(**plan_delta)

    irp = None
    if rerun_plan:
        irp = IterationRerunPlan(**rerun_plan)

    llm_wr = None
    if llm_result:
        llm_wr = LLMWorkflowRefinementResult(
            workflow_refinement_decision=WorkflowRefinementDecisionDTO(**decision_dto) if decision_dto else None,
            decision_reasoning=DecisionReasoning(**reasoning) if reasoning else None,
            evidence_used=evidence_used,
            revised_workflow_plan=revised_plan,
            iteration_rerun_plan=rerun_plan,
            confidence_level=llm_result.get("confidence_level", "medium"),
        )

    vr = None
    if validation_result:
        vr = WorkflowRefinementValidationResult(**validation_result)

    am = None
    if artifact_manifest:
        am = ArtifactManifest(**artifact_manifest)

    return WorkflowRefinementResponse(
        workflow_refinement_id=record.id,
        task_id=record.task_id,
        result_diagnosis_id=record.result_diagnosis_id,
        metric_evaluation_id=record.metric_evaluation_id,
        iteration_index=record.iteration_index or 0,
        status=record.status or "deciding",
        decision=decision,
        decision_confidence_level=decision_confidence,
        decision_reasoning=DecisionReasoning(**reasoning) if reasoning else None,
        evidence_used=evidence_used,
        recommended_rerun_from_stage=recommended_rerun,
        revised_workflow_plan=rwp,
        workflow_plan_delta=wpd,
        iteration_rerun_plan=irp,
        llm_workflow_refinement=llm_wr,
        workflow_refinement_validation_result=vr,
        artifact_manifest=am,
        ready_for_iteration=record.ready_for_iteration or False,
        warnings=warnings or [],
        error_message=record.error_message,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
