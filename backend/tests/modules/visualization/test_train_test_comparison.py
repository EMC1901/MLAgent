from types import SimpleNamespace

from app.modules.visualization import visualization_data_builder as builder


def _metric_evaluation(**overrides):
    base = {
        "best_model_id": "model_best",
        "best_trial_id": "trial_best",
        "best_primary_metric_value": 0.2,
        "primary_metric": "MAE",
        "evaluation_json": {},
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_build_train_test_comparison_uses_best_trial_fold_metrics():
    me = _metric_evaluation(
        evaluation_json={
            "trial_metric_results": [
                {
                    "trial_id": "trial_other",
                    "fold_metrics": [
                        {"fold_index": 0, "n_samples": 99, "primary_metric_value": 999.0},
                    ],
                },
                {
                    "trial_id": "trial_best",
                    "fold_metrics": [
                        {"fold_index": 0, "n_samples": 10, "primary_metric_value": 0.2},
                        {"fold_index": 1, "n_samples": 11, "metrics": {"MAE": 0.3}},
                    ],
                },
            ],
        },
    )

    data = builder._build_train_test_comparison(me)

    assert data is not None
    assert [item["fold_index"] for item in data.comparisons] == [0, 1]
    assert [item["test_value"] for item in data.comparisons] == [0.2, 0.3]
    assert [item["n_samples"] for item in data.comparisons] == [10, 11]
    assert {item["metric_name"] for item in data.comparisons} == {"MAE"}


def test_build_model_performance_allows_missing_fold_metrics():
    me = _metric_evaluation(evaluation_json={"trial_metric_results": []})

    section = builder._build_model_performance(None, me, None, "regression")

    assert section.model_id == "model_best"
    assert section.model_trial_id == "trial_best"
    assert section.train_test_comparison is None
    assert section.cross_validation_box_plot is None