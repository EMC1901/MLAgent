"""Model Factory — the ONLY place that instantiates ML models.

Maps registry model_ids to concrete sklearn (or compatible) classes.
No dynamic imports, no eval, no user-supplied class names.
"""

from app.shared.registry.model_registry import (
    is_valid_model_family,
    get_model_spec,
    get_baseline_models,
)
from app.modules.pipeline_execution.exceptions import ModelInstantiationException

# ---- Safe, explicit model mapping (no dynamic imports) ----

_REGRESSION_MODELS = {}
_CLASSIFICATION_MODELS = {}

try:
    from sklearn.dummy import DummyRegressor, DummyClassifier
    _REGRESSION_MODELS["dummy_mean"] = lambda **kw: DummyRegressor(strategy="mean", **kw)
    _CLASSIFICATION_MODELS["dummy_mean"] = lambda **kw: DummyClassifier(strategy="most_frequent", **kw)
except ImportError:
    pass

try:
    from sklearn.linear_model import LinearRegression
    _REGRESSION_MODELS["linear_regression"] = lambda **kw: LinearRegression(**kw)
    _REGRESSION_MODELS["linear"] = lambda **kw: LinearRegression(**kw)
except ImportError:
    pass

try:
    from sklearn.linear_model import Ridge
    _REGRESSION_MODELS["ridge"] = lambda **kw: Ridge(**kw)
except ImportError:
    pass

try:
    from sklearn.linear_model import Lasso
    _REGRESSION_MODELS["lasso"] = lambda **kw: Lasso(**kw)
except ImportError:
    pass

try:
    from sklearn.linear_model import ElasticNet
    _REGRESSION_MODELS["elastic_net"] = lambda **kw: ElasticNet(**kw)
except ImportError:
    pass

try:
    from sklearn.ensemble import RandomForestRegressor
    _REGRESSION_MODELS["random_forest"] = lambda **kw: RandomForestRegressor(**kw)
except ImportError:
    pass

try:
    from sklearn.ensemble import RandomForestClassifier
    _CLASSIFICATION_MODELS["random_forest"] = lambda **kw: RandomForestClassifier(**kw)
except ImportError:
    pass

try:
    from sklearn.ensemble import GradientBoostingRegressor
    _REGRESSION_MODELS["gradient_boosting"] = lambda **kw: GradientBoostingRegressor(**kw)
except ImportError:
    pass

try:
    from sklearn.ensemble import GradientBoostingClassifier
    _CLASSIFICATION_MODELS["gradient_boosting"] = lambda **kw: GradientBoostingClassifier(**kw)
except ImportError:
    pass

try:
    from sklearn.svm import SVR, SVC
    _REGRESSION_MODELS["svr"] = lambda **kw: SVR(**kw)
    _CLASSIFICATION_MODELS["svc"] = lambda **kw: SVC(probability=True, **kw)
except ImportError:
    pass

try:
    from sklearn.linear_model import LogisticRegression
    _CLASSIFICATION_MODELS["logistic_regression"] = lambda **kw: LogisticRegression(max_iter=1000, **kw)
except ImportError:
    pass

try:
    from sklearn.neighbors import KNeighborsRegressor, KNeighborsClassifier
    _REGRESSION_MODELS["knn"] = lambda **kw: KNeighborsRegressor(**kw)
    _CLASSIFICATION_MODELS["knn"] = lambda **kw: KNeighborsClassifier(**kw)
except ImportError:
    pass

try:
    from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
    _REGRESSION_MODELS["decision_tree"] = lambda **kw: DecisionTreeRegressor(**kw)
    _CLASSIFICATION_MODELS["decision_tree"] = lambda **kw: DecisionTreeClassifier(**kw)
except ImportError:
    pass

try:
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel, Matern

    def _make_gp(**kw):
        kernel_str = kw.pop("kernel", "rbf")
        alpha = kw.pop("alpha", 1e-5)
        if kernel_str == "matern":
            kernel = ConstantKernel(1.0) * Matern(length_scale=1.0) + WhiteKernel(1e-3)
        elif kernel_str == "rbf_white":
            kernel = RBF(length_scale=1.0) + WhiteKernel(1e-3)
        else:
            kernel = ConstantKernel(1.0) * RBF(length_scale=1.0) + WhiteKernel(1e-3)
        return GaussianProcessRegressor(
            kernel=kernel,
            alpha=alpha,
            normalize_y=True,
            random_state=kw.pop("random_state", 42),
            **kw,
        )

    _REGRESSION_MODELS["gaussian_process"] = _make_gp
except ImportError:
    pass

try:
    from sklearn.ensemble import ExtraTreesRegressor, ExtraTreesClassifier
    _REGRESSION_MODELS["extra_trees"] = lambda **kw: ExtraTreesRegressor(**kw)
    _CLASSIFICATION_MODELS["extra_trees"] = lambda **kw: ExtraTreesClassifier(**kw)
except ImportError:
    pass

# XGBoost is optional
try:
    from xgboost import XGBRegressor, XGBClassifier
    _REGRESSION_MODELS["xgboost"] = lambda **kw: XGBRegressor(**kw)
    _CLASSIFICATION_MODELS["xgboost"] = lambda **kw: XGBClassifier(**kw)
except ImportError:
    pass

# LightGBM is optional
try:
    from lightgbm import LGBMRegressor, LGBMClassifier
    _REGRESSION_MODELS["lightgbm"] = lambda **kw: LGBMRegressor(verbose=-1, **kw)
    _CLASSIFICATION_MODELS["lightgbm"] = lambda **kw: LGBMClassifier(verbose=-1, **kw)
except ImportError:
    pass

try:
    from sklearn.neural_network import MLPRegressor, MLPClassifier
    _REGRESSION_MODELS["mlp"] = lambda **kw: MLPRegressor(max_iter=1000, early_stopping=True, **kw)
    _CLASSIFICATION_MODELS["mlp"] = lambda **kw: MLPClassifier(max_iter=1000, early_stopping=True, **kw)
except ImportError:
    pass


def _get_model_map(task_type: str) -> dict:
    t = (task_type or "regression").lower()
    if t == "classification":
        return _CLASSIFICATION_MODELS
    return _REGRESSION_MODELS


def create_model(model_id: str, task_type: str, params: dict = None):
    """Safely create a model instance from the registry.

    Args:
        model_id: Registry model identifier (e.g. 'ridge', 'random_forest').
        task_type: 'regression' or 'classification'.
        params: Optional keyword arguments forwarded to the constructor.

    Returns:
        An sklearn-compatible estimator instance.

    Raises:
        ModelInstantiationException if the model is unknown, unsupported for the
        task type, or its dependency is missing.
    """
    if not is_valid_model_family(model_id):
        spec = get_model_spec(model_id)
        if spec is None:
            raise ModelInstantiationException(
                f"Model '{model_id}' is not registered in the Model Registry."
            )
        else:
            raise ModelInstantiationException(
                f"Model '{model_id}' is registered but not supported for task type '{task_type}'."
            )

    spec = get_model_spec(model_id)
    if spec and task_type not in spec.get("supported_task_types", []):
        raise ModelInstantiationException(
            f"Model '{model_id}' does not support task type '{task_type}'."
        )

    model_map = _get_model_map(task_type)
    factory = model_map.get(model_id)
    if factory is None:
        # Check if it exists for the other task type
        other = "classification" if task_type == "regression" else "regression"
        other_map = _get_model_map(other)
        if model_id in other_map:
            raise ModelInstantiationException(
                f"Model '{model_id}' is available for '{other}' but not for '{task_type}'."
            )
        raise ModelInstantiationException(
            f"Dependency missing for model '{model_id}'. Install the required library."
        )

    try:
        return factory(**(params or {}))
    except TypeError as e:
        raise ModelInstantiationException(
            f"Invalid parameters for model '{model_id}': {e}"
        )
    except Exception as e:
        raise ModelInstantiationException(
            f"Failed to instantiate model '{model_id}': {e}"
        )


def is_model_available(model_id: str, task_type: str) -> bool:
    """Check if a model can be instantiated without actually creating it."""
    model_map = _get_model_map(task_type)
    return model_id in model_map


def get_available_models(task_type: str) -> list:
    """Return list of model_ids that can be instantiated right now."""
    return list(_get_model_map(task_type).keys())
