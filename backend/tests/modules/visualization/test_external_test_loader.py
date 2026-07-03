from types import SimpleNamespace

import pandas as pd

from app.modules.visualization import visualization_data_builder as builder


def test_external_test_loader_filters_to_final_test_rows(monkeypatch):
    pe = SimpleNamespace(
        execution_json={
            "training_artifact_manifest": {
                "external_test_prediction_path": "/app/artifacts/training/pe_x/predictions/final_external_test_predictions.parquet"
            }
        }
    )
    source = pd.DataFrame({
        "sample_id": [1, 2, 3],
        "split": ["test", "validation", "test"],
        "is_final_external_test": [True, False, True],
        "y_true": [1.0, 2.0, 3.0],
        "y_pred": [1.1, 2.1, 2.9],
    })

    monkeypatch.setattr(builder.os.path, "exists", lambda path: True)
    monkeypatch.setattr(builder, "_load_table", lambda path: source)

    df = builder._load_external_test_prediction_dataframe(pe)

    assert df is not None
    assert len(df) == 2
    assert set(df["sample_id"]) == {1, 3}
    assert set(df["split"]) == {"test"}

def test_final_train_test_loader_filters_to_final_model_train_test_rows(monkeypatch):
    pe = SimpleNamespace(
        execution_json={
            "training_artifact_manifest": {
                "final_train_test_prediction_path": "/app/artifacts/training/pe_x/predictions/final_train_test_predictions.parquet"
            }
        }
    )
    source = pd.DataFrame({
        "sample_id": [1, 2, 3],
        "split": ["train", "test", "validation"],
        "is_final_model_prediction": [True, True, False],
        "y_true": [1.0, 2.0, 3.0],
        "y_pred": [1.0, 1.8, 2.7],
    })

    monkeypatch.setattr(builder.os.path, "exists", lambda path: True)
    monkeypatch.setattr(builder, "_load_table", lambda path: source)

    df = builder._load_final_train_test_prediction_dataframe(pe)

    assert df is not None
    assert len(df) == 2
    assert set(df["sample_id"]) == {1, 2}
    assert set(df["split"]) == {"train", "test"}


def test_predicted_vs_actual_preserves_split_and_reports_r2_by_split():
    source = pd.DataFrame({
        "sample_id": [1, 2, 3, 4],
        "split": ["train", "train", "test", "test"],
        "y_true": [1.0, 2.0, 1.0, 3.0],
        "y_pred": [1.0, 2.0, 1.0, 2.0],
    })
    me = SimpleNamespace(primary_metric="MAE", best_primary_metric_value=0.25)

    data = builder._predicted_vs_actual_from_predictions(source, me, None)

    assert data is not None
    assert {point["split"] for point in data.points} == {"train", "test"}
    r2_metrics = {
        metric["split"]: metric["metric_value"]
        for metric in data.split_metrics
        if metric["metric_name"] == "R2"
    }
    assert r2_metrics["train"] == 1.0
    assert r2_metrics["test"] == 0.5
