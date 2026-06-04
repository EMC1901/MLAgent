import logging
from typing import Dict, Any, Optional
from app.modules.iteration_decision.schemas import (
    LLMDecisionOutput, SystemChecks, IterationRerunPlan, RevisedWorkflowPlan,
)
from app.modules.iteration_decision.enums import Decision, TargetStage

logger = logging.getLogger(__name__)


def build_iteration_plan(
    llm_output: LLMDecisionOutput,
    current_workflow_plan: Optional[Dict[str, Any]],
    system_checks: SystemChecks,
    history: Dict[str, Any],
) -> Dict[str, Any]:
    """Build the concrete iteration plan from LLM output + system context."""

    llm_plan = llm_output.iteration_plan

    # Build Revised Workflow Plan
    revised_plan = _build_revised_workflow_plan(llm_output, current_workflow_plan)

    # Build Re-run Plan
    rerun_plan = _build_rerun_plan(llm_plan, system_checks, history)

    stage_changes = llm_plan.stage_changes if llm_plan else []
    rerun_from = llm_plan.rerun_from_stage if llm_plan else "unknown"
    logger.info("Iteration plan built — rerun_from=%s, %d stage changes, %d reuse artifacts",
                 rerun_from, len(stage_changes), len(rerun_plan.reuse_artifacts))

    return {
        "revised_workflow_plan": revised_plan,
        "iteration_rerun_plan": rerun_plan,
    }


def _build_revised_workflow_plan(
    llm_output: LLMDecisionOutput,
    current_plan: Optional[Dict[str, Any]],
) -> RevisedWorkflowPlan:
    """Build a RevisedWorkflowPlan by merging LLM stage changes with the current plan."""
    llm_plan = llm_output.iteration_plan

    changed_stages = set()
    preserved = set(llm_plan.preserved_stages) if llm_plan else set()
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

    # Build the revised plan sections
    revised = RevisedWorkflowPlan(
        task_summary=plan_dict.get("task_summary"),
        data_strategy=plan_dict.get("data_strategy"),
        feature_strategy=_apply_change(
            plan_dict.get("feature_strategy"), TargetStage.FEATURE_ENGINEERING, stage_map
        ),
        model_strategy=_apply_change(
            plan_dict.get("model_strategy"), TargetStage.MODEL_SEARCH, stage_map
        ),
        hpo_strategy=_apply_change(
            plan_dict.get("hpo_strategy"), TargetStage.PIPELINE_GENERATION, stage_map
        ),
        validation_strategy=_apply_change(
            plan_dict.get("validation_strategy"), TargetStage.PIPELINE_EXECUTION, stage_map
        ),
        evaluation_strategy=_apply_change(
            plan_dict.get("evaluation_strategy"), TargetStage.METRIC_EVALUATION, stage_map
        ),
        changed_sections=sorted(changed_stages),
        preserved_sections=sorted(preserved),
        llm_reasoning_summary=llm_output.reasoning.final_reasoning_summary,
    )

    return revised


def _apply_change(
    original: Any, stage: str, stage_map: Dict[str, Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Apply stage change metadata to the original strategy dict."""
    result = dict(original) if isinstance(original, dict) else {}
    if stage in stage_map:
        result["_iteration_change"] = stage_map[stage]
    else:
        result["_iteration_change"] = {"action": "keep", "description": "No changes requested.", "rationale": ""}
    return result if result else None


def _build_rerun_plan(
    llm_plan: Any, system_checks: SystemChecks, history: Dict[str, Any]
) -> IterationRerunPlan:
    """Build the concrete re-run instructions."""
    if llm_plan is None:
        return IterationRerunPlan()

    n_iter = history.get("n_iterations_completed", 0)
    next_index = n_iter + 1

    rerun_from = llm_plan.rerun_from_stage

    # Determine which stages to rerun (sequential from rerun_from)
    stage_order = [
        TargetStage.WORKFLOW_PLANNING,
        TargetStage.FEATURE_ENGINEERING,
        TargetStage.FEATURE_PREPROCESSING,
        TargetStage.MODEL_SEARCH_CONTEXT,
        TargetStage.MODEL_SEARCH,
        TargetStage.PIPELINE_GENERATION,
        TargetStage.PIPELINE_EXECUTION,
        TargetStage.METRIC_EVALUATION,
    ]

    rerun_stages = []
    found = False
    for s in stage_order:
        if s == rerun_from:
            found = True
        if found:
            rerun_stages.append(s)

    # Determine artifact reusability
    reuse = []
    invalidate = []
    for s in stage_order:
        if s in rerun_stages:
            invalidate.append(f"{s}_artifact")
        else:
            reuse.append(f"{s}_artifact")

    # Add specific reusable items
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
