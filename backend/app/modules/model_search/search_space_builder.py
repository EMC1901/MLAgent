import logging
from typing import List, Optional
from app.shared.registry.model_registry import get_model_spec
from app.modules.model_search.schemas import SearchSpaceParameter, SearchSpaceItem, SearchSpacePlan
from app.modules.model_search.enums import SearchSpaceProfile, TaskType

logger = logging.getLogger(__name__)

# Search space templates keyed by model family
_SEARCH_SPACE_TEMPLATES: dict = {
    "ridge": {
        "regression": [
            {"name": "alpha", "param_type": "float", "low": 1e-3, "high": 1e3, "sampling": "log_uniform", "default_value": "1.0"},
        ],
        "classification": [
            {"name": "C", "param_type": "float", "low": 1e-3, "high": 1e3, "sampling": "log_uniform", "default_value": "1.0"},
        ],
    },
    "lasso": {
        "regression": [
            {"name": "alpha", "param_type": "float", "low": 1e-4, "high": 1e2, "sampling": "log_uniform", "default_value": "1.0"},
        ],
    },
    "elastic_net": {
        "regression": [
            {"name": "alpha", "param_type": "float", "low": 1e-4, "high": 1e2, "sampling": "log_uniform", "default_value": "1.0"},
            {"name": "l1_ratio", "param_type": "float", "low": 0.0, "high": 1.0, "sampling": "uniform", "default_value": "0.5"},
        ],
    },
    "random_forest": {
        "regression": [
            {"name": "n_estimators", "param_type": "int", "low": 50, "high": 500, "sampling": "uniform", "default_value": "100"},
            {"name": "max_depth", "param_type": "int", "low": 3, "high": 30, "sampling": "uniform", "default_value": "None"},
            {"name": "min_samples_split", "param_type": "int", "low": 2, "high": 20, "sampling": "uniform", "default_value": "2"},
            {"name": "min_samples_leaf", "param_type": "int", "low": 1, "high": 10, "sampling": "uniform", "default_value": "1"},
        ],
        "classification": [
            {"name": "n_estimators", "param_type": "int", "low": 50, "high": 500, "sampling": "uniform", "default_value": "100"},
            {"name": "max_depth", "param_type": "int", "low": 3, "high": 30, "sampling": "uniform", "default_value": "None"},
            {"name": "min_samples_split", "param_type": "int", "low": 2, "high": 20, "sampling": "uniform", "default_value": "2"},
            {"name": "criterion", "param_type": "categorical", "choices": ["gini", "entropy"], "sampling": "choice", "default_value": "gini"},
        ],
    },
    "gradient_boosting": {
        "regression": [
            {"name": "n_estimators", "param_type": "int", "low": 50, "high": 500, "sampling": "uniform", "default_value": "100"},
            {"name": "learning_rate", "param_type": "float", "low": 0.01, "high": 0.3, "sampling": "log_uniform", "default_value": "0.1"},
            {"name": "max_depth", "param_type": "int", "low": 2, "high": 10, "sampling": "uniform", "default_value": "3"},
            {"name": "subsample", "param_type": "float", "low": 0.5, "high": 1.0, "sampling": "uniform", "default_value": "1.0"},
        ],
        "classification": [
            {"name": "n_estimators", "param_type": "int", "low": 50, "high": 500, "sampling": "uniform", "default_value": "100"},
            {"name": "learning_rate", "param_type": "float", "low": 0.01, "high": 0.3, "sampling": "log_uniform", "default_value": "0.1"},
            {"name": "max_depth", "param_type": "int", "low": 2, "high": 10, "sampling": "uniform", "default_value": "3"},
        ],
    },
    "xgboost": {
        "regression": [
            {"name": "n_estimators", "param_type": "int", "low": 50, "high": 500, "sampling": "uniform", "default_value": "100"},
            {"name": "learning_rate", "param_type": "float", "low": 0.01, "high": 0.3, "sampling": "log_uniform", "default_value": "0.1"},
            {"name": "max_depth", "param_type": "int", "low": 2, "high": 12, "sampling": "uniform", "default_value": "6"},
            {"name": "subsample", "param_type": "float", "low": 0.5, "high": 1.0, "sampling": "uniform", "default_value": "1.0"},
            {"name": "colsample_bytree", "param_type": "float", "low": 0.5, "high": 1.0, "sampling": "uniform", "default_value": "1.0"},
        ],
        "classification": [
            {"name": "n_estimators", "param_type": "int", "low": 50, "high": 500, "sampling": "uniform", "default_value": "100"},
            {"name": "learning_rate", "param_type": "float", "low": 0.01, "high": 0.3, "sampling": "log_uniform", "default_value": "0.1"},
            {"name": "max_depth", "param_type": "int", "low": 2, "high": 12, "sampling": "uniform", "default_value": "6"},
        ],
    },
    "svr": {
        "regression": [
            {"name": "C", "param_type": "float", "low": 1e-3, "high": 1e3, "sampling": "log_uniform", "default_value": "1.0"},
            {"name": "epsilon", "param_type": "float", "low": 1e-3, "high": 1.0, "sampling": "log_uniform", "default_value": "0.1"},
            {"name": "kernel", "param_type": "categorical", "choices": ["linear", "rbf", "poly"], "sampling": "choice", "default_value": "rbf"},
            {"name": "gamma", "param_type": "float", "low": 1e-4, "high": 1e0, "sampling": "log_uniform", "default_value": "scale"},
        ],
    },
    "svc": {
        "classification": [
            {"name": "C", "param_type": "float", "low": 1e-3, "high": 1e3, "sampling": "log_uniform", "default_value": "1.0"},
            {"name": "kernel", "param_type": "categorical", "choices": ["linear", "rbf", "poly"], "sampling": "choice", "default_value": "rbf"},
            {"name": "gamma", "param_type": "float", "low": 1e-4, "high": 1e0, "sampling": "log_uniform", "default_value": "scale"},
        ],
    },
    "logistic_regression": {
        "classification": [
            {"name": "C", "param_type": "float", "low": 1e-3, "high": 1e3, "sampling": "log_uniform", "default_value": "1.0"},
            {"name": "penalty", "param_type": "categorical", "choices": ["l1", "l2"], "sampling": "choice", "default_value": "l2"},
        ],
    },
    "knn": {
        "regression": [
            {"name": "n_neighbors", "param_type": "int", "low": 1, "high": 30, "sampling": "uniform", "default_value": "5"},
            {"name": "weights", "param_type": "categorical", "choices": ["uniform", "distance"], "sampling": "choice", "default_value": "uniform"},
        ],
        "classification": [
            {"name": "n_neighbors", "param_type": "int", "low": 1, "high": 30, "sampling": "uniform", "default_value": "5"},
            {"name": "weights", "param_type": "categorical", "choices": ["uniform", "distance"], "sampling": "choice", "default_value": "uniform"},
        ],
    },
    "linear_regression": {
        "regression": [
            {"name": "fit_intercept", "param_type": "bool", "choices": ["true", "false"], "sampling": "choice", "default_value": "true"},
        ],
    },
    "gaussian_process": {
        "regression": [
            {"name": "alpha", "param_type": "float", "low": 1e-8, "high": 1e-2, "sampling": "log_uniform", "default_value": "1e-5"},
            {"name": "kernel", "param_type": "categorical", "choices": ["rbf", "matern", "rbf_white"], "sampling": "choice", "default_value": "rbf"},
        ],
    },
    "decision_tree": {
        "regression": [
            {"name": "max_depth", "param_type": "int", "low": 2, "high": 20, "sampling": "uniform", "default_value": "None"},
            {"name": "min_samples_split", "param_type": "int", "low": 2, "high": 20, "sampling": "uniform", "default_value": "2"},
            {"name": "min_samples_leaf", "param_type": "int", "low": 1, "high": 10, "sampling": "uniform", "default_value": "1"},
        ],
        "classification": [
            {"name": "max_depth", "param_type": "int", "low": 2, "high": 20, "sampling": "uniform", "default_value": "None"},
            {"name": "min_samples_split", "param_type": "int", "low": 2, "high": 20, "sampling": "uniform", "default_value": "2"},
            {"name": "min_samples_leaf", "param_type": "int", "low": 1, "high": 10, "sampling": "uniform", "default_value": "1"},
            {"name": "criterion", "param_type": "categorical", "choices": ["gini", "entropy"], "sampling": "choice", "default_value": "gini"},
        ],
    },
    "lightgbm": {
        "regression": [
            {"name": "n_estimators", "param_type": "int", "low": 50, "high": 500, "sampling": "uniform", "default_value": "100"},
            {"name": "learning_rate", "param_type": "float", "low": 0.01, "high": 0.3, "sampling": "log_uniform", "default_value": "0.1"},
            {"name": "num_leaves", "param_type": "int", "low": 8, "high": 64, "sampling": "uniform", "default_value": "31"},
            {"name": "max_depth", "param_type": "int", "low": 3, "high": 12, "sampling": "uniform", "default_value": "-1"},
            {"name": "subsample", "param_type": "float", "low": 0.5, "high": 1.0, "sampling": "uniform", "default_value": "1.0"},
        ],
        "classification": [
            {"name": "n_estimators", "param_type": "int", "low": 50, "high": 500, "sampling": "uniform", "default_value": "100"},
            {"name": "learning_rate", "param_type": "float", "low": 0.01, "high": 0.3, "sampling": "log_uniform", "default_value": "0.1"},
            {"name": "num_leaves", "param_type": "int", "low": 8, "high": 64, "sampling": "uniform", "default_value": "31"},
            {"name": "max_depth", "param_type": "int", "low": 3, "high": 12, "sampling": "uniform", "default_value": "-1"},
        ],
    },
    "mlp": {
        "regression": [
            {"name": "hidden_layer_sizes", "param_type": "categorical", "choices": ["(50,)", "(100,)", "(100,50)", "(50,25)"], "sampling": "choice", "default_value": "(100,)"},
            {"name": "activation", "param_type": "categorical", "choices": ["relu", "tanh"], "sampling": "choice", "default_value": "relu"},
            {"name": "alpha", "param_type": "float", "low": 1e-5, "high": 1e-1, "sampling": "log_uniform", "default_value": "0.0001"},
            {"name": "learning_rate_init", "param_type": "float", "low": 1e-4, "high": 1e-2, "sampling": "log_uniform", "default_value": "0.001"},
        ],
        "classification": [
            {"name": "hidden_layer_sizes", "param_type": "categorical", "choices": ["(50,)", "(100,)", "(100,50)", "(50,25)"], "sampling": "choice", "default_value": "(100,)"},
            {"name": "activation", "param_type": "categorical", "choices": ["relu", "tanh"], "sampling": "choice", "default_value": "relu"},
            {"name": "alpha", "param_type": "float", "low": 1e-5, "high": 1e-1, "sampling": "log_uniform", "default_value": "0.0001"},
            {"name": "learning_rate_init", "param_type": "float", "low": 1e-4, "high": 1e-2, "sampling": "log_uniform", "default_value": "0.001"},
        ],
    },
    "extra_trees": {
        "regression": [
            {"name": "n_estimators", "param_type": "int", "low": 50, "high": 500, "sampling": "uniform", "default_value": "100"},
            {"name": "max_depth", "param_type": "int", "low": 3, "high": 30, "sampling": "uniform", "default_value": "None"},
            {"name": "min_samples_split", "param_type": "int", "low": 2, "high": 20, "sampling": "uniform", "default_value": "2"},
            {"name": "min_samples_leaf", "param_type": "int", "low": 1, "high": 10, "sampling": "uniform", "default_value": "1"},
        ],
        "classification": [
            {"name": "n_estimators", "param_type": "int", "low": 50, "high": 500, "sampling": "uniform", "default_value": "100"},
            {"name": "max_depth", "param_type": "int", "low": 3, "high": 30, "sampling": "uniform", "default_value": "None"},
            {"name": "min_samples_split", "param_type": "int", "low": 2, "high": 20, "sampling": "uniform", "default_value": "2"},
            {"name": "criterion", "param_type": "categorical", "choices": ["gini", "entropy"], "sampling": "choice", "default_value": "gini"},
        ],
    },
    "dummy_mean": {},
}


def build_search_space_plan(
    candidate_models: List[dict],
    task_type: str,
    search_space_profile: dict,
) -> SearchSpacePlan:
    """Build search spaces from system templates. LLM can only suggest profile; templates are authoritative."""
    space_width = "moderate"
    if search_space_profile:
        space_width = search_space_profile.get("space_width", "moderate")

    spaces: List[SearchSpaceItem] = []
    for model in candidate_models:
        model_id = model.get("model_id", "")
        if not model.get("hpo_enabled", True):
            # Models without HPO get empty search space
            spaces.append(SearchSpaceItem(
                model_id=model_id,
                search_space_id=f"{model_id}_no_hpo",
                parameters=[],
            ))
            continue

        params = _get_search_space_params(model_id, task_type, space_width)
        space_id = f"{model_id}_default_{task_type}"
        spaces.append(SearchSpaceItem(
            model_id=model_id,
            search_space_id=space_id,
            parameters=params,
        ))

    return SearchSpacePlan(spaces=spaces)


def _get_search_space_params(
    model_id: str,
    task_type: str,
    space_width: str,
) -> List[SearchSpaceParameter]:
    template = _SEARCH_SPACE_TEMPLATES.get(model_id, {})
    task_params = template.get(task_type, template.get("regression", []))

    params = []
    for p in task_params:
        param = SearchSpaceParameter(
            name=p["name"],
            param_type=p.get("param_type", "float"),
            low=p.get("low"),
            high=p.get("high"),
            choices=p.get("choices", []),
            sampling=p.get("sampling", "uniform"),
            default_value=p.get("default_value"),
        )

        # Adjust ranges based on space width
        if space_width == SearchSpaceProfile.NARROW and param.param_type in ("float", "int"):
            if param.low is not None and param.high is not None:
                mid = (param.low + param.high) / 2
                half_range = (param.high - param.low) * 0.25
                param.low = max(param.low, mid - half_range)
                param.high = min(param.high, mid + half_range)
        elif space_width == SearchSpaceProfile.WIDE and param.param_type in ("float", "int"):
            if param.low is not None and param.high is not None:
                range_size = param.high - param.low
                param.low = max(0.0 if param.param_type == "float" else 1, param.low - range_size * 0.3)
                param.high = param.high + range_size * 0.3

        params.append(param)

    return params
