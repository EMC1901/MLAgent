from app.modules.model_search_context.search_space_builder import build_search_space_plan


def _space_param(plan, model_id: str, param_name: str):
    for space in plan.spaces:
        if space.model_id != model_id:
            continue
        for param in space.parameters:
            if param.name == param_name:
                return param
    raise AssertionError(f"{model_id}.{param_name} not found")


def test_lightgbm_moderate_profile_allows_more_leaves():
    plan = build_search_space_plan(
        candidate_models=[{"model_id": "lightgbm", "model_family": "lightgbm", "hpo_enabled": True}],
        task_type="regression",
        search_space_profile={"space_width": "moderate"},
    )

    assert _space_param(plan, "lightgbm", "num_leaves").high == 63


def test_lightgbm_wide_profile_expands_leaf_and_depth_bounds():
    plan = build_search_space_plan(
        candidate_models=[{"model_id": "lightgbm", "model_family": "lightgbm", "hpo_enabled": True}],
        task_type="regression",
        search_space_profile={"space_width": "wide"},
    )

    assert _space_param(plan, "lightgbm", "num_leaves").high == 127
    assert _space_param(plan, "lightgbm", "max_depth").high >= 16


def test_xgboost_narrow_profile_keeps_depth_conservative():
    plan = build_search_space_plan(
        candidate_models=[{"model_id": "xgboost", "model_family": "xgboost", "hpo_enabled": True}],
        task_type="regression",
        search_space_profile={"space_width": "narrow"},
    )

    assert _space_param(plan, "xgboost", "max_depth").high <= 8
