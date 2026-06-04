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

Supported methods:
  - random_search:        Simple random sampling.
  - grid_search:          Grid or sub-sampled grid via islice.
  - bayesian_optimization: Optuna TPE sampler if optuna is installed, otherwise
                          falls back to Latin Hypercube Sampling (LHS).
"""

import logging
import random
import math
import itertools
from typing import List, Optional

logger = logging.getLogger(__name__)


# ---- Optuna availability ----

_OPTUNA_AVAILABLE = False
try:
    import optuna
    _OPTUNA_AVAILABLE = True
except ImportError:
    pass


def generate_hpo_trials(
    search_space: dict,
    search_method: str,
    max_trials: int,
    random_state: int = 42,
) -> List[dict]:
    """Generate a list of parameter dicts for HPO trials.

    Args:
        search_space: SearchSpaceItem dict from upstream with a "parameters" key.
        search_method: 'random_search', 'grid_search', or 'bayesian_optimization'.
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
    if search_method == "bayesian_optimization":
        if _OPTUNA_AVAILABLE:
            return _optuna_tpe_trials(params, max_trials, random_state)
        logger.debug("Optuna not installed, falling back to LHS for bayesian_optimization")
        return _bayesian_optimization_trials(params, max_trials, random_state)
    if _OPTUNA_AVAILABLE and search_method in ("optuna_tpe", "successive_halving"):
        return _optuna_tpe_trials(params, max_trials, random_state)
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
    # Use islice to avoid materializing the full Cartesian product when the
    # space is large.  Compute the step size so we sample evenly across the
    # full enumerated space without building the intermediate list.
    total_size = 1
    for k in keys:
        total_size *= len(grids[k])
    take = min(total_size, max_trials)
    step = max(1, total_size // take) if take > 0 else 1

    combos = []
    for i, combo in enumerate(itertools.product(*(grids[k] for k in keys))):
        if i % step == 0:
            combos.append({k: v for k, v in zip(keys, combo)})
            if len(combos) >= take:
                break

    return combos


def _bayesian_optimization_trials(
    params: list, max_trials: int, random_state: int
) -> List[dict]:
    """Generate initial trials using Latin Hypercube Sampling as a space-filling design.

    LHS produces well-distributed points across the search space, providing a
    superior starting surrogate for Bayesian Optimization compared to random
    sampling. The actual iterative BO loop (GP + acquisition function) requires
    model evaluation feedback, which is not available at trial-generation time.
    """
    from scipy.stats.qmc import LatinHypercube

    continuous_params = []
    categorical_params = []
    for p in params:
        pt = p.get("param_type", "float")
        choices = p.get("choices", [])
        sampling = p.get("sampling", "uniform")
        if pt in ("categorical", "bool") or sampling == "choice" or choices:
            categorical_params.append(p)
        else:
            continuous_params.append(p)

    if not continuous_params:
        return _generate_random_trials(params, max_trials, random_state)

    sampler = LatinHypercube(d=len(continuous_params), seed=random_state)
    lhs_samples = sampler.random(n=max_trials)

    trials = []
    for i in range(max_trials):
        combo = {}
        for j, p in enumerate(continuous_params):
            combo[p["name"]] = _map_lhs_to_param(p, lhs_samples[i, j])
        rng = random.Random(random_state + i)
        for p in categorical_params:
            combo[p["name"]] = _sample_param(p, rng)
        trials.append(combo)

    return trials


def _map_lhs_to_param(param_spec: dict, unit_val: float):
    """Map a [0,1] LHS value to the parameter's actual range."""
    pt = param_spec.get("param_type", "float")
    sampling = param_spec.get("sampling", "uniform")
    low = param_spec.get("low")
    high = param_spec.get("high")

    if low is None or high is None:
        return param_spec.get("default_value")

    if sampling == "log_uniform":
        log_low = math.log(max(float(low), 1e-10))
        log_high = math.log(max(float(high), 1e-10))
        val = math.exp(log_low + unit_val * (log_high - log_low))
    else:
        val = float(low) + unit_val * (float(high) - float(low))

    if pt == "int":
        return max(int(low), int(round(val)))
    return val


def _optuna_tpe_trials(
    params: list, max_trials: int, random_state: int
) -> List[dict]:
    """Generate trial parameter sets using Optuna's TPE sampler.

    Uses a dummy study with TPE sampler to produce parameter suggestions that
    respect the distributions defined in the search space.  Without objective
    values the TPE prior acts as a structured space-filling design (better
    than pure random, especially for mixed continuous/categorical spaces).

    Falls back to random search if Optuna raises an exception.
    """
    if not params or max_trials <= 0:
        return [{}]

    try:
        recorded: List[dict] = []

        def _objective(trial):
            combo = {}
            for p in params:
                name = p["name"]
                pt = p.get("param_type", "float")
                choices = p.get("choices", [])
                low = p.get("low")
                high = p.get("high")
                sampling = p.get("sampling", "uniform")

                if pt in ("categorical", "bool") or sampling == "choice" or choices:
                    combo[name] = trial.suggest_categorical(name, choices if choices else [])
                elif pt == "int":
                    if low is None or high is None:
                        combo[name] = p.get("default_value")
                    elif sampling == "log_uniform":
                        combo[name] = trial.suggest_int(name, int(low), int(high), log=True)
                    else:
                        combo[name] = trial.suggest_int(name, int(low), int(high))
                else:  # float
                    if low is None or high is None:
                        combo[name] = p.get("default_value")
                    elif sampling == "log_uniform":
                        combo[name] = trial.suggest_float(name, float(low), float(high), log=True)
                    else:
                        combo[name] = trial.suggest_float(name, float(low), float(high))
            recorded.append(combo)
            return 0.0

        sampler = optuna.samplers.TPESampler(
            seed=random_state,
            n_startup_trials=max(1, max_trials // 3),
        )
        study = optuna.create_study(
            sampler=sampler,
            direction="minimize",
        )
        # Suppress optuna's default logging to keep our log output clean
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        study.optimize(_objective, n_trials=max_trials, show_progress_bar=False)

        logger.debug("Optuna TPE generated %d trials", len(recorded))
        return recorded

    except Exception as e:
        logger.debug("Optuna TPE failed (%s), falling back to random search", e)
        return _generate_random_trials(params, max_trials, random_state)
