import logging
from typing import Dict, Any, Optional, List
from app.modules.iteration_decision.schemas import (
    LLMDecisionOutput, SystemChecks, IterationRerunPlan, RevisedWorkflowPlan,
)
from app.modules.iteration_decision.enums import Decision, TargetStage

logger = logging.getLogger(__name__)

STAGE_ORDER = [
    TargetStage.WORKFLOW_PLANNING,
    TargetStage.FEATURE_ENGINEERING,
    TargetStage.FEATURE_PREPROCESSING,
    TargetStage.MODEL_SEARCH_CONTEXT,
    TargetStage.PIPELINE_GENERATION,
    TargetStage.PIPELINE_EXECUTION,
    TargetStage.METRIC_EVALUATION,
]

# Strategy-field → stage names that influence it.
# When a stage_change targets any of these stage names, the change is
# attached to the corresponding strategy dict so downstream consumers find it.
STRATEGY_STAGE_BINDING: Dict[str, List[str]] = {
    "feature_strategy": [
        TargetStage.FEATURE_ENGINEERING,
        TargetStage.FEATURE_PREPROCESSING,
    ],
    "model_strategy": [
        TargetStage.MODEL_SEARCH_CONTEXT,
    ],
    "hpo_strategy": [
        TargetStage.PIPELINE_GENERATION,
    ],
    "validation_strategy": [
        TargetStage.PIPELINE_EXECUTION,
    ],
    "evaluation_strategy": [
        TargetStage.METRIC_EVALUATION,
    ],
}

# Core modules that MUST re-run Workflow Planning when changed,
# because they consume structured strategy fields and have no LLM.
WP_GATED_STAGES = {TargetStage.WORKFLOW_PLANNING, TargetStage.FEATURE_ENGINEERING}


def build_iteration_plan(
    llm_output: LLMDecisionOutput,
    current_workflow_plan: Optional[Dict[str, Any]],
    system_checks: SystemChecks,
    history: Dict[str, Any],
) -> Dict[str, Any]:
    """Build the concrete iteration plan from LLM output + system context."""

    llm_plan = llm_output.iteration_plan

    # Build iteration guidance blob — the single source of iteration feedback
    iteration_guidance = _build_iteration_guidance(llm_output, history, system_checks)

    # Build Revised Workflow Plan (carries iteration_guidance + per-strategy metadata)
    revised_plan = _build_revised_workflow_plan(
        llm_output, current_workflow_plan, iteration_guidance, history,
    )

    # Build Re-run Plan
    rerun_plan = _build_rerun_plan(llm_plan, system_checks, history)

    stage_changes = llm_plan.stage_changes if llm_plan else []
    rerun_from = rerun_plan.rerun_from_stage
    logger.info(
        "Iteration plan built — rerun_from=%s, %d stage changes, %d reuse artifacts, "
        "needs_wp_rerun=%s",
        rerun_from, len(stage_changes), len(rerun_plan.reuse_artifacts),
        rerun_from == TargetStage.WORKFLOW_PLANNING,
    )

    return {
        "revised_workflow_plan": revised_plan,
        "iteration_rerun_plan": rerun_plan,
        "iteration_guidance": iteration_guidance,
    }


# ---------------------------------------------------------------------------
#  Iteration Guidance
# ---------------------------------------------------------------------------

def _build_iteration_guidance(
    llm_output: LLMDecisionOutput,
    history: Dict[str, Any],
    system_checks: SystemChecks,
) -> Dict[str, Any]:
    llm_plan = llm_output.iteration_plan
    reasoning = llm_output.reasoning

    return {
        "iteration_index": history.get("n_iterations_completed", 0) + 1,
        "decision": llm_output.decision,
        "confidence": llm_output.confidence,
        "root_cause": {
            "primary_root_cause": reasoning.root_cause.primary_root_cause,
            "dimension": reasoning.root_cause.dimension,
            "upstream_stage_at_fault": reasoning.root_cause.upstream_stage_at_fault,
            "causal_chain": reasoning.root_cause.causal_chain,
        },
        "gap_analysis": {
            "primary_gap": reasoning.gap_analysis.primary_gap,
            "gap_magnitude": reasoning.gap_analysis.gap_magnitude,
            "contributing_factors": reasoning.gap_analysis.contributing_factors,
        },
        "improvement_potential": {
            "estimate": reasoning.improvement_potential.estimate,
            "key_levers": reasoning.improvement_potential.key_levers,
        },
        "stage_changes": [
            {
                "stage": sc.stage,
                "action": sc.action,
                "description": sc.description,
                "rationale": sc.rationale,
                "specific_instructions": sc.specific_instructions,
            }
            for sc in (llm_plan.stage_changes if llm_plan else [])
            if sc.action != "keep"
        ],
        "final_reasoning_summary": reasoning.final_reasoning_summary,
    }


# ---------------------------------------------------------------------------
#  Revised Workflow Plan
# ---------------------------------------------------------------------------

def _build_revised_workflow_plan(
    llm_output: LLMDecisionOutput,
    current_plan: Optional[Dict[str, Any]],
    iteration_guidance: Dict[str, Any],
    history: Dict[str, Any],
) -> RevisedWorkflowPlan:
    """Build a RevisedWorkflowPlan carrying iteration_guidance + per-strategy metadata."""
    llm_plan = llm_output.iteration_plan

    changed_stages: set[str] = set()
    preserved: set[str] = set(llm_plan.preserved_stages) if llm_plan else set()
    stage_map: Dict[str, Dict[str, Any]] = {}

    if llm_plan:
        for sc in llm_plan.stage_changes:
            changed_stages.add(sc.stage)
            stage_map[sc.stage] = {
                "action": sc.action,
                "description": sc.description,
                "rationale": sc.rationale,
                "specific_instructions": sc.specific_instructions,
            }

    # Start with current plan as base
    wp = current_plan or {}
    plan_dict = wp.get("plan_json") if isinstance(wp, dict) else wp
    if not isinstance(plan_dict, dict):
        plan_dict = {}

    revised = RevisedWorkflowPlan(
        task_summary=plan_dict.get("task_summary"),
        data_strategy=plan_dict.get("data_strategy"),
        feature_strategy=_collect_iteration_changes(
            plan_dict.get("feature_strategy"), "feature_strategy", stage_map,
        ),
        model_strategy=_collect_iteration_changes(
            plan_dict.get("model_strategy"), "model_strategy", stage_map,
        ),
        hpo_strategy=_collect_iteration_changes(
            plan_dict.get("hpo_strategy"), "hpo_strategy", stage_map,
        ),
        validation_strategy=_collect_iteration_changes(
            plan_dict.get("validation_strategy"), "validation_strategy", stage_map,
        ),
        evaluation_strategy=_collect_iteration_changes(
            plan_dict.get("evaluation_strategy"), "evaluation_strategy", stage_map,
        ),
        iteration_guidance=iteration_guidance,
        changed_sections=sorted(changed_stages),
        preserved_sections=sorted(preserved),
        llm_reasoning_summary=llm_output.reasoning.final_reasoning_summary,
    )

    return revised


def _collect_iteration_changes(
    original: Any,
    strategy_name: str,
    stage_map: Dict[str, Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Collect _iteration_changes from all stages that influence this strategy."""
    result = dict(original) if isinstance(original, dict) else {}

    bound_stages = STRATEGY_STAGE_BINDING.get(strategy_name, [])
    merged = {}
    for stage in bound_stages:
        if stage in stage_map:
            merged[stage] = stage_map[stage]

    if merged:
        result["_iteration_changes"] = merged
    else:
        result["_iteration_changes"] = {}

    return result if result else None


# ---------------------------------------------------------------------------
#  Rerun Plan
# ---------------------------------------------------------------------------

def _determine_rerun_from_stage(stage_changes: Optional[List[Any]]) -> str:
    """Determine the earliest stage to re-run based on which stages were changed.

    - workflow_planning / feature_engineering changes require WP re-run
      (FE has no LLM; only WP can interpret natural-language instructions
      and produce a revised feature_strategy that FE can consume).
    - All other stage changes can be handled by the downstream LLM modules
      directly via iteration_guidance in the WorkflowPlan.
    """
    if not stage_changes:
        return TargetStage.FEATURE_ENGINEERING

    changed = {sc.stage for sc in stage_changes if sc.action != "keep"}

    if changed & WP_GATED_STAGES:
        logger.info("Rerun starts from Workflow Planning — changes in %s require WP re-run",
                     sorted(changed & WP_GATED_STAGES))
        return TargetStage.WORKFLOW_PLANNING

    for s in STAGE_ORDER:
        if s in changed:
            return s

    return TargetStage.FEATURE_ENGINEERING


def _build_rerun_plan(
    llm_plan: Any, system_checks: SystemChecks, history: Dict[str, Any]
) -> IterationRerunPlan:
    """Build the concrete re-run instructions."""
    if llm_plan is None:
        return IterationRerunPlan()

    n_iter = history.get("n_iterations_completed", 0)
    next_index = n_iter + 1

    stage_changes = llm_plan.stage_changes if llm_plan else []
    rerun_from = _determine_rerun_from_stage(stage_changes)

    # All stages from rerun_from onwards are re-executed
    rerun_stages = []
    found = False
    for s in STAGE_ORDER:
        if s == rerun_from:
            found = True
        if found:
            rerun_stages.append(s)

    # Determine artifact reusability
    reuse = []
    invalidate = []
    for s in STAGE_ORDER:
        if s in rerun_stages:
            invalidate.append(f"{s}_artifact")
        else:
            reuse.append(f"{s}_artifact")

    if TargetStage.WORKFLOW_PLANNING not in rerun_stages:
        reuse.append("raw_dataset")
        reuse.append("dataset_profile")

    # Build expected improvement targets
    targets = [llm_plan.expected_improvement] if llm_plan.expected_improvement else []
    if system_checks.high_fold_variance:
        targets.append("reduce fold variance")
    if system_checks.weak_baseline_improvement:
        targets.append("improve baseline improvement")

    return IterationRerunPlan(
        next_iteration_index=next_index,
        rerun_from_stage=rerun_from,
        rerun_stages=rerun_stages,
        reuse_artifacts=reuse,
        invalidate_artifacts=invalidate,
        expected_improvement_targets=targets,
        minimum_improvement_threshold=0.03,
        stop_after_next_iteration_if_no_gain=True,
        reasoning=llm_plan.stop_condition or "",
    )
