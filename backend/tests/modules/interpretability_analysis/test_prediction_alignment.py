import pandas as pd

from app.modules.interpretability_analysis.service import _align_predictions_to_feature_rows


def test_align_predictions_to_feature_rows_uses_sample_id_index():
    X = pd.DataFrame({"feat": [1.0, 2.0, 3.0]}, index=[10, 20, 30])
    y = pd.Series([0.1, 0.2, 0.3], index=X.index)
    y_pred = pd.Series([2.2, 3.3], index=[20, 30])
    y_true = pd.Series([0.2, 0.3], index=[20, 30])

    X2, y2, yp2, yt2, info = _align_predictions_to_feature_rows(
        X=X,
        y=y,
        y_pred=y_pred,
        y_true=y_true,
        prediction_index_source="sample_id",
    )

    assert info["aligned"] is True
    assert info["strategy"] == "sample_id"
    assert list(X2.index) == [20, 30]
    assert list(y2.index) == [20, 30]
    assert list(yp2.index) == [20, 30]
    assert list(yt2.index) == [20, 30]
