import copy
from typing import Dict, Any
from app.modules.iteration_decision.schemas import (
    LLMDecisionOutput,
    DecisionReasoning,
    TaskCompletionAssessment,
    GapAnalysis,
    RootCauseAnalysis,
    ImprovementPotential,
    StageChange,
    IterationPlan,
    StopRationale,
    EvidenceItem,
)
from app.modules.iteration_decision.enums import canonical_target_stage


def normalize_decision(raw: Dict[str, Any]) -> LLMDecisionOutput:
    data = copy.deepcopy(raw)

    # Reasoning
    r = data.get("reasoning") or {}
    tc = r.get("task_completion") or {}
    ga = r.get("gap_analysis") or {}
    rc = r.get("root_cause") or {}
    ip_ = r.get("improvement_potential") or {}

    reasoning = DecisionReasoning(
        task_completion=TaskCompletionAssessment(
            completion_level=tc.get("completion_level", "partial"),
            target_metric=tc.get("target_metric"),
            target_value=tc.get("target_value"),
            actual_value=tc.get("actual_value"),
            gap_description=tc.get("gap_description", ""),
            physics_constraints_satisfied=tc.get("physics_constraints_satisfied", True),
            physics_violations=tc.get("physics_violations") or [],
        ),
        performance_assessment=r.get("performance_assessment", ""),
        gap_analysis=GapAnalysis(
            primary_gap=ga.get("primary_gap", ""),
            gap_magnitude=ga.get("gap_magnitude", "moderate"),
            contributing_factors=ga.get("contributing_factors") or [],
        ),
        root_cause=RootCauseAnalysis(
            primary_root_cause=rc.get("primary_root_cause", ""),
            dimension=rc.get("dimension", ""),
            causal_chain=rc.get("causal_chain", ""),
            upstream_stage_at_fault=canonical_target_stage(rc.get("upstream_stage_at_fault", "")) if rc.get("upstream_stage_at_fault") else None,
            supporting_evidence=rc.get("supporting_evidence") or [],
        ),
        improvement_potential=ImprovementPotential(
            estimate=ip_.get("estimate", "moderate"),
            key_levers=ip_.get("key_levers") or [],
            estimated_effort=ip_.get("estimated_effort", "moderate"),
        ),
        final_reasoning_summary=r.get("final_reasoning_summary", ""),
    )

    # Evidence
    evidence_items = []
    for e in (data.get("evidence_basis") or []):
        if isinstance(e, dict):
            evidence_items.append(EvidenceItem(
                evidence_type=e.get("evidence_type", ""),
                source_module=e.get("source_module", ""),
                source_field=e.get("source_field", ""),
                value=e.get("value"),
                interpretation=e.get("interpretation", ""),
            ))

    # Iteration plan
    iteration_plan = None
    ip_raw = data.get("iteration_plan")
    if ip_raw and isinstance(ip_raw, dict):
        stage_changes = []
        for sc in (ip_raw.get("stage_changes") or []):
            if isinstance(sc, dict):
                stage_changes.append(StageChange(
                    stage=canonical_target_stage(sc.get("stage", "")),
                    action=sc.get("action", "adjust"),
                    description=sc.get("description", ""),
                    rationale=sc.get("rationale", ""),
                    specific_instructions=sc.get("specific_instructions"),
                ))
        iteration_plan = IterationPlan(
            rerun_from_stage=canonical_target_stage(ip_raw.get("rerun_from_stage", "")),
            stage_changes=stage_changes,
            preserved_stages=[canonical_target_stage(s) for s in (ip_raw.get("preserved_stages") or [])],
            expected_improvement=ip_raw.get("expected_improvement", ""),
            estimated_remaining_iterations=ip_raw.get("estimated_remaining_iterations", 1),
            stop_condition=ip_raw.get("stop_condition", ""),
        )

    # Stop rationale
    stop_rationale = None
    sr_raw = data.get("stop_rationale")
    if sr_raw and isinstance(sr_raw, dict):
        stop_rationale = StopRationale(
            primary_reason=sr_raw.get("primary_reason", ""),
            category=sr_raw.get("category", ""),
            supporting_reasons=sr_raw.get("supporting_reasons") or [],
            best_result_summary=sr_raw.get("best_result_summary", ""),
        )

    return LLMDecisionOutput(
        decision=data.get("decision", ""),
        reasoning=reasoning,
        evidence_basis=evidence_items,
        iteration_plan=iteration_plan,
        stop_rationale=stop_rationale,
        confidence=data.get("confidence", "medium"),
    )
