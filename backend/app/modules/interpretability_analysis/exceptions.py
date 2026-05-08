from app.shared.common.exceptions import BusinessException


class InterpretabilityAnalysisNotFoundException(BusinessException):
    def __init__(self, message: str = "Interpretability analysis not found."):
        super().__init__(message, "INTERPRETABILITY_ANALYSIS_NOT_FOUND")


class FinalPipelineSelectionRequiredException(BusinessException):
    def __init__(self, message: str = "Final pipeline selection is required before interpretability analysis."):
        super().__init__(message, "FINAL_PIPELINE_SELECTION_REQUIRED")


class FinalPipelineSelectionNotReadyException(BusinessException):
    def __init__(self, message: str = "Final pipeline selection is not ready for interpretability analysis."):
        super().__init__(message, "FINAL_SELECTION_NOT_READY_FOR_INTERPRETABILITY")


class InterpretabilityInputInvalidException(BusinessException):
    def __init__(self, message: str = "Interpretability analysis input is invalid."):
        super().__init__(message, "INTERPRETABILITY_INPUT_INVALID")


class ModelArtifactLoadException(BusinessException):
    def __init__(self, message: str = "Failed to load model artifact."):
        super().__init__(message, "MODEL_ARTIFACT_LOAD_FAILED")


class FeatureMatrixLoadException(BusinessException):
    def __init__(self, message: str = "Failed to load feature matrix."):
        super().__init__(message, "FEATURE_MATRIX_LOAD_FAILED")


class PredictionArtifactLoadException(BusinessException):
    def __init__(self, message: str = "Failed to load prediction artifact."):
        super().__init__(message, "PREDICTION_ARTIFACT_LOAD_FAILED")


class InterpretabilityMethodSelectionException(BusinessException):
    def __init__(self, message: str = "Failed to select interpretability methods."):
        super().__init__(message, "INTERPRETABILITY_METHOD_SELECTION_FAILED")


class FeatureImportanceCalculationException(BusinessException):
    def __init__(self, message: str = "Feature importance calculation failed."):
        super().__init__(message, "FEATURE_IMPORTANCE_CALCULATION_FAILED")


class ShapCalculationException(BusinessException):
    def __init__(self, message: str = "SHAP calculation failed."):
        super().__init__(message, "SHAP_CALCULATION_FAILED")


class LocalExplanationException(BusinessException):
    def __init__(self, message: str = "Local explanation generation failed."):
        super().__init__(message, "LOCAL_EXPLANATION_FAILED")


class LLMInterpretabilitySummaryException(BusinessException):
    def __init__(self, message: str = "LLM interpretability summary failed."):
        super().__init__(message, "LLM_INTERPRETABILITY_SUMMARY_FAILED")


class FinalOutputInputBuildException(BusinessException):
    def __init__(self, message: str = "Failed to build final output input."):
        super().__init__(message, "FINAL_OUTPUT_INPUT_BUILD_FAILED")


class InterpretabilityArtifactSaveException(BusinessException):
    def __init__(self, message: str = "Failed to save interpretability artifacts."):
        super().__init__(message, "INTERPRETABILITY_ARTIFACT_SAVE_FAILED")
