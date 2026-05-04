"""Execution Planner — expands PipelineSpecs + TrialPlan into executable run plans."""

import uuid
from typing import List, Tuple
from app.modules.pipeline_generation.schemas import PipelineSpec, TrialPlan


def expand_execution_plan(
    pipeline_specs: List[PipelineSpec],
    trial_plan: TrialPlan,
    max_trials_override: int = None,
) -> List[dict]:
    """Expand pipeline specs and trial plan into a flat list of trial plans.

    Each entry describes one trial to execute:
        {
            "pipeline_spec_id": str,
            "pipeline_role": str,
            "model_id": str,
            "model_family": str,
            "hpo_enabled": bool,
            "trial_index": int,
            "trial_type": "baseline" | "fixed_params" | "hpo",
            "params": dict,
            "trial_id": str,
        }

    Rules:
    - baseline → 1 trial with fixed_params (or empty params if none)
    - fixed_params candidate → 1 trial with fixed_params
    - hpo_candidate → multiple trials from search_space
    - If max_trials_override is set, reduce (never increase) trial count
    - Skip specs with execution_ready=False
    """
    plans = []
    trial_allocation_map = {
        t.model_id: t.max_trials
        for t in (trial_plan.trial_allocation or [])
    }

    # Build effective max trials per model, respecting override
    global_max = max_trials_override or trial_plan.max_total_trials

    for spec in pipeline_specs:
        if not spec.execution_ready:
            continue

        model_id = spec.model_id
        role = spec.pipeline_role
        hpo_enabled = spec.hpo_enabled and trial_plan.hpo_enabled

        if role == "baseline":
            # Baseline: exactly 1 trial
            params = spec.fixed_params or {}
            trial_id = _make_trial_id(model_id, 1)

            plans.append({
                "pipeline_spec_id": spec.pipeline_spec_id,
                "pipeline_role": role,
                "model_id": model_id,
                "model_family": spec.model_family or model_id,
                "hpo_enabled": False,
                "trial_index": 1,
                "trial_type": "baseline",
                "params": params,
                "trial_id": trial_id,
            })

        elif hpo_enabled and spec.search_space:
            # HPO candidate: multiple trials
            alloc = trial_allocation_map.get(model_id, 5)
            n_trials = min(alloc, global_max) if global_max > 0 else alloc
            if max_trials_override is not None:
                n_trials = min(n_trials, max_trials_override)
            n_trials = max(1, n_trials)

            # Generate HPO parameter sets
            from app.modules.pipeline_execution.hpo_trial_generator import (
                generate_hpo_trials,
            )
            search_method = trial_plan.search_method or "random_search"
            hpo_params = generate_hpo_trials(
                search_space=spec.search_space or {},
                search_method=search_method,
                max_trials=n_trials,
                random_state=trial_plan.trial_plan_id.__hash__() % (2 ** 31) if trial_plan.trial_plan_id else 42,
            )

            for idx, params in enumerate(hpo_params, start=1):
                # Merge fixed_params on top (fixed_params take precedence)
                merged = {**params, **spec.fixed_params}
                trial_id = _make_trial_id(model_id, idx)

                plans.append({
                    "pipeline_spec_id": spec.pipeline_spec_id,
                    "pipeline_role": role,
                    "model_id": model_id,
                    "model_family": spec.model_family or model_id,
                    "hpo_enabled": True,
                    "trial_index": idx,
                    "trial_type": "hpo",
                    "params": merged,
                    "trial_id": trial_id,
                })

        else:
            # Fixed-params candidate: 1 trial
            params = spec.fixed_params or {}
            trial_id = _make_trial_id(model_id, 1)

            plans.append({
                "pipeline_spec_id": spec.pipeline_spec_id,
                "pipeline_role": role,
                "model_id": model_id,
                "model_family": spec.model_family or model_id,
                "hpo_enabled": False,
                "trial_index": 1,
                "trial_type": "fixed_params",
                "params": params,
                "trial_id": trial_id,
            })

    return plans


def _make_trial_id(model_id: str, index: int) -> str:
    short = uuid.uuid4().hex[:6]
    return f"trial_{model_id}_{index:04d}_{short}"
