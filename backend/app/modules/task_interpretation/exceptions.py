from app.shared.common.exceptions import BusinessException


class TaskInterpretationException(BusinessException):
    def __init__(self, message: str, error_code: str = "TASK_INTERPRETATION_ERROR"):
        super().__init__(message, error_code)


class TaskNotReadyException(TaskInterpretationException):
    def __init__(self, message: str = "Only valid or valid_with_warning tasks can be interpreted."):
        super().__init__(message, error_code="TASK_NOT_READY")


class LLMCallException(TaskInterpretationException):
    def __init__(self, message: str = "LLM interpretation failed."):
        super().__init__(message, error_code="LLM_CALL_FAILED")


class LLMOutputParseException(TaskInterpretationException):
    def __init__(self, message: str = "Failed to parse LLM output as valid JSON."):
        super().__init__(message, error_code="LLM_OUTPUT_PARSE_ERROR")


class LLMOutputValidationException(TaskInterpretationException):
    def __init__(self, message: str = "LLM output does not match Task Interpretation Schema."):
        super().__init__(message, error_code="LLM_OUTPUT_VALIDATION_ERROR")


class InterpretationNotFoundException(TaskInterpretationException):
    def __init__(self, message: str = "Task interpretation not found."):
        super().__init__(message, error_code="INTERPRETATION_NOT_FOUND")
