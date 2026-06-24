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