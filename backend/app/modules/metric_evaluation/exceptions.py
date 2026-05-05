from app.shared.common.exceptions import BusinessException


class MetricEvaluationException(BusinessException):
    def __init__(self, message: str, error_code: str = "METRIC_EVALUATION_ERROR"):
        super().__init__(message, error_code)


class MetricEvaluationNotFoundException(MetricEvaluationException):
    def __init__(self, message: str):
        super().__init__(message, "METRIC_EVALUATION_NOT_FOUND")


class PipelineExecutionRequiredException(MetricEvaluationException):
    def __init__(self, message: str):
        super().__init__(message, "PIPELINE_EXECUTION_REQUIRED")


class PipelineExecutionNotReadyException(MetricEvaluationException):
    def __init__(self, message: str):
        super().__init__(message, "PIPELINE_EXECUTION_NOT_READY_FOR_METRIC_EVALUATION")


class MetricEvaluationInputInvalidException(MetricEvaluationException):
    def __init__(self, message: str):
        super().__init__(message, "METRIC_EVALUATION_INPUT_INVALID")


class PredictionArtifactLoadException(MetricEvaluationException):
    def __init__(self, message: str):
        super().__init__(message, "PREDICTION_ARTIFACT_LOAD_FAILED")


class MetricNotSupportedException(MetricEvaluationException):
    def __init__(self, message: str):
        super().__init__(message, "METRIC_NOT_SUPPORTED")


class MetricCalculationException(MetricEvaluationException):
    def __init__(self, message: str):
        super().__init__(message, "METRIC_CALCULATION_FAILED")


class MetricAggregationException(MetricEvaluationException):
    def __init__(self, message: str):
        super().__init__(message, "METRIC_AGGREGATION_FAILED")


class ModelRankingException(MetricEvaluationException):
    def __init__(self, message: str):
        super().__init__(message, "MODEL_RANKING_FAILED")


class BaselineComparisonException(MetricEvaluationException):
    def __init__(self, message: str):
        super().__init__(message, "BASELINE_COMPARISON_FAILED")


class ResultDiagnosisInputBuildException(MetricEvaluationException):
    def __init__(self, message: str):
        super().__init__(message, "RESULT_DIAGNOSIS_INPUT_BUILD_FAILED")


class EvaluationArtifactSaveException(MetricEvaluationException):
    def __init__(self, message: str):
        super().__init__(message, "EVALUATION_ARTIFACT_SAVE_FAILED")
