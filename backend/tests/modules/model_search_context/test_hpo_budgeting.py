from app.modules.model_search_context.builder import build_hpo_plan
from app.shared.config.settings import settings


def _candidate(model_id: str, priority: str = "high") -> dict:
    return {
        "model_id": model_id,
        "model_family": model_id,
        "priority": priority,
        "hpo_enabled": True,
    }


def _allocations(plan) -> dict:
    return {item.model_id: item.max_trials for item in plan.trial_allocation}


def test_high_budget_large_profile_uses_large_cap(monkeypatch):
    monkeypatch.setattr(settings, "MODEL_CONTEXT_MAX_HPO_TRIALS", 50)
    monkeypatch.setattr(settings, "MODEL_CONTEXT_LARGE_HPO_MAX_TRIALS", 100, raising=False)
    monkeypatch.setattr(settings, "MODEL_CONTEXT_HARD_MAX_HPO_TRIALS", 200, raising=False)

    plan = build_hpo_plan(
        updated_hpo_strategy={
            "enabled": True,
            "search_method": "optuna_tpe",
            "budget_level": "high",
            "max_trials": 120,
            "search_space_width": "wide",
        },
        candidate_models=[_candidate("xgboost"), _candidate("lightgbm"), _candidate("random_forest")],
        baseline_models=[{"model_id": "linear_regression", "hpo_enabled": False}],
        dataset_profile={"n_samples": 1200, "n_final_features": 80},
    )

    assert plan.max_total_trials == 100
    assert sum(_allocations(plan).values()) == 100


def test_llm_allocation_keeps_complex_models_above_minimum_when_feasible(monkeypatch):
    monkeypatch.setattr(settings, "MODEL_CONTEXT_MAX_HPO_TRIALS", 50)
    monkeypatch.setattr(settings, "MODEL_CONTEXT_COMPLEX_MODEL_MIN_TRIALS", 20, raising=False)

    plan = build_hpo_plan(
        updated_hpo_strategy={
            "enabled": True,
            "search_method": "random_search",
            "budget_level": "moderate",
            "max_trials": 50,
            "search_space_width": "moderate",
        },
        candidate_models=[_candidate("xgboost"), _candidate("lightgbm"), _candidate("random_forest")],
        baseline_models=[],
        llm_trial_allocation=[
            {"model_family": "xgboost", "max_trials": 15, "allocation_rationale": "complex"},
            {"model_family": "lightgbm", "max_trials": 10, "allocation_rationale": "complex"},
            {"model_family": "random_forest", "max_trials": 25, "allocation_rationale": "stable"},
        ],
        dataset_profile={"n_samples": 500, "n_final_features": 30},
    )

    allocations = _allocations(plan)
    assert allocations["xgboost"] >= 20
    assert allocations["lightgbm"] >= 20
    assert sum(allocations.values()) == 50


def test_resource_constrained_profile_keeps_small_hpo_cap(monkeypatch):
    monkeypatch.setattr(settings, "MODEL_CONTEXT_MAX_HPO_TRIALS", 50)
    monkeypatch.setattr(settings, "MODEL_CONTEXT_DEFAULT_HPO_MAX_TRIALS_SMALL", 20)
    monkeypatch.setattr(settings, "MODEL_CONTEXT_LARGE_HPO_MAX_TRIALS", 100, raising=False)

    plan = build_hpo_plan(
        updated_hpo_strategy={
            "enabled": True,
            "search_method": "random_search",
            "budget_level": "high",
            "max_trials": 80,
            "search_space_width": "wide",
        },
        candidate_models=[_candidate("xgboost"), _candidate("lightgbm")],
        baseline_models=[],
        dataset_profile={
            "n_samples": 120,
            "n_final_features": 15,
            "is_small_sample": True,
            "is_low_feature": True,
        },
    )

    assert plan.max_total_trials == 20
    assert sum(_allocations(plan).values()) == 20
