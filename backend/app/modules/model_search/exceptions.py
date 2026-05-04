from app.shared.common.exceptions import BusinessException


class ModelSearchException(BusinessException):
    def __init__(self, message: str, error_code: str = "MODEL_SEARCH_ERROR"):
        super().__init__(message, error_code)


class ModelSearchPlanNotFoundException(ModelSearchException):
    def __init__(self, message: str):
        super().__init__(message, "MODEL_SEARCH_PLAN_NOT_FOUND")


class ModelSearchContextRequiredException(ModelSearchException):
    def __init__(self, message: str = "Model Search Context not executed yet."):
        super().__init__(message, "MODEL_SEARCH_CONTEXT_REQUIRED")


class ModelSearchContextNotReadyException(ModelSearchException):
    def __init__(self, message: str = "Model Search Context status not ready."):
        super().__init__(message, "MODEL_SEARCH_CONTEXT_NOT_READY")


class ModelReadyInputNotReadyException(ModelSearchException):
    def __init__(self, message: str = "ready_for_model_search_plan is false."):
        super().__init__(message, "MODEL_READY_INPUT_NOT_READY")


class ModelRegistryUnavailableException(ModelSearchException):
    def __init__(self, message: str = "Model Registry unavailable."):
        super().__init__(message, "MODEL_REGISTRY_UNAVAILABLE")


class HPORegistryUnavailableException(ModelSearchException):
    def __init__(self, message: str = "HPO Registry unavailable."):
        super().__init__(message, "HPO_REGISTRY_UNAVAILABLE")


class LLMModelSearchCallException(ModelSearchException):
    def __init__(self, message: str = "LLM model search call failed."):
        super().__init__(message, "LLM_MODEL_SEARCH_CALL_FAILED")


class LLMModelSearchParseException(ModelSearchException):
    def __init__(self, message: str = "LLM model search output parse failed."):
        super().__init__(message, "LLM_MODEL_SEARCH_PARSE_FAILED")


class LLMModelSearchValidationException(ModelSearchException):
    def __init__(self, message: str = "LLM model search validation failed."):
        super().__init__(message, "LLM_MODEL_SEARCH_VALIDATION_FAILED")


class NoSupportedModelFoundException(ModelSearchException):
    def __init__(self, message: str = "No supported model found."):
        super().__init__(message, "NO_SUPPORTED_MODEL_FOUND")


class NoSupportedHPOMethodFoundException(ModelSearchException):
    def __init__(self, message: str = "No supported HPO method found."):
        super().__init__(message, "NO_SUPPORTED_HPO_METHOD_FOUND")


class SearchSpaceBuildException(ModelSearchException):
    def __init__(self, message: str = "Search space build failed."):
        super().__init__(message, "SEARCH_SPACE_BUILD_FAILED")


class TrialAllocationException(ModelSearchException):
    def __init__(self, message: str = "Trial allocation failed."):
        super().__init__(message, "TRIAL_ALLOCATION_FAILED")
