from app.shared.common.exceptions import BusinessException


class PipelineExecutionNotFoundException(BusinessException):
    def __init__(self, message: str = "Pipeline execution not found."):
        super().__init__(message, "PIPELINE_EXECUTION_NOT_FOUND")


class PipelineGenerationRequiredException(BusinessException):
    def __init__(self, message: str = "Pipeline generation is required before execution."):
        super().__init__(message, "PIPELINE_GENERATION_REQUIRED")


class PipelineGenerationNotReadyException(BusinessException):
    def __init__(self, message: str = "Pipeline generation is not ready for execution."):
        super().__init__(message, "PIPELINE_GENERATION_NOT_READY")


class ExecutionInputInvalidException(BusinessException):
    def __init__(self, message: str = "Execution input is invalid."):
        super().__init__(message, "EXECUTION_INPUT_INVALID")


class TrainingDataLoadException(BusinessException):
    def __init__(self, message: str = "Failed to load training data."):
        super().__init__(message, "TRAINING_DATA_LOAD_FAILED")


class ValidationSplitException(BusinessException):
    def __init__(self, message: str = "Failed to create validation splits."):
        super().__init__(message, "VALIDATION_SPLIT_FAILED")


class ModelInstantiationException(BusinessException):
    def __init__(self, message: str = "Failed to instantiate model."):
        super().__init__(message, "MODEL_INSTANTIATION_FAILED")


class TrialGenerationException(BusinessException):
    def __init__(self, message: str = "Failed to generate trial parameters."):
        super().__init__(message, "TRIAL_GENERATION_FAILED")


class TrialExecutionException(BusinessException):
    def __init__(self, message: str = "Trial execution failed."):
        super().__init__(message, "TRIAL_EXECUTION_FAILED")


class TrainingArtifactSaveException(BusinessException):
    def __init__(self, message: str = "Failed to save training artifacts."):
        super().__init__(message, "TRAINING_ARTIFACT_SAVE_FAILED")


class MetricEvaluationInputBuildException(BusinessException):
    def __init__(self, message: str = "Failed to build metric evaluation input."):
        super().__init__(message, "METRIC_EVALUATION_INPUT_BUILD_FAILED")
