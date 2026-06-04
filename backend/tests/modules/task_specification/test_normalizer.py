import pytest
from app.modules.task_specification.normalizer import (
    normalize_task_type,
    normalize_input_type,
    normalize_evaluation_metric,
    normalize_user_priority,
    normalize_fields,
)


class TestNormalizeTaskType:
    def test_standard_value(self):
        assert normalize_task_type("regression") == "regression"

    def test_case_insensitive(self):
        assert normalize_task_type("REGRESSION") == "regression"

    def test_whitespace(self):
        assert normalize_task_type("  classification  ") == "classification"

    def test_empty(self):
        assert normalize_task_type("") == ""

    def test_none(self):
        assert normalize_task_type(None) is None


class TestNormalizeInputType:
    def test_standard_value(self):
        assert normalize_input_type("composition") == "composition"

    def test_variant_spelling(self):
        assert normalize_input_type("chemical composition") == "composition"
        assert normalize_input_type("Crystal structure") == "structure"

    def test_text_features(self):
        assert normalize_input_type("text-derived features") == "text_features"
        assert normalize_input_type("text features") == "text_features"


class TestNormalizeEvaluationMetric:
    def test_abbreviation(self):
        assert normalize_evaluation_metric("MAE") == "MAE"

    def test_full_name(self):
        assert normalize_evaluation_metric("mean absolute error") == "MAE"

    def test_case_insensitive(self):
        assert normalize_evaluation_metric("rmse") == "RMSE"

    def test_f1(self):
        assert normalize_evaluation_metric("f1 score") == "F1"


class TestNormalizeUserPriority:
    def test_normal_list(self):
        result = normalize_user_priority(["accuracy", "speed"])
        assert result == ["accuracy", "speed"]

    def test_empty_list(self):
        assert normalize_user_priority([]) == []

    def test_none(self):
        assert normalize_user_priority(None) == []


class TestNormalizeFields:
    def test_all_fields(self):
        raw = {
            "task_name": "  My Task  ",
            "task_type": "  Regression  ",
            "input_type": "Chemical composition",
            "evaluation_metric": "Mean Absolute Error",
            "user_priority": ["accuracy"],
            "prediction_target": " Band Gap ",
            "dataset_description": " test ",
            "target_column": " band_gap ",
        }
        result = normalize_fields(raw)
        assert result["task_name"] == "My Task"
        assert result["task_type"] == "regression"
        assert result["input_type"] == "composition"
        assert result["evaluation_metric"] == "MAE"
        assert result["user_priority"] == ["accuracy"]
        assert result["prediction_target"] == "Band Gap"

    def test_omits_none_values(self):
        raw = {
            "task_name": None,
            "task_type": "regression",
        }
        result = normalize_fields(raw)
        assert "task_name" not in result
        assert result["task_type"] == "regression"

    def test_empty_input(self):
        assert normalize_fields({}) == {}
