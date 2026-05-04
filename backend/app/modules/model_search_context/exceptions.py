from app.shared.common.exceptions import BusinessException


class ModelSearchContextException(BusinessException):
    def __init__(self, message: str, error_code: str = "MODEL_SEARCH_CONTEXT_ERROR"):
        super().__init__(message, error_code)


class ModelSearchContextNotFoundException(ModelSearchContextException):
    def __init__(self, message: str):
        super().__init__(message, "MODEL_SEARCH_CONTEXT_NOT_FOUND")


class UpstreamNotReadyException(ModelSearchContextException):
    def __init__(self, message: str, error_code: str):
        super().__init__(message, error_code)


class LLMCallException(ModelSearchContextException):
    def __init__(self, message: str = "LLM call failed."):
        super().__init__(message, "LLM_CALL_FAILED")


class LLMOutputParseException(ModelSearchContextException):
    def __init__(self, message: str = "LLM output parse error."):
        super().__init__(message, "LLM_OUTPUT_PARSE_ERROR")


class LLMAdviceValidationException(ModelSearchContextException):
    def __init__(self, message: str = "LLM advice validation failed."):
        super().__init__(message, "LLM_ADVICE_VALIDATION_FAILED")


class StrategyMergeException(ModelSearchContextException):
    def __init__(self, message: str = "Strategy merge failed."):
        super().__init__(message, "STRATEGY_MERGE_FAILED")
