import logging
from typing import List, Optional
from app.shared.registry.model_registry import get_model_spec
from app.modules.model_search_context.schemas import SearchSpaceParameter, SearchSpaceItem, SearchSpacePlan
from app.modules.model_search_context.enums import SearchSpaceProfile, TaskType

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
            {"name": "max_features", "param_type": "categorical", "choices": ["sqrt", "log2", 0.5, 0.8, 1.0], "sampling": "choice", "default_value": "1.0"},
        ],
        "classification": [
            {"name": "n_estimators", "param_type": "int", "low": 50, "high": 500, "sampling": "uniform", "default_value": "100"},
            {"name": "max_depth", "param_type": "int", "low": 3, "high": 30, "sampling": "uniform", "default_value": "None"},
            {"name": "min_samples_split", "param_type": "int", "low": 2, "high": 20, "sampling": "uniform", "default_value": "2"},
            {"name": "min_samples_leaf", "param_type": "int", "low": 1, "high": 10, "sampling": "uniform", "default_value": "1"},
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
            {"name": "solver", "param_type": "categorical", "choices": ["liblinear", "saga"], "sampling": "choice", "default_value": "liblinear"},
        ],
    },
    "knn": {
        "regression": [
            {"name": "n_neighbors", "param_type": "int", "low": 3, "high": 30, "sampling": "uniform", "default_value": "5"},
            {"name": "weights", "param_type": "categorical", "choices": ["uniform", "distance"], "sampling": "choice", "default_value": "uniform"},
        ],
        "classification": [
            {"name": "n_neighbors", "param_type": "int", "low": 3, "high": 30, "sampling": "uniform", "default_value": "5"},
            {"name": "weights", "param_type": "categorical", "choices": ["uniform", "distance"], "sampling": "choice", "default_value": "uniform"},
        ],
    },
    "linear_regression": {
        "regression": [
            {"name": "fit_intercept", "param_type": "bool", "choices": ["true", "false"], "sampling": "choice", "default_value": "true"},
            {"name": "positive", "param_type": "bool", "choices": ["true", "false"], "sampling": "choice", "default_value": "false"},
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
            {"name": "num_leaves", "param_type": "int", "low": 8, "high": 31, "sampling": "uniform", "default_value": "31"},
            {"name": "max_depth", "param_type": "int", "low": 3, "high": 12, "sampling": "uniform", "default_value": "-1"},
            {"name": "subsample", "param_type": "float", "low": 0.5, "high": 1.0, "sampling": "uniform", "default_value": "1.0"},
        ],
        "classification": [
            {"name": "n_estimators", "param_type": "int", "low": 50, "high": 500, "sampling": "uniform", "default_value": "100"},
            {"name": "learning_rate", "param_type": "float", "low": 0.01, "high": 0.3, "sampling": "log_uniform", "default_value": "0.1"},
            {"name": "num_leaves", "param_type": "int", "low": 8, "high": 31, "sampling": "uniform", "default_value": "31"},
            {"name": "max_depth", "param_type": "int", "low": 3, "high": 12, "sampling": "uniform", "default_value": "-1"},
        ],
    },
    "mlp": {
        "regression": [
            {"name": "hidden_layer_sizes", "param_type": "categorical", "choices": ["(50,)", "(100,)", "(100,50)", "(100,50,25)", "(50,25)"], "sampling": "choice", "default_value": "(100,)"},
            {"name": "activation", "param_type": "categorical", "choices": ["relu", "tanh"], "sampling": "choice", "default_value": "relu"},
            {"name": "alpha", "param_type": "float", "low": 1e-5, "high": 1e-1, "sampling": "log_uniform", "default_value": "0.0001"},
            {"name": "learning_rate_init", "param_type": "float", "low": 1e-4, "high": 1e-2, "sampling": "log_uniform", "default_value": "0.001"},
        ],
        "classification": [
            {"name": "hidden_layer_sizes", "param_type": "categorical", "choices": ["(50,)", "(100,)", "(100,50)", "(100,50,25)", "(50,25)"], "sampling": "choice", "default_value": "(100,)"},
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
            {"name": "max_features", "param_type": "categorical", "choices": ["sqrt", "log2", 0.5, 0.8, 1.0], "sampling": "choice", "default_value": "1.0"},
        ],
        "classification": [
            {"name": "n_estimators", "param_type": "int", "low": 50, "high": 500, "sampling": "uniform", "default_value": "100"},
            {"name": "max_depth", "param_type": "int", "low": 3, "high": 30, "sampling": "uniform", "default_value": "None"},
            {"name": "min_samples_split", "param_type": "int", "low": 2, "high": 20, "sampling": "uniform", "default_value": "2"},
            {"name": "min_samples_leaf", "param_type": "int", "low": 1, "high": 10, "sampling": "uniform", "default_value": "1"},
            {"name": "max_features", "param_type": "categorical", "choices": ["sqrt", "log2", 0.5, 0.8, 1.0], "sampling": "choice", "default_value": "1.0"},
            {"name": "criterion", "param_type": "categorical", "choices": ["gini", "entropy"], "sampling": "choice", "default_value": "gini"},
        ],
    },
    "dummy_mean": {},
}


def build_search_space_plan(
    candidate_models: List[dict],
    task_type: str,
    search_space_profile: dict,
    llm_overrides: List[dict] = None,
) -> SearchSpacePlan:
    """Build search spaces from system templates, with optional LLM overrides."""
    space_width = "moderate"
    if search_space_profile:
        space_width = search_space_profile.get("space_width", "moderate")

    # Build a lookup: model_family -> {param_name -> override dict}
    override_map: dict = {}
    if llm_overrides:
        for ov in llm_overrides:
            family = ov.get("model_family", "")
            pname = ov.get("parameter_name", "")
            if family and pname:
                override_map.setdefault(family, {})[pname] = ov

    spaces: List[SearchSpaceItem] = []
    for model in candidate_models:
        model_id = model.get("model_id", "")
        model_family = model.get("model_family", model_id)
        if not model.get("hpo_enabled", True):
            spaces.append(SearchSpaceItem(
                model_id=model_id,
                search_space_id=f"{model_id}_no_hpo",
                parameters=[],
            ))
            continue

        params = _get_search_space_params(model_id, task_type, space_width)

        # Apply LLM overrides for this model family
        family_overrides = override_map.get(model_id, {}) or override_map.get(model_family, {})
        if family_overrides:
            params = _apply_overrides_to_params(params, family_overrides)

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

        _apply_model_specific_profile_bounds(model_id, space_width, param)
        params.append(param)

    return params


def _apply_model_specific_profile_bounds(
    model_id: str,
    space_width: str,
    param: SearchSpaceParameter,
) -> None:
    """Tune high-sensitivity tree model ranges after generic profile scaling."""
    if model_id == "lightgbm":
        if space_width == SearchSpaceProfile.NARROW:
            if param.name == "num_leaves" and param.high is not None:
                param.high = min(param.high, 31)
            elif param.name == "max_depth" and param.high is not None:
                param.high = min(param.high, 8)
        elif space_width == SearchSpaceProfile.MODERATE:
            if param.name == "num_leaves":
                param.high = max(param.high or 0, 63)
        elif space_width == SearchSpaceProfile.WIDE:
            if param.name == "num_leaves":
                param.high = max(param.high or 0, 127)
            elif param.name == "max_depth":
                param.high = max(param.high or 0, 16)
            elif param.name == "n_estimators":
                param.high = max(param.high or 0, 800)

    if model_id == "xgboost":
        if space_width == SearchSpaceProfile.NARROW:
            if param.name == "max_depth" and param.high is not None:
                param.high = min(param.high, 8)
        elif space_width == SearchSpaceProfile.WIDE:
            if param.name == "max_depth":
                param.high = max(param.high or 0, 16)
            elif param.name == "n_estimators":
                param.high = max(param.high or 0, 800)


def _apply_overrides_to_params(
    params: List[SearchSpaceParameter],
    family_overrides: dict,
) -> List[SearchSpaceParameter]:
    """Apply LLM-suggested per-parameter overrides, with validation."""
    for param in params:
        override = family_overrides.get(param.name)
        if not override:
            continue

        # Apply low bound override
        if override.get("low") is not None:
            new_low = float(override["low"])
            if param.high is None or new_low < param.high:
                param.low = new_low
                param.override_rationale = override.get("override_rationale", "")

        # Apply high bound override
        if override.get("high") is not None:
            new_high = float(override["high"])
            if param.low is None or new_high > param.low:
                param.high = new_high
                param.override_rationale = override.get("override_rationale", "")

        # Apply choices override (preserve types — sklearn distinguishes str from float for params like max_features)
        if override.get("choices") is not None and isinstance(override["choices"], list):
            param.choices = list(override["choices"])
            param.override_rationale = override.get("override_rationale", "")

    return params
