from app.modules.model_search_context.builder import build_validation_plan


def test_build_validation_plan_preserves_holdout_test_size():
    plan = build_validation_plan({
        "split_strategy": "train_test_split",
        "test_size": 0.1,
        "n_splits": 5,
        "random_state": 123,
    })

    assert plan.split_strategy == "train_test_split"
    assert plan.test_size == 0.1
    assert plan.random_state == 123


def test_build_validation_plan_preserves_external_test_fields():
    plan = build_validation_plan({
        "external_test_enabled": True,
        "external_test_size": 0.25,
        "cv_strategy": "k_fold_cross_validation",
        "split_strategy": "train_test_split",
        "test_size": 0.25,
    })

    assert plan.external_test_enabled is True
    assert plan.external_test_size == 0.25
    assert plan.cv_strategy == "k_fold_cross_validation"