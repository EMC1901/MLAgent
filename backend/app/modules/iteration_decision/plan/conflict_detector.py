from typing import List, Optional

from app.modules.iteration_decision.schemas import IterationPlan


CONFLICT_PAIRS = [
    ({"expand_features", "add_features"}, {"reduce_dimensionality", "feature_selection", "reduce_features"}),
    ({"increase_hpo"}, {"reduce_hpo_budget"}),
    ({"add_models"}, {"reduce_models"}),
]


def detect_conflicts(
    iteration_plan: IterationPlan,
    effective_rerun_from_stage: Optional[str] = None,
) -> List[str]:
    """Detect semantic conflicts between stage changes."""
    conflicts: List[str] = []

    if not iteration_plan or not iteration_plan.stage_changes:
        return conflicts

    actions_by_stage: dict[str, set[str]] = {}
    for stage_change in iteration_plan.stage_changes:
        actions_by_stage.setdefault(stage_change.stage, set()).add(stage_change.action)

    for stage, actions in actions_by_stage.items():
        for set_a, set_b in CONFLICT_PAIRS:
            if actions & set_a and actions & set_b:
                conflicts.append(
                    f"Stage '{stage}': conflicting actions {actions & set_a} vs {actions & set_b}."
                )

    all_actions: set[str] = set()
    for actions in actions_by_stage.values():
        all_actions |= actions

    if "expand_features" in all_actions and "reduce_dimensionality" in all_actions:
        conflicts.append(
            "Global conflict: expand_features in one stage but reduce_dimensionality "
            "in another; these strategies may work against each other."
        )

    rerun_from_stage = effective_rerun_from_stage or iteration_plan.rerun_from_stage
    if rerun_from_stage:
        stages_after_rerun: set[str] = set()
        stage_order = [
            "workflow_planning",
            "feature_engineering",
            "feature_preprocessing",
            "model_search_context",
            "pipeline_generation",
            "pipeline_execution",
            "metric_evaluation",
        ]
        found = False
        for stage in stage_order:
            if stage == rerun_from_stage:
                found = True
            if found:
                stages_after_rerun.add(stage)

        for stage_change in iteration_plan.stage_changes:
            if (
                stage_change.stage not in stages_after_rerun
                and stage_change.stage not in iteration_plan.preserved_stages
            ):
                conflicts.append(
                    f"Stage '{stage_change.stage}' has changes but is before effective "
                    f"rerun_from_stage '{rerun_from_stage}'; changes may not take effect."
                )

    return conflicts
