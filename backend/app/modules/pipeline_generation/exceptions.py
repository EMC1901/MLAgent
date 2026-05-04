from app.shared.common.exceptions import BusinessException


class PipelineGenerationException(BusinessException):
    def __init__(self, message: str, error_code: str = "PIPELINE_GENERATION_ERROR"):
        super().__init__(message, error_code)


class PipelineGenerationNotFoundException(PipelineGenerationException):
    def __init__(self, message: str):
        super().__init__(message, "PIPELINE_GENERATION_NOT_FOUND")


class ModelSearchPlanRequiredException(PipelineGenerationException):
    def __init__(self, message: str = "Model Search Plan is required."):
        super().__init__(message, "MODEL_SEARCH_PLAN_REQUIRED")


class ModelSearchPlanNotReadyException(PipelineGenerationException):
    def __init__(self, message: str = "Model Search Plan is not ready."):
        super().__init__(message, "MODEL_SEARCH_PLAN_NOT_READY")


class PipelineGenerationInputMissingException(PipelineGenerationException):
    def __init__(self, message: str = "Pipeline generation input is missing."):
        super().__init__(message, "PIPELINE_GENERATION_INPUT_MISSING")


class ArtifactResolveException(PipelineGenerationException):
    def __init__(self, message: str = "Artifact resolve failed."):
        super().__init__(message, "ARTIFACT_RESOLVE_FAILED")


class ComponentBindingException(PipelineGenerationException):
    def __init__(self, message: str = "Component binding failed."):
        super().__init__(message, "COMPONENT_BINDING_FAILED")


class PipelineSpecBuildException(PipelineGenerationException):
    def __init__(self, message: str = "Pipeline spec build failed."):
        super().__init__(message, "PIPELINE_SPEC_BUILD_FAILED")


class PipelineValidationException(PipelineGenerationException):
    def __init__(self, message: str = "Pipeline validation failed."):
        super().__init__(message, "PIPELINE_VALIDATION_FAILED")


class PipelineSafetyException(PipelineGenerationException):
    def __init__(self, message: str = "Pipeline safety check failed."):
        super().__init__(message, "PIPELINE_SAFETY_CHECK_FAILED")


class LLMPipelineReviewException(PipelineGenerationException):
    def __init__(self, message: str = "LLM pipeline review failed."):
        super().__init__(message, "LLM_PIPELINE_REVIEW_FAILED")


class ExecutionInputBuildException(PipelineGenerationException):
    def __init__(self, message: str = "Execution input build failed."):
        super().__init__(message, "EXECUTION_INPUT_BUILD_FAILED")
