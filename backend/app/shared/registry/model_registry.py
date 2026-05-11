from typing import List, Optional

MODEL_FAMILIES: List[dict] = [
    {
        "family": "dummy_mean",
        "display_name": "Dummy Mean Predictor",
        "supported_task_types": ["regression", "classification"],
        "requires_scaling": False,
        "supports_regression": True,
        "supports_classification": True,
        "complexity_level": "baseline",
        "interpretability_level": "high",
    },
    {
        "family": "linear_regression",
        "display_name": "Linear Regression",
        "supported_task_types": ["regression"],
        "requires_scaling": True,
        "supports_regression": True,
        "supports_classification": False,
        "complexity_level": "simple",
        "interpretability_level": "high",
    },
    {
        "family": "ridge",
        "display_name": "Ridge Regression",
        "supported_task_types": ["regression"],
        "requires_scaling": True,
        "supports_regression": True,
        "supports_classification": False,
        "complexity_level": "simple",
        "interpretability_level": "high",
    },
    {
        "family": "lasso",
        "display_name": "Lasso Regression",
        "supported_task_types": ["regression"],
        "requires_scaling": True,
        "supports_regression": True,
        "supports_classification": False,
        "complexity_level": "simple",
        "interpretability_level": "high",
    },
    {
        "family": "elastic_net",
        "display_name": "Elastic Net",
        "supported_task_types": ["regression"],
        "requires_scaling": True,
        "supports_regression": True,
        "supports_classification": False,
        "complexity_level": "moderate",
        "interpretability_level": "high",
    },
    {
        "family": "random_forest",
        "display_name": "Random Forest",
        "supported_task_types": ["regression", "classification"],
        "requires_scaling": False,
        "supports_regression": True,
        "supports_classification": True,
        "complexity_level": "moderate",
        "interpretability_level": "medium",
    },
    {
        "family": "gradient_boosting",
        "display_name": "Gradient Boosting",
        "supported_task_types": ["regression", "classification"],
        "requires_scaling": False,
        "supports_regression": True,
        "supports_classification": True,
        "complexity_level": "high",
        "interpretability_level": "medium",
    },
    {
        "family": "xgboost",
        "display_name": "XGBoost",
        "supported_task_types": ["regression", "classification"],
        "requires_scaling": False,
        "supports_regression": True,
        "supports_classification": True,
        "complexity_level": "high",
        "interpretability_level": "medium",
    },
    {
        "family": "svr",
        "display_name": "Support Vector Regression",
        "supported_task_types": ["regression"],
        "requires_scaling": True,
        "supports_regression": True,
        "supports_classification": False,
        "complexity_level": "moderate",
        "interpretability_level": "low",
    },
    {
        "family": "svc",
        "display_name": "Support Vector Classification",
        "supported_task_types": ["classification"],
        "requires_scaling": True,
        "supports_regression": False,
        "supports_classification": True,
        "complexity_level": "moderate",
        "interpretability_level": "low",
    },
    {
        "family": "logistic_regression",
        "display_name": "Logistic Regression",
        "supported_task_types": ["classification"],
        "requires_scaling": True,
        "supports_regression": False,
        "supports_classification": True,
        "complexity_level": "simple",
        "interpretability_level": "high",
    },
    {
        "family": "knn",
        "display_name": "K-Nearest Neighbors",
        "supported_task_types": ["regression", "classification"],
        "requires_scaling": True,
        "supports_regression": True,
        "supports_classification": True,
        "complexity_level": "simple",
        "interpretability_level": "medium",
    },
    {
        "family": "gaussian_process",
        "display_name": "Gaussian Process",
        "supported_task_types": ["regression"],
        "requires_scaling": True,
        "supports_regression": True,
        "supports_classification": False,
        "complexity_level": "high",
        "interpretability_level": "medium",
    },
    {
        "family": "decision_tree",
        "display_name": "Decision Tree",
        "supported_task_types": ["regression", "classification"],
        "requires_scaling": False,
        "supports_regression": True,
        "supports_classification": True,
        "complexity_level": "simple",
        "interpretability_level": "high",
    },
    {
        "family": "lightgbm",
        "display_name": "LightGBM",
        "supported_task_types": ["regression", "classification"],
        "requires_scaling": False,
        "supports_regression": True,
        "supports_classification": True,
        "complexity_level": "high",
        "interpretability_level": "medium",
    },
    {
        "family": "mlp",
        "display_name": "Multi-Layer Perceptron",
        "supported_task_types": ["regression", "classification"],
        "requires_scaling": True,
        "supports_regression": True,
        "supports_classification": True,
        "complexity_level": "high",
        "interpretability_level": "low",
    },
    {
        "family": "extra_trees",
        "display_name": "Extra Trees",
        "supported_task_types": ["regression", "classification"],
        "requires_scaling": False,
        "supports_regression": True,
        "supports_classification": True,
        "complexity_level": "moderate",
        "interpretability_level": "medium",
    },
]


def get_all_model_families() -> List[str]:
    return [m["family"] for m in MODEL_FAMILIES]


def get_model_families_for_task_type(task_type: str) -> List[str]:
    return [m["family"] for m in MODEL_FAMILIES if task_type in m["supported_task_types"]]


def is_valid_model_family(family: str) -> bool:
    return family in get_all_model_families()


def get_model_spec(family: str) -> Optional[dict]:
    for m in MODEL_FAMILIES:
        if m["family"] == family:
            return m
    return None


def get_baseline_models(task_type: str) -> List[str]:
    baselines = []
    for m in MODEL_FAMILIES:
        if m["complexity_level"] == "baseline" and task_type in m["supported_task_types"]:
            baselines.append(m["family"])
    return baselines
