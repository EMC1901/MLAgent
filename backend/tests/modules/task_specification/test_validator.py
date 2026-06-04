import pytest
from app.modules.task_specification.validator import (
    check_required_fields,
    check_evaluation_metric_compatibility,
    check_input_dataset_consistency,
    check_evaluation_metric_provided,
    validate,
)


class TestCheckRequiredFields:
    def test_all_required_present(self):
        data = {
            "prediction_target": "band gap",
            "task_type": "regression",
            "dataset_description": "materials project data",
            "input_type": "composition",
            "target_column": "band_gap",
        }
        missing, issues = check_required_fields(data)
        assert missing == []
        assert issues == []

    def test_missing_fields(self):
        data = {}
        missing, issues = check_required_fields(data)
        assert "prediction_target" in missing
        assert "task_type" in missing
        assert "dataset_description" in missing
        assert "input_type" in missing
        assert "target_column" in missing
        assert len(issues) == 5
        assert all(sev == "error" for sev, _ in issues)


class TestCheckEvaluationMetricCompatibility:
    def test_compatible_metric(self):
        data = {"task_type": "regression", "evaluation_metric": "MAE"}
        assert check_evaluation_metric_compatibility(data) == []

    def test_incompatible_metric(self):
        data = {"task_type": "regression", "evaluation_metric": "Accuracy"}
        issues = check_evaluation_metric_compatibility(data)
        assert len(issues) == 1
        assert issues[0][0] == "error"
        assert "not suitable" in issues[0][1]

    def test_no_metric_specified(self):
        data = {"task_type": "regression"}
        assert check_evaluation_metric_compatibility(data) == []

    def test_all_regression_metrics(self):
        for metric in ["MAE", "RMSE", "R2"]:
            issues = check_evaluation_metric_compatibility({
                "task_type": "regression", "evaluation_metric": metric,
            })
            assert issues == [], f"{metric} should be valid for regression"

    def test_all_classification_metrics(self):
        for metric in ["Accuracy", "F1", "ROC-AUC"]:
            issues = check_evaluation_metric_compatibility({
                "task_type": "classification", "evaluation_metric": metric,
            })
            assert issues == [], f"{metric} should be valid for classification"


class TestCheckInputDatasetConsistency:
    def test_structure_with_cif(self):
        data = {"input_type": "structure", "dataset_description": "We have CIF files"}
        assert check_input_dataset_consistency(data) == []

    def test_structure_missing_source(self):
        data = {"input_type": "structure", "dataset_description": "Some data"}
        issues = check_input_dataset_consistency(data)
        assert len(issues) == 1
        assert issues[0][0] == "error"

    def test_composition_with_structure_keywords(self):
        data = {"input_type": "composition", "dataset_description": "Contains CIF files"}
        issues = check_input_dataset_consistency(data)
        assert len(issues) == 1
        assert issues[0][0] == "warning"

    def test_composition_normal(self):
        data = {"input_type": "composition", "dataset_description": "Chemical formulas"}
        assert check_input_dataset_consistency(data) == []


class TestCheckEvaluationMetricProvided:
    def test_no_metric_warns(self):
        data = {}
        issues = check_evaluation_metric_provided(data)
        assert len(issues) == 1
        assert issues[0][0] == "warning"

    def test_metric_present(self):
        data = {"evaluation_metric": "MAE"}
        assert check_evaluation_metric_provided(data) == []


class TestValidate:
    def test_valid_task(self):
        data = {
            "prediction_target": "band gap",
            "task_type": "regression",
            "dataset_description": "materials project",
            "input_type": "composition",
            "target_column": "band_gap",
            "evaluation_metric": "MAE",
        }
        result = validate(data)
        assert result["status"] == "valid"
        assert result["missing_fields"] == []
        assert result["warnings"] == []

    def test_incomplete_task(self):
        result = validate({"prediction_target": "band gap"})
        assert result["status"] == "incomplete"
        assert len(result["missing_fields"]) >= 4

    def test_invalid_metric_compatibility(self):
        data = {
            "prediction_target": "band gap",
            "task_type": "regression",
            "dataset_description": "test",
            "input_type": "composition",
            "target_column": "x",
            "evaluation_metric": "Accuracy",
        }
        result = validate(data)
        assert result["status"] == "invalid"

    def test_valid_with_warning(self):
        data = {
            "prediction_target": "band gap",
            "task_type": "regression",
            "dataset_description": "test",
            "input_type": "composition",
            "target_column": "x",
        }
        result = validate(data)
        assert result["status"] == "valid_with_warning"
        assert len(result["warnings"]) >= 1

    def test_missing_fields_take_priority_over_warnings(self):
        data = {"prediction_target": "band gap"}
        result = validate(data)
        assert result["status"] == "incomplete"

    def test_errors_take_priority_over_warnings(self):
        data = {
            "prediction_target": "band gap",
            "task_type": "regression",
            "dataset_description": "test",
            "input_type": "structure",
            "target_column": "x",
        }
        result = validate(data)
        # structure without source keywords -> error, plus missing metric -> warning
        assert result["status"] in ("invalid", "valid_with_warning")
