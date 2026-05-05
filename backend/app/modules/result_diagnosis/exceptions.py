from app.shared.common.exceptions import BusinessException


class ResultDiagnosisException(BusinessException):
    def __init__(self, message: str, error_code: str = "RESULT_DIAGNOSIS_ERROR"):
        super().__init__(message, error_code)


class ResultDiagnosisNotFoundException(ResultDiagnosisException):
    def __init__(self, message: str):
        super().__init__(message, "RESULT_DIAGNOSIS_NOT_FOUND")


class MetricEvaluationRequiredException(ResultDiagnosisException):
    def __init__(self, message: str):
        super().__init__(message, "METRIC_EVALUATION_REQUIRED")


class MetricEvaluationNotReadyException(ResultDiagnosisException):
    def __init__(self, message: str):
        super().__init__(message, "METRIC_EVALUATION_NOT_READY_FOR_DIAGNOSIS")


class DiagnosisInputInvalidException(ResultDiagnosisException):
    def __init__(self, message: str):
        super().__init__(message, "RESULT_DIAGNOSIS_INPUT_INVALID")


class DiagnosticContextBuildException(ResultDiagnosisException):
    def __init__(self, message: str):
        super().__init__(message, "DIAGNOSTIC_CONTEXT_BUILD_FAILED")


class LLMDiagnosisCallException(ResultDiagnosisException):
    def __init__(self, message: str):
        super().__init__(message, "LLM_DIAGNOSIS_CALL_FAILED")


class LLMDiagnosisParseException(ResultDiagnosisException):
    def __init__(self, message: str):
        super().__init__(message, "LLM_DIAGNOSIS_PARSE_FAILED")


class LLMDiagnosisValidationException(ResultDiagnosisException):
    def __init__(self, message: str):
        super().__init__(message, "LLM_DIAGNOSIS_VALIDATION_FAILED")


class ClosedLoopInputBuildException(ResultDiagnosisException):
    def __init__(self, message: str):
        super().__init__(message, "CLOSED_LOOP_REFINEMENT_INPUT_BUILD_FAILED")


class DiagnosisArtifactSaveException(ResultDiagnosisException):
    def __init__(self, message: str):
        super().__init__(message, "DIAGNOSIS_ARTIFACT_SAVE_FAILED")
