import pandas as pd

from app.modules.interpretability_analysis import prediction_artifact_loader as loader


def test_load_all_prediction_artifacts_indexes_by_sample_id(monkeypatch):
    frames = {
        "fold_0.parquet": pd.DataFrame({
            "sample_id": [10, 20],
            "y_true": [1.0, 2.0],
            "y_pred": [1.1, 1.9],
            "fold_index": [0, 0],
        }),
        "fold_1.parquet": pd.DataFrame({
            "sample_id": [30],
            "y_true": [3.0],
            "y_pred": [3.2],
            "fold_index": [1],
        }),
    }

    monkeypatch.setattr(loader, "load_prediction_artifact", lambda path: frames[path])

    df = loader.load_all_prediction_artifacts(["fold_0.parquet", "fold_1.parquet"])

    assert df.attrs["index_source"] == "sample_id"
    assert list(df.index) == [10, 20, 30]
    assert df.loc[20, "y_pred"] == 1.9


def test_load_all_prediction_artifacts_deduplicates_sample_id(monkeypatch):
    frames = {
        "repeated.parquet": pd.DataFrame({
            "sample_id": [10, 10, 20],
            "y_true": [1.0, 1.0, 2.0],
            "y_pred": [0.8, 1.2, 2.1],
            "fold_index": [0, 1, 0],
            "model_id": ["m1", "m1", "m1"],
        }),
    }

    monkeypatch.setattr(loader, "load_prediction_artifact", lambda path: frames[path])

    df = loader.load_all_prediction_artifacts(["repeated.parquet"])

    assert list(df.index) == [10, 20]
    assert df.loc[10, "y_pred"] == 1.0
    assert df.loc[10, "model_id"] == "m1"
