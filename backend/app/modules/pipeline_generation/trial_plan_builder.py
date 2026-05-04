import uuid
import logging
from app.modules.pipeline_generation.schemas import (
    TrialPlan,
    TrialAllocationItem,
    BaselineTrialPolicy,
    CandidateTrialPolicy,
    EarlyStoppingPolicy,
    FallbackPolicy,
)
from app.modules.pipeline_generation.enums import PipelineRole
from app.modules.pipeline_generation.exceptions import PipelineSpecBuildException

logger = logging.getLogger(__name__)


def build_trial_plan(context: dict, pipeline_specs: list) -> TrialPlan:
    """Build TrialPlan from upstream HPO plan and generated pipeline specs."""
    pg_input = context.get("pipeline_generation_input", {})
    hpo_plan = pg_input.get("hpo_plan", {})

    plan_id = f"tp_{uuid.uuid4().hex[:8]}"

    hpo_enabled = hpo_plan.get("enabled", False)
    search_method = hpo_plan.get("search_method") or hpo_plan.get("method")
    max_total_trials = hpo_plan.get("max_total_trials", 30)
    max_parallel_trials = hpo_plan.get("max_parallel_trials", 1)

    # Map existing trial allocations from HPO plan
    existing_allocations = hpo_plan.get("trial_allocation", [])
    allocation_map = {}
    for a in existing_allocations:
        allocation_map[a.get("model_id")] = a.get("max_trials", 0)

    trial_allocation = []
    for spec in pipeline_specs:
        spec_dict = spec if isinstance(spec, dict) else spec.model_dump()
        model_id = spec_dict.get("model_id", "")
        role = spec_dict.get("pipeline_role", "")

        if role == PipelineRole.BASELINE:
            max_trials = 1
        elif spec_dict.get("hpo_enabled", False):
            max_trials = allocation_map.get(model_id, max_total_trials // max(len(pipeline_specs), 1))
        else:
            max_trials = 1

        trial_allocation.append(TrialAllocationItem(
            model_id=model_id,
            pipeline_spec_id=spec_dict.get("pipeline_spec_id"),
            max_trials=max_trials,
            role=role,
        ))

    early_stopping = hpo_plan.get("early_stopping", False)
    fallback_method = hpo_plan.get("fallback_method")

    return TrialPlan(
        trial_plan_id=plan_id,
        hpo_enabled=hpo_enabled,
        search_method=search_method,
        max_total_trials=max_total_trials,
        max_parallel_trials=max_parallel_trials,
        trial_allocation=trial_allocation,
        baseline_trial_policy=BaselineTrialPolicy(
            single_run=True,
        ),
        candidate_trial_policy=CandidateTrialPolicy(
            expand_by_search_space=hpo_enabled,
        ),
        early_stopping_policy=EarlyStoppingPolicy(
            enabled=early_stopping,
        ),
        fallback_policy=FallbackPolicy(
            enabled=True,
            fallback_model_id=fallback_method,
        ),
    )
