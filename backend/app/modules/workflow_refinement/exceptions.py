from app.shared.common.exceptions import BusinessException


class WorkflowRefinementException(BusinessException):
    def __init__(self, message: str, error_code: str = "WORKFLOW_REFINEMENT_ERROR"):
        super().__init__(message, error_code)


class WorkflowRefinementNotFoundException(WorkflowRefinementException):
    def __init__(self, message: str):
        super().__init__(message, "WORKFLOW_REFINEMENT_NOT_FOUND")


class ResultDiagnosisRequiredException(WorkflowRefinementException):
    def __init__(self, message: str):
        super().__init__(message, "RESULT_DIAGNOSIS_REQUIRED")


class ResultDiagnosisNotReadyException(WorkflowRefinementException):
    def __init__(self, message: str):
        super().__init__(message, "RESULT_DIAGNOSIS_NOT_READY_FOR_WORKFLOW_REFINEMENT")


class WorkflowRefinementInputInvalidException(WorkflowRefinementException):
    def __init__(self, message: str):
        super().__init__(message, "WORKFLOW_REFINEMENT_INPUT_INVALID")


class WorkflowRefinementContextBuildException(WorkflowRefinementException):
    def __init__(self, message: str):
        super().__init__(message, "WORKFLOW_REFINEMENT_CONTEXT_BUILD_FAILED")


class LLMWorkflowRefinementCallException(WorkflowRefinementException):
    def __init__(self, message: str):
        super().__init__(message, "LLM_WORKFLOW_REFINEMENT_CALL_FAILED")


class LLMWorkflowRefinementParseException(WorkflowRefinementException):
    def __init__(self, message: str):
        super().__init__(message, "LLM_WORKFLOW_REFINEMENT_PARSE_FAILED")


class LLMWorkflowRefinementValidationException(WorkflowRefinementException):
    def __init__(self, message: str):
        super().__init__(message, "LLM_WORKFLOW_REFINEMENT_VALIDATION_FAILED")


class RevisedWorkflowPlanValidationException(WorkflowRefinementException):
    def __init__(self, message: str):
        super().__init__(message, "REVISED_WORKFLOW_PLAN_VALIDATION_FAILED")


class IterationRerunPlanBuildException(WorkflowRefinementException):
    def __init__(self, message: str):
        super().__init__(message, "ITERATION_RERUN_PLAN_BUILD_FAILED")


class WorkflowRefinementArtifactSaveException(WorkflowRefinementException):
    def __init__(self, message: str):
        super().__init__(message, "WORKFLOW_REFINEMENT_ARTIFACT_SAVE_FAILED")
