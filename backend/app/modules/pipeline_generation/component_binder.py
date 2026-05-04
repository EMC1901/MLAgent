import logging
from app.modules.pipeline_generation.schemas import ComponentBinding, ComponentBindingResult
from app.modules.pipeline_generation.component_registry import (
    is_valid_validation_strategy,
    is_valid_metric,
)
from app.modules.pipeline_generation.exceptions import ComponentBindingException
from app.shared.registry.model_registry import is_valid_model_family, get_model_spec
from app.shared.registry.hpo_registry import is_valid_hpo_method

logger = logging.getLogger(__name__)


def bind_components(context: dict) -> ComponentBindingResult:
    """Bind model, HPO, validation, evaluation, and artifact components
    from the upstream plan to system Registry entries.
    """
    pg_input = context.get("pipeline_generation_input", {})
    candidate_model_plan = pg_input.get("candidate_model_plan", {})
    hpo_plan = pg_input.get("hpo_plan", {})
    validation_plan = pg_input.get("validation_plan", {})
    evaluation_plan = pg_input.get("evaluation_plan", {})

    bindings = []
    errors = []

    # Collect all models: baseline + candidate
    all_models = []
    for b in candidate_model_plan.get("baseline_models", []):
        all_models.append(b)
    for c in candidate_model_plan.get("candidate_models", []):
        all_models.append(c)

    if not all_models:
        raise ComponentBindingException("No models found in candidate model plan.")

    hpo_method = hpo_plan.get("search_method") or hpo_plan.get("method")
    primary_metric = evaluation_plan.get("primary_metric") or context.get("primary_metric", "MAE")
    validation_strategy = validation_plan.get("split_strategy", "k_fold_cross_validation")

    # Validate shared components
    hpo_registry_valid = is_valid_hpo_method(hpo_method) if hpo_method else False
    metric_valid = is_valid_metric(primary_metric)
    validation_strategy_valid = is_valid_validation_strategy(validation_strategy)

    for model_entry in all_models:
        model_id = model_entry.get("model_id") if isinstance(model_entry, dict) else getattr(model_entry, "model_id", None)
        if not model_id:
            continue

        model_family = model_entry.get("model_family") if isinstance(model_entry, dict) else getattr(model_entry, "model_family", None)
        if not model_family:
            model_spec = get_model_spec(model_id) or get_model_spec(model_id.split("_")[0] if "_" in model_id else model_id)
            if model_spec:
                model_family = model_spec["family"]
            else:
                model_family = model_id

        model_registry_valid = is_valid_model_family(model_family) or is_valid_model_family(model_id)
        hpo_enabled = model_entry.get("hpo_enabled", False) if isinstance(model_entry, dict) else getattr(model_entry, "hpo_enabled", False)
        hpo_valid = hpo_registry_valid if hpo_enabled else True

        binding = ComponentBinding(
            model_id=model_id,
            model_family=model_family,
            model_registry_valid=model_registry_valid,
            hpo_method=hpo_method,
            hpo_registry_valid=hpo_valid,
            validation_strategy=validation_strategy,
            validation_strategy_valid=validation_strategy_valid,
            primary_metric=primary_metric,
            metric_valid=metric_valid,
            preprocessor_artifact_bound=bool(context.get("preprocessor_artifact_path")),
            model_ready_matrix_bound=bool(context.get("model_ready_matrix_path")),
        )

        if not model_registry_valid:
            errors.append(f"Model '{model_id}' not found in Model Registry.")
        if hpo_enabled and not hpo_valid:
            errors.append(f"HPO method '{hpo_method}' not found in HPO Registry for model '{model_id}'.")
        if not validation_strategy_valid:
            errors.append(f"Validation strategy '{validation_strategy}' not in allowed list.")
        if not metric_valid:
            errors.append(f"Metric '{primary_metric}' not in allowed list.")

        bindings.append(binding)

    all_valid = len(errors) == 0 and all(
        b.model_registry_valid and b.metric_valid and b.validation_strategy_valid
        for b in bindings
    )

    return ComponentBindingResult(
        bindings=bindings,
        all_valid=all_valid,
        errors=errors,
    )
