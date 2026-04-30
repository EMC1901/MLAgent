from typing import Dict, Any, List, Tuple


REGRESSION_METRICS = {"MAE", "RMSE", "R2"}
CLASSIFICATION_METRICS = {"Accuracy", "F1", "ROC-AUC"}
RANKING_METRICS = {"Spearman", "NDCG", "Top-k recall"}

TASK_METRIC_MAP = {
    "regression": REGRESSION_METRICS,
    "classification": CLASSIFICATION_METRICS,
    "ranking": RANKING_METRICS,
}

CONTINUOUS_PROPERTIES = {
    "band gap", "formation energy", "elastic modulus", "young's modulus",
    "shear modulus", "bulk modulus", "thermal conductivity", "heat capacity",
}


def check_required_fields(normalized_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    missing_fields = []
    validation_messages = []

    if not normalized_data.get("prediction_target"):
        missing_fields.append("prediction_target")
        validation_messages.append("Please specify the material property to be predicted.")

    if not normalized_data.get("task_type"):
        missing_fields.append("task_type")
        validation_messages.append("Please select the machine learning task type.")

    if not normalized_data.get("dataset_description"):
        missing_fields.append("dataset_description")
        validation_messages.append("Please provide the dataset description.")

    if not normalized_data.get("input_type"):
        missing_fields.append("input_type")
        validation_messages.append("Please select the input data type.")

    if not normalized_data.get("target_column"):
        missing_fields.append("target_column")
        validation_messages.append("Please specify the target column in the dataset.")

    return missing_fields, validation_messages


def check_evaluation_metric_compatibility(normalized_data: Dict[str, Any]) -> List[str]:
    validation_messages = []

    task_type = normalized_data.get("task_type")
    evaluation_metric = normalized_data.get("evaluation_metric")

    if task_type and evaluation_metric:
        valid_metrics = TASK_METRIC_MAP.get(task_type, set())
        if evaluation_metric not in valid_metrics:
            valid_metrics_str = ", ".join(sorted(valid_metrics))
            validation_messages.append(
                f"{evaluation_metric} is not suitable for {task_type} tasks. "
                f"Please select {valid_metrics_str}."
            )

    return validation_messages


def check_input_dataset_consistency(normalized_data: Dict[str, Any]) -> List[str]:
    validation_messages = []

    input_type = normalized_data.get("input_type")
    dataset_description = normalized_data.get("dataset_description", "").lower()

    if input_type == "structure":
        structure_indicators = ["cif", "poscar", "structure", "crystal"]
        has_structure_source = any(ind in dataset_description for ind in structure_indicators)
        if not has_structure_source and dataset_description:
            validation_messages.append(
                "Please specify where the structure data is provided, "
                "such as CIF files, POSCAR files, or a structure column."
            )

    if input_type == "composition":
        if any(ind in dataset_description for ind in ["cif", "poscar", "structure"]) and "composition" not in dataset_description:
            validation_messages.append(
                "Dataset appears to contain structure files, but input type is composition. "
                "Please verify the input type matches the dataset."
            )

    return validation_messages


def check_evaluation_metric_provided(normalized_data: Dict[str, Any]) -> List[str]:
    warnings = []

    if not normalized_data.get("evaluation_metric"):
        warnings.append("No evaluation metric is specified. A default metric may be used later.")

    return warnings


def validate(normalized_data: Dict[str, Any]) -> Dict[str, Any]:
    missing_fields, validation_messages = check_required_fields(normalized_data)

    compatibility_messages = check_evaluation_metric_compatibility(normalized_data)
    validation_messages.extend(compatibility_messages)

    consistency_messages = check_input_dataset_consistency(normalized_data)
    validation_messages.extend(consistency_messages)

    warnings = check_evaluation_metric_provided(normalized_data)

    if missing_fields:
        status = "incomplete"
    elif validation_messages and any(
        "not suitable" in msg or "Please specify" in msg for msg in validation_messages
    ):
        status = "invalid"
    elif warnings:
        status = "valid_with_warning"
    else:
        status = "valid"

    return {
        "status": status,
        "missing_fields": missing_fields,
        "validation_messages": validation_messages,
        "warnings": warnings,
    }
