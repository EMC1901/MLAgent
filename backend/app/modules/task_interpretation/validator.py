from typing import Dict, Any, List


ALLOWED_TASK_TYPES = {"regression", "classification", "ranking", "unknown"}
ALLOWED_INPUT_MODALITIES = {"composition", "structure", "descriptor", "text", "mixed"}
ALLOWED_TARGET_CATEGORIES = {
    "electronic_property", "mechanical_property", "thermal_property",
    "optical_property", "magnetic_property", "structural_property",
    "chemical_property", "other",
}
ALLOWED_PRIMARY_GOALS = {
    "property_prediction", "material_screening", "classification",
    "ranking", "interpretability_analysis", "benchmark_comparison",
}

REQUIRED_TOP_LEVEL_KEYS = [
    "interpreted_task_type",
    "interpreted_input_modality",
    "interpreted_material_domain",
    "interpreted_prediction_target",
    "modeling_intent",
    "dataset_intent",
    "planning_hint",
    "constraint_interpretation",
    "recommended_defaults",
    "ambiguities",
    "warnings",
    "llm_reasoning_summary",
    "confidence_score",
]


def validate_interpretation(data: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            errors.append(f"Missing required field: {key}")

    if "interpreted_task_type" in data and data["interpreted_task_type"] not in ALLOWED_TASK_TYPES:
        errors.append(f"Invalid interpreted_task_type: {data['interpreted_task_type']}")

    if "interpreted_input_modality" in data and data["interpreted_input_modality"] not in ALLOWED_INPUT_MODALITIES:
        errors.append(f"Invalid interpreted_input_modality: {data['interpreted_input_modality']}")

    if "interpreted_prediction_target" in data:
        target = data["interpreted_prediction_target"]
        if isinstance(target, dict):
            cat = target.get("target_category")
            if cat and cat not in ALLOWED_TARGET_CATEGORIES:
                errors.append(f"Invalid target_category: {cat}")

    if "modeling_intent" in data:
        intent = data["modeling_intent"]
        if isinstance(intent, dict):
            goal = intent.get("primary_goal")
            if goal and goal not in ALLOWED_PRIMARY_GOALS:
                errors.append(f"Invalid primary_goal: {goal}")

    if "confidence_score" in data:
        cs = data["confidence_score"]
        if not isinstance(cs, (int, float)) or cs < 0 or cs > 1:
            errors.append(f"confidence_score must be a number between 0 and 1, got: {cs}")

    if "ambiguities" in data and not isinstance(data["ambiguities"], list):
        errors.append("ambiguities must be an array")

    if "warnings" in data and not isinstance(data["warnings"], list):
        errors.append("warnings must be an array")

    is_valid = len(errors) == 0
    return {"is_valid": is_valid, "errors": errors}
