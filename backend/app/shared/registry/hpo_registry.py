from typing import List, Optional

HPO_METHODS: List[dict] = [
    {
        "method": "random_search",
        "display_name": "Random Search",
        "description": "Randomly sample hyperparameter combinations.",
        "requires_budget": True,
        "default_max_trials_small": 10,
        "default_max_trials_medium": 30,
        "default_max_trials_large": 50,
    },
    {
        "method": "grid_search",
        "display_name": "Grid Search",
        "description": "Exhaustive search over a predefined hyperparameter grid.",
        "requires_budget": True,
        "default_max_trials_small": 16,
        "default_max_trials_medium": 36,
        "default_max_trials_large": 64,
    },
    {
        "method": "optuna_tpe",
        "display_name": "Optuna TPE",
        "description": "Tree-structured Parzen Estimator (Optuna).",
        "requires_budget": True,
        "default_max_trials_small": 10,
        "default_max_trials_medium": 30,
        "default_max_trials_large": 50,
    },
    {
        "method": "bayesian_search",
        "display_name": "Bayesian Optimization",
        "description": "Bayesian optimization with Gaussian Process.",
        "requires_budget": True,
        "default_max_trials_small": 10,
        "default_max_trials_medium": 30,
        "default_max_trials_large": 50,
    },
    {
        "method": "successive_halving",
        "display_name": "Successive Halving",
        "description": "Successive halving for early stopping of poor trials.",
        "requires_budget": True,
        "default_max_trials_small": 20,
        "default_max_trials_medium": 50,
        "default_max_trials_large": 100,
    },
]


def get_all_hpo_methods() -> List[str]:
    return [m["method"] for m in HPO_METHODS]


def is_valid_hpo_method(method: str) -> bool:
    return method in get_all_hpo_methods()


def get_hpo_method_spec(method: str) -> Optional[dict]:
    for m in HPO_METHODS:
        if m["method"] == method:
            return m
    return None
