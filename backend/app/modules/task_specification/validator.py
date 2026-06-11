from typing import Dict, Any, List, Literal

Severity = Literal["error", "warning"]
Issue = tuple[Severity, str]

REGRESSION_METRICS = {"MAE", "RMSE", "R2"}
CLASSIFICATION_METRICS = {"Accuracy", "F1", "ROC-AUC"}
RANKING_METRICS = {"Spearman", "NDCG", "Top-k recall"}

UNSUPPORTED_METRICS = {"Spearman", "NDCG", "Top-k recall"}
UNSUPPORTED_METRIC_MSG = (
    "{metric} is a ranking metric and is not yet supported. "
    "Please select a supported metric: MAE, RMSE, R2 (regression) "
    "or Accuracy, F1, ROC-AUC (classification)."
)

TASK_METRIC_MAP = {
    "regression": REGRESSION_METRICS,
    "classification": CLASSIFICATION_METRICS,
    "ranking": RANKING_METRICS,
}


def check_required_fields(normalized_data: Dict[str, Any]) -> tuple[List[str], List[Issue]]:
    missing_fields: List[str] = []
    issues: List[Issue] = []

    checks = [
        ("prediction_target", "Please specify the material property to be predicted."),
        ("task_type", "Please select the machine learning task type."),
        ("dataset_description", "Please provide the dataset description."),
        ("input_type", "Please select the input data type."),
        ("target_column", "Please specify the target column in the dataset."),
    ]

    for field, message in checks:
        if not normalized_data.get(field):
            missing_fields.append(field)
            issues.append(("error", message))

    return missing_fields, issues


def check_evaluation_metric_compatibility(normalized_data: Dict[str, Any]) -> List[Issue]:
    issues: List[Issue] = []

    task_type = normalized_data.get("task_type")
    evaluation_metric = normalized_data.get("evaluation_metric")

    if task_type and evaluation_metric:
        valid_metrics = TASK_METRIC_MAP.get(task_type, set())
        if evaluation_metric not in valid_metrics:
            valid_metrics_str = ", ".join(sorted(valid_metrics))
            issues.append(("error",
                f"{evaluation_metric} is not suitable for {task_type} tasks. "
                f"Please select {valid_metrics_str}."
            ))

    return issues


def check_input_dataset_consistency(normalized_data: Dict[str, Any]) -> List[Issue]:
    issues: List[Issue] = []

    input_type = normalized_data.get("input_type")
    dataset_description = normalized_data.get("dataset_description", "").lower()

    if input_type == "structure":
        structure_indicators = ["cif", "poscar", "structure", "crystal"]
        has_structure_source = any(ind in dataset_description for ind in structure_indicators)
        if not has_structure_source and dataset_description:
            issues.append(("error",
                "Please specify where the structure data is provided, "
                "such as CIF files, POSCAR files, or a structure column."
            ))

    if input_type == "composition":
        if any(ind in dataset_description for ind in ["cif", "poscar", "structure"]) and "composition" not in dataset_description:
            issues.append(("warning",
                "Dataset appears to contain structure files, but input type is composition. "
                "Please verify the input type matches the dataset."
            ))

    return issues


def check_evaluation_metric_provided(normalized_data: Dict[str, Any]) -> List[Issue]:
    if not normalized_data.get("evaluation_metric"):
        return [("warning", "No evaluation metric is specified. A default metric may be used later.")]
    return []


def check_unsupported_metrics(normalized_data: Dict[str, Any]) -> List[Issue]:
    """Reject ranking metrics that are not yet implemented in the backend."""
    metric = normalized_data.get("evaluation_metric")
    if metric and metric in UNSUPPORTED_METRICS:
        return [("error", UNSUPPORTED_METRIC_MSG.format(metric=metric))]
    return []


def check_ranking_task_type(normalized_data: Dict[str, Any]) -> List[Issue]:
    """Reject ranking task type as it is not yet supported."""
    task_type = normalized_data.get("task_type")
    if task_type == "ranking":
        return [("error",
            "Ranking tasks are not yet supported. "
            "Please select Regression or Classification as the task type."
        )]
    return []


def validate(normalized_data: Dict[str, Any]) -> Dict[str, Any]:
    missing_fields, required_issues = check_required_fields(normalized_data)
    compat_issues = check_evaluation_metric_compatibility(normalized_data)
    consistency_issues = check_input_dataset_consistency(normalized_data)
    metric_warnings = check_evaluation_metric_provided(normalized_data)
    unsupported_issues = check_unsupported_metrics(normalized_data)
    ranking_task_issues = check_ranking_task_type(normalized_data)

    all_issues = (required_issues + compat_issues + consistency_issues
                  + metric_warnings + unsupported_issues + ranking_task_issues)

    errors = [msg for sev, msg in all_issues if sev == "error"]
    warnings = [msg for sev, msg in all_issues if sev == "warning"]

    if missing_fields:
        status = "incomplete"
    elif errors:
        status = "invalid"
    elif warnings:
        status = "valid_with_warning"
    else:
        status = "valid"

    return {
        "status": status,
        "missing_fields": missing_fields,
        "validation_messages": errors + warnings,
        "warnings": warnings,
    }
