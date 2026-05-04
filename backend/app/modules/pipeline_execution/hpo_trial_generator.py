"""HPO Trial Generator — generates hyperparameter combinations from search spaces.

Parses the upstream SearchSpaceItem format (list of SearchSpaceParameter dicts):
    {
        "model_id": "...",
        "search_space_id": "...",
        "parameters": [
            {"name": "alpha", "param_type": "float", "low": 1e-3, "high": 1e3, "sampling": "log_uniform"},
            {"name": "kernel", "param_type": "categorical", "choices": ["linear","rbf"], "sampling": "choice"},
            ...
        ]
    }

MVP supports random_search and grid_search.
"""

import random
import math
import itertools
from typing import List, Optional


def generate_hpo_trials(
    search_space: dict,
    search_method: str,
    max_trials: int,
    random_state: int = 42,
) -> List[dict]:
    """Generate a list of parameter dicts for HPO trials.

    Args:
        search_space: SearchSpaceItem dict from upstream with a "parameters" key.
        search_method: 'random_search' or 'grid_search'.
        max_trials: Maximum number of trials to generate.
        random_state: Seed for reproducibility.

    Returns:
        List of parameter dictionaries, e.g. [{"alpha": 0.1, "kernel": "rbf"}, ...].
    """
    params = _extract_parameters(search_space)
    if not params or max_trials <= 0:
        return [{}]

    if search_method == "grid_search":
        return _generate_grid_trials(params, max_trials)
    else:
        return _generate_random_trials(params, max_trials, random_state)


def _extract_parameters(search_space: dict) -> list:
    """Extract the parameter list from the upstream SearchSpaceItem format."""
    if not search_space:
        return []
    params = search_space.get("parameters", [])
    if not params:
        # Also try direct list (bare SearchSpaceParameter list)
        if isinstance(search_space, list):
            return search_space
    return params


def _sample_param(param_spec: dict, rng: random.Random):
    """Sample a single value from a SearchSpaceParameter spec."""
    pt = param_spec.get("param_type", "float")
    choices = param_spec.get("choices", [])
    sampling = param_spec.get("sampling", "uniform")

    if pt == "categorical" or pt == "bool" or sampling == "choice":
        if choices:
            return rng.choice(choices)
        return None

    low = param_spec.get("low")
    high = param_spec.get("high")
    if low is None or high is None:
        return param_spec.get("default_value")

    if pt == "int":
        if sampling == "log_uniform":
            log_low = math.log(max(float(low), 1e-10))
            log_high = math.log(max(float(high), 1e-10))
            val = math.exp(rng.uniform(log_low, log_high))
            return max(int(low), int(round(val)))
        return rng.randint(int(low), int(high))

    # float
    if sampling == "log_uniform":
        log_low = math.log(max(float(low), 1e-10))
        log_high = math.log(max(float(high), 1e-10))
        return math.exp(rng.uniform(log_low, log_high))
    return rng.uniform(float(low), float(high))


def _generate_random_trials(
    params: list, max_trials: int, random_state: int
) -> List[dict]:
    rng = random.Random(random_state)
    trials = []
    seen = set()
    attempts = 0
    max_attempts = max_trials * 20
    while len(trials) < max_trials and attempts < max_attempts:
        combo = {}
        for p in params:
            combo[p["name"]] = _sample_param(p, rng)
        key = frozenset((k, str(v)) for k, v in combo.items())
        if key not in seen:
            seen.add(key)
            trials.append(combo)
        attempts += 1
    return trials


def _generate_grid_trials(params: list, max_trials: int) -> List[dict]:
    """Generate grid points from parameter specs, limited to max_trials."""
    grids = {}
    for p in params:
        pt = p.get("param_type", "float")
        choices = p.get("choices", [])
        sampling = p.get("sampling", "uniform")

        if pt == "categorical" or pt == "bool" or sampling == "choice":
            grids[p["name"]] = choices if choices else [p.get("default_value")]
        elif pt == "int":
            low = int(p.get("low", 0))
            high = int(p.get("high", 100))
            n = p.get("n_grid", 5)
            if sampling == "log_uniform":
                log_low = math.log(max(float(low), 1e-10))
                log_high = math.log(max(float(high), 1e-10))
                vals = [int(round(math.exp(log_low + i * (log_high - log_low) / (n - 1)))) for i in range(n)]
            else:
                step = max(1, (high - low) // n)
                vals = list(range(low, high + 1, step))
            grids[p["name"]] = vals
        else:  # float
            low = float(p.get("low", 0.0))
            high = float(p.get("high", 1.0))
            n = p.get("n_grid", 5)
            if sampling == "log_uniform":
                log_low = math.log(max(low, 1e-10))
                log_high = math.log(max(high, 1e-10))
                vals = [math.exp(log_low + i * (log_high - log_low) / (n - 1)) for i in range(n)]
            else:
                vals = [low + i * (high - low) / (n - 1) for i in range(n)]
            grids[p["name"]] = vals

    if not grids:
        return [{}]

    keys = list(grids.keys())
    all_combos = list(itertools.product(*(grids[k] for k in keys)))
    if len(all_combos) > max_trials:
        step = max(1, len(all_combos) // max_trials)
        all_combos = all_combos[::step][:max_trials]

    return [{k: v for k, v in zip(keys, combo)} for combo in all_combos]
