from app.shared.common.exceptions import BusinessException


class WorkflowPlanningException(BusinessException):
    def __init__(self, message: str, error_code: str = "WORKFLOW_PLANNING_ERROR"):
        super().__init__(message, error_code)


class WorkflowPlanNotFoundException(WorkflowPlanningException):
    def __init__(self, message: str):
        super().__init__(message, "WORKFLOW_PLAN_NOT_FOUND")


class UpstreamNotReadyException(WorkflowPlanningException):
    def __init__(self, message: str, error_code: str):
        super().__init__(message, error_code)


class WorkflowPlanningLLMCallException(WorkflowPlanningException):
    def __init__(self, message: str = "LLM call failed."):
        super().__init__(message, "LLM_CALL_FAILED")


class WorkflowPlanParseException(WorkflowPlanningException):
    def __init__(self, message: str = "LLM output parse error."):
        super().__init__(message, "LLM_OUTPUT_PARSE_ERROR")


class WorkflowPlanValidationException(WorkflowPlanningException):
    def __init__(self, message: str = "Workflow plan validation failed."):
        super().__init__(message, "WORKFLOW_PLAN_VALIDATION_FAILED")
