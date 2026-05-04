import logging
from app.modules.pipeline_generation.schemas import PipelineValidationResult
from app.modules.pipeline_generation.component_registry import (
    is_valid_model_family,
    is_valid_hpo_method,
    is_valid_validation_strategy,
    is_valid_metric,
)
from app.shared.registry.model_registry import get_model_spec
from app.shared.registry.hpo_registry import get_hpo_method_spec

logger = logging.getLogger(__name__)


def validate_pipeline_bundle(context: dict, pipeline_specs: list, trial_plan, artifact_manifest, binding_result) -> PipelineValidationResult:
    """Validate all aspects of the generated pipeline bundle."""
    result = PipelineValidationResult()
    errors = []
    warnings = []

    specs = [s if isinstance(s, dict) else s.model_dump() for s in pipeline_specs]

    # --- Structure validation ---
    structure_errors = []
    for spec in specs:
        required_fields = ["pipeline_spec_id", "pipeline_role", "model_id"]
        for f in required_fields:
            if not spec.get(f):
                structure_errors.append(f"Missing required field '{f}' in spec {spec.get('pipeline_spec_id', '?')}.")
    result.structure_valid = len(structure_errors) == 0
    if structure_errors:
        errors.extend(structure_errors)

    # --- Registry validation ---
    registry_errors = []
    for spec in specs:
        model_id = spec.get("model_id", "")
        model_family = spec.get("model_family", "")
        if not is_valid_model_family(model_family) and not is_valid_model_family(model_id):
            registry_errors.append(f"Model '{model_id}' (family: {model_family}) not in Model Registry.")

    if trial_plan:
        tp = trial_plan if isinstance(trial_plan, dict) else trial_plan.model_dump()
        hpo_method = tp.get("search_method")
        if hpo_method and not is_valid_hpo_method(hpo_method):
            registry_errors.append(f"HPO method '{hpo_method}' not in HPO Registry.")

    result.registry_valid = len(registry_errors) == 0
    if registry_errors:
        errors.extend(registry_errors)

    # --- Artifact validation ---
    artifact_errors = []
    if artifact_manifest:
        am = artifact_manifest if isinstance(artifact_manifest, dict) else artifact_manifest.model_dump()
        if not am.get("model_ready_exists"):
            artifact_errors.append("Model ready artifact does not exist.")
        if am.get("preprocessor_artifact_path") and not am.get("preprocessor_exists"):
            artifact_errors.append("Preprocessor artifact does not exist but path was specified.")

    result.artifact_valid = len(artifact_errors) == 0
    if artifact_errors:
        errors.extend(artifact_errors)

    # --- Task type compatibility ---
    task_type = context.get("task_type", "regression")
    task_type_errors = []
    for spec in specs:
        model_id = spec.get("model_id", "")
        model_spec = get_model_spec(model_id) or get_model_spec(spec.get("model_family", ""))
        if model_spec and task_type not in model_spec.get("supported_task_types", []):
            task_type_errors.append(f"Model '{model_id}' does not support task type '{task_type}'.")
    result.task_type_compatible = len(task_type_errors) == 0
    if task_type_errors:
        errors.extend(task_type_errors)

    # --- Search space validation ---
    search_space_errors = []
    for spec in specs:
        if spec.get("hpo_enabled") and not spec.get("search_space"):
            search_space_errors.append(f"HPO enabled for '{spec.get('model_id')}' but no search space provided.")
    result.search_space_valid = len(search_space_errors) == 0
    if search_space_errors:
        warnings.extend(search_space_errors)

    # --- Trial validation ---
    trial_errors = []
    if trial_plan:
        tp = trial_plan if isinstance(trial_plan, dict) else trial_plan.model_dump()
        if tp.get("max_total_trials", 0) <= 0:
            trial_errors.append("Max total trials must be > 0.")
    result.trial_valid = len(trial_errors) == 0
    if trial_errors:
        errors.extend(trial_errors)

    # --- Data fields validation ---
    data_errors = []
    feature_columns = context.get("feature_columns", [])
    target_column = context.get("target_column")
    if not feature_columns:
        data_errors.append("Feature columns list is empty.")
    if not target_column:
        data_errors.append("Target column is not set.")
    result.data_fields_valid = len(data_errors) == 0
    if data_errors:
        errors.extend(data_errors)

    # --- Execution input valid ---
    result.execution_input_valid = result.structure_valid and result.registry_valid and result.data_fields_valid

    result.errors = errors
    result.warnings = warnings
    result.is_valid = len(errors) == 0

    return result
