from typing import List
from app.shared.registry.model_registry import (
    get_all_model_families,
    is_valid_model_family,
    get_model_spec,
)
from app.shared.registry.hpo_registry import (
    get_all_hpo_methods,
    is_valid_hpo_method,
    get_hpo_method_spec,
)
from app.modules.pipeline_generation.enums import ComponentType

# Whitelist of allowed validation strategies
VALIDATION_STRATEGIES = {
    "k_fold_cross_validation",
    "train_test_split",
    "stratified_k_fold",
    "repeated_cv",
}

# Whitelist of allowed metrics
ALLOWED_METRICS = {
    "mae", "mse", "rmse", "r2", "r2_score",
    "accuracy", "precision", "recall", "f1", "f1_score",
    "roc_auc", "average_precision",
}


def get_allowed_model_families() -> List[str]:
    return get_all_model_families()


def get_allowed_hpo_methods() -> List[str]:
    return get_all_hpo_methods()


def get_allowed_validation_strategies() -> List[str]:
    return sorted(VALIDATION_STRATEGIES)


def get_allowed_metrics() -> List[str]:
    return sorted(ALLOWED_METRICS)


def is_valid_validation_strategy(strategy: str) -> bool:
    return strategy.lower() in VALIDATION_STRATEGIES


def is_valid_metric(metric: str) -> bool:
    return metric.lower() in ALLOWED_METRICS


def get_component_capability(component_type: str) -> dict:
    capabilities = {
        ComponentType.INPUT_LOADER: {
            "description": "Loads model-ready feature matrix.",
            "allowed_inputs": [".parquet", ".csv"],
        },
        ComponentType.PREPROCESSOR: {
            "description": "Loads preprocessor artifact for inference reproducibility.",
            "allowed_inputs": [".joblib", ".pkl"],
        },
        ComponentType.ESTIMATOR: {
            "description": "Instantiates a registered estimator from Model Registry.",
            "requires_registry": True,
        },
        ComponentType.VALIDATION_SPLITTER: {
            "description": "Splits data for cross-validation.",
            "allowed_strategies": sorted(VALIDATION_STRATEGIES),
        },
        ComponentType.METRIC_EVALUATOR: {
            "description": "Computes evaluation metrics.",
            "allowed_metrics": sorted(ALLOWED_METRICS),
        },
        ComponentType.HPO_CONTROLLER: {
            "description": "Controls hyperparameter optimization execution.",
            "allowed_methods": get_all_hpo_methods(),
        },
    }
    return capabilities.get(component_type, {})
