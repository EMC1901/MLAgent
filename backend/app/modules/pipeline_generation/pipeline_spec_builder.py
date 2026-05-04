import uuid
import logging
from typing import List
from app.modules.pipeline_generation.schemas import PipelineSpec, SafetyConstraints
from app.modules.pipeline_generation.enums import PipelineRole, ModelPriority
from app.modules.pipeline_generation.exceptions import PipelineSpecBuildException
from app.shared.registry.model_registry import get_model_spec

logger = logging.getLogger(__name__)


def build_pipeline_specs(context: dict, include_baselines: bool = True, include_hpo: bool = True) -> List[PipelineSpec]:
    """Generate PipelineSpec for each model in the candidate model plan."""
    pg_input = context.get("pipeline_generation_input", {})
    candidate_model_plan = pg_input.get("candidate_model_plan", {})
    search_space_plan = pg_input.get("search_space_plan", {})
    validation_plan = pg_input.get("validation_plan", {})
    evaluation_plan = pg_input.get("evaluation_plan", {})

    specs = []
    task_type = context.get("task_type", "regression")

    # Process baseline models
    if include_baselines:
        for b in candidate_model_plan.get("baseline_models", []):
            spec = _build_single_spec(
                model_entry=b,
                role=PipelineRole.BASELINE,
                context=context,
                search_space_plan=search_space_plan,
                validation_plan=validation_plan,
                evaluation_plan=evaluation_plan,
            )
            specs.append(spec)

    # Process candidate models
    for c in candidate_model_plan.get("candidate_models", []):
        hpo_enabled = c.get("hpo_enabled", False)
        if not include_hpo and hpo_enabled:
            spec = _build_single_spec(
                model_entry=c,
                role=PipelineRole.CANDIDATE,
                context=context,
                search_space_plan={},
                validation_plan=validation_plan,
                evaluation_plan=evaluation_plan,
            )
            spec.hpo_enabled = False
            spec.search_space = None
            spec.search_space_ref = None
        else:
            role = PipelineRole.HPO_CANDIDATE if hpo_enabled else PipelineRole.CANDIDATE
            spec = _build_single_spec(
                model_entry=c,
                role=role,
                context=context,
                search_space_plan=search_space_plan if hpo_enabled else {},
                validation_plan=validation_plan,
                evaluation_plan=evaluation_plan,
            )
        specs.append(spec)

    if not specs:
        raise PipelineSpecBuildException("No pipeline specs could be generated.")

    return specs


def _build_single_spec(
    model_entry: dict,
    role: str,
    context: dict,
    search_space_plan: dict,
    validation_plan: dict,
    evaluation_plan: dict,
) -> PipelineSpec:
    model_id = model_entry.get("model_id", "unknown")
    model_family = model_entry.get("model_family", model_id)
    model_spec_entry = get_model_spec(model_family) or get_model_spec(model_id)

    spec_id = f"ps_{model_id}_{uuid.uuid4().hex[:6]}"
    priority = model_entry.get("priority", ModelPriority.MEDIUM)
    hpo_enabled = model_entry.get("hpo_enabled", False)

    # Find matching search space
    search_space_ref = None
    search_space = None
    if hpo_enabled:
        for space in search_space_plan.get("spaces", []):
            if space.get("model_id") == model_id:
                search_space_ref = space.get("search_space_id")
                search_space = space
                break

    display_name = model_id
    if model_spec_entry:
        display_name = model_spec_entry.get("display_name", model_id)

    fixed_params = model_entry.get("fixed_params", {})

    component_bindings = {
        "model_id": model_id,
        "model_family": model_family,
        "model_registry_valid": model_spec_entry is not None,
        "preprocessor_artifact_bound": bool(context.get("preprocessor_artifact_path")),
        "model_ready_matrix_bound": bool(context.get("model_ready_matrix_path")),
    }

    safety_constraints = SafetyConstraints(
        max_runtime_seconds=3600,
        max_memory_mb=4096,
    )

    execution_ready = bool(
        model_spec_entry
        and context.get("model_ready_matrix_path")
        and context.get("target_column")
        and context.get("feature_columns")
    )

    return PipelineSpec(
        pipeline_spec_id=spec_id,
        pipeline_role=role,
        model_id=model_id,
        model_family=model_family,
        model_display_name=display_name,
        priority=priority,
        hpo_enabled=hpo_enabled,
        search_space_ref=search_space_ref,
        fixed_params=fixed_params,
        search_space=search_space,
        validation_plan_ref=validation_plan.get("split_strategy", "k_fold_cross_validation"),
        evaluation_plan_ref=evaluation_plan.get("primary_metric", "MAE"),
        input_artifact_ref=context.get("model_ready_matrix_path"),
        preprocessor_artifact_ref=context.get("preprocessor_artifact_path"),
        component_bindings=component_bindings,
        safety_constraints=safety_constraints,
        execution_ready=execution_ready,
        warnings=[],
    )
