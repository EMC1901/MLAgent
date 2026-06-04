from typing import List
from app.modules.iteration_decision.schemas import StageChange, IterationPlan

# Known conflicting action pairs
CONFLICT_PAIRS = [
    ({"expand_features", "add_features"}, {"reduce_dimensionality", "feature_selection", "reduce_features"}),
    ({"increase_hpo"}, {"reduce_hpo_budget"}),
    ({"add_models"}, {"reduce_models"}),
]


def detect_conflicts(iteration_plan: IterationPlan) -> List[str]:
    """Detect semantic conflicts between stage changes."""
    conflicts: List[str] = []

    if not iteration_plan or not iteration_plan.stage_changes:
        return conflicts

    actions_by_stage: dict = {}
    for sc in iteration_plan.stage_changes:
        actions_by_stage.setdefault(sc.stage, set()).add(sc.action)

    for stage, actions in actions_by_stage.items():
        for set_a, set_b in CONFLICT_PAIRS:
            if actions & set_a and actions & set_b:
                conflicts.append(f"Stage '{stage}': conflicting actions {actions & set_a} vs {actions & set_b}.")

    # Check global conflicts: expand features + dimensionality reduction
    all_actions = set()
    for actions in actions_by_stage.values():
        all_actions |= actions

    if "expand_features" in all_actions and "reduce_dimensionality" in all_actions:
        conflicts.append("Global conflict: expand_features in one stage but reduce_dimensionality in another — these strategies may work against each other.")

    # Check that rerun_from_stage is consistent with changes
    if iteration_plan.rerun_from_stage:
        stages_after_rerun = set()
        stage_order = [
            "workflow_planning", "feature_engineering", "feature_preprocessing",
            "model_search_context", "model_search", "pipeline_generation",
            "pipeline_execution", "metric_evaluation",
        ]
        found = False
        for s in stage_order:
            if s == iteration_plan.rerun_from_stage:
                found = True
            if found:
                stages_after_rerun.add(s)

        for sc in iteration_plan.stage_changes:
            if sc.stage not in stages_after_rerun and sc.stage not in iteration_plan.preserved_stages:
                conflicts.append(
                    f"Stage '{sc.stage}' has changes but is before rerun_from_stage "
                    f"'{iteration_plan.rerun_from_stage}' — changes may not take effect."
                )

    return conflicts
