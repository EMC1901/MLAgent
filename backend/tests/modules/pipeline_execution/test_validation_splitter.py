import pandas as pd

from app.modules.pipeline_execution.validation_splitter import (
    create_external_test_split,
    create_validation_splits,
)


def test_train_test_split_uses_explicit_test_size():
    X = pd.DataFrame({"x": range(100)})
    y = pd.Series(range(100))

    splits = create_validation_splits(
        X,
        y,
        {
            "split_strategy": "train_test_split",
            "test_size": 0.1,
            "random_state": 42,
            "shuffle": True,
        },
    )

    assert len(splits) == 1
    assert splits[0]["train_size"] == 90
    assert splits[0]["validation_size"] == 10


def test_external_test_split_isolated_before_cv():
    X = pd.DataFrame({"x": range(100)})
    y = pd.Series(range(100))

    split = create_external_test_split(
        X,
        y,
        {
            "external_test_enabled": True,
            "external_test_size": 0.2,
            "random_state": 42,
            "shuffle": True,
        },
    )

    train_pool = set(split["train_pool_indices"].tolist())
    test = set(split["test_indices"].tolist())
    assert split["train_pool_size"] == 80
    assert split["external_test_size"] == 20
    assert train_pool.isdisjoint(test)
    assert len(train_pool | test) == 100