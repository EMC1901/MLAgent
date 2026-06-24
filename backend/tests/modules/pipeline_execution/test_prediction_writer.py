import pandas as pd

from app.modules.pipeline_execution.prediction_writer import save_predictions


def test_save_predictions_can_write_final_external_test_artifact(tmp_path):
    path = save_predictions(
        y_true=[1.0, 2.0],
        y_pred=[1.1, 1.9],
        sample_indices=[10, 20],
        trial_id="trial_best",
        pipeline_spec_id="spec_1",
        fold_index=-1,
        model_id="ridge",
        output_dir=str(tmp_path),
        split="test",
        filename="final_external_test_predictions.parquet",
        extra_columns={
            "is_final_external_test": True,
            "prediction_source": "final_external_test",
        },
    )

    df = pd.read_parquet(path)
    assert len(df) == 2
    assert set(df["sample_id"]) == {10, 20}
    assert set(df["split"]) == {"test"}
    assert df["is_final_external_test"].all()
    assert set(df["prediction_source"]) == {"final_external_test"}