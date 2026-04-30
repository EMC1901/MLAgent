from typing import Dict, Any


TASK_TYPE_MAPPING = {
    "regression": "regression",
    "classification": "classification",
    "ranking": "ranking",
}

INPUT_TYPE_MAPPING = {
    "chemical composition": "composition",
    "composition": "composition",
    "crystal structure": "structure",
    "structure": "structure",
    "descriptor table": "descriptor_table",
    "text-derived features": "text_features",
    "text features": "text_features",
}

EVALUATION_METRIC_MAPPING = {
    "mean absolute error": "MAE",
    "mae": "MAE",
    "root mean squared error": "RMSE",
    "rmse": "RMSE",
    "r-squared": "R2",
    "r2": "R2",
    "accuracy": "Accuracy",
    "f1 score": "F1",
    "f1": "F1",
    "roc-auc": "ROC-AUC",
    "spearman": "Spearman",
    "ndcg": "NDCG",
    "top-k recall": "Top-k recall",
}

USER_PRIORITY_MAPPING = {
    "accuracy": "accuracy",
    "interpretability": "interpretability",
    "speed": "speed",
    "robustness": "robustness",
}


def normalize_task_type(value: str) -> str:
    if not value:
        return value
    return TASK_TYPE_MAPPING.get(value.strip().lower(), value.strip().lower())


def normalize_input_type(value: str) -> str:
    if not value:
        return value
    return INPUT_TYPE_MAPPING.get(value.strip().lower(), value.strip().lower())


def normalize_evaluation_metric(value: str) -> str:
    if not value:
        return value
    return EVALUATION_METRIC_MAPPING.get(value.strip().lower(), value.strip())


def normalize_user_priority(values: list) -> list:
    if not values:
        return []
    normalized = []
    for v in values:
        n = USER_PRIORITY_MAPPING.get(v.strip().lower(), v.strip().lower())
        normalized.append(n)
    return normalized


def normalize_fields(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {}

    if raw_data.get("task_type"):
        normalized["task_type"] = normalize_task_type(raw_data["task_type"])

    if raw_data.get("input_type"):
        normalized["input_type"] = normalize_input_type(raw_data["input_type"])

    if raw_data.get("evaluation_metric"):
        normalized["evaluation_metric"] = normalize_evaluation_metric(raw_data["evaluation_metric"])

    if raw_data.get("user_priority") is not None:
        normalized["user_priority"] = normalize_user_priority(raw_data["user_priority"])

    for key in ["task_name", "task_description", "material_system", "prediction_target",
                "dataset_description", "target_column", "constraints"]:
        if raw_data.get(key) is not None:
            normalized[key] = raw_data[key].strip() if isinstance(raw_data[key], str) else raw_data[key]

    return normalized
