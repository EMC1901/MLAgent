from app.shared.common.exceptions import BusinessException


class IterationDecisionException(BusinessException):
    def __init__(self, message: str, error_code: str = "ITERATION_DECISION_ERROR"):
        super().__init__(message, error_code)


class IterationDecisionNotFoundException(IterationDecisionException):
    def __init__(self, message: str):
        super().__init__(message, "ITERATION_DECISION_NOT_FOUND")


class MetricEvaluationRequiredException(IterationDecisionException):
    def __init__(self, message: str):
        super().__init__(message, "METRIC_EVALUATION_REQUIRED")


class MetricEvaluationNotReadyException(IterationDecisionException):
    def __init__(self, message: str):
        super().__init__(message, "METRIC_EVALUATION_NOT_READY")


class ContextBuildFailedException(IterationDecisionException):
    def __init__(self, message: str):
        super().__init__(message, "CONTEXT_BUILD_FAILED")


class LLMCallFailedException(IterationDecisionException):
    def __init__(self, message: str):
        super().__init__(message, "LLM_CALL_FAILED")


class LLMParseFailedException(IterationDecisionException):
    def __init__(self, message: str):
        super().__init__(message, "LLM_PARSE_FAILED")


class DecisionValidationFailedException(IterationDecisionException):
    def __init__(self, message: str):
        super().__init__(message, "DECISION_VALIDATION_FAILED")


class PlanBuildFailedException(IterationDecisionException):
    def __init__(self, message: str):
        super().__init__(message, "PLAN_BUILD_FAILED")


class ArtifactSaveFailedException(IterationDecisionException):
    def __init__(self, message: str):
        super().__init__(message, "ARTIFACT_SAVE_FAILED")
