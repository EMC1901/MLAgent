from app.shared.common.exceptions import BusinessException


class FeaturePreprocessingException(BusinessException):
    def __init__(self, message: str, error_code: str = "FEATURE_PREPROCESSING_ERROR"):
        super().__init__(message, error_code)


class FeaturePreprocessingNotFoundException(FeaturePreprocessingException):
    def __init__(self, message: str):
        super().__init__(message, "FEATURE_PREPROCESSING_NOT_FOUND")


class FeaturePreprocessingUpstreamNotReadyException(FeaturePreprocessingException):
    def __init__(self, message: str, error_code: str = "UPSTREAM_NOT_READY"):
        super().__init__(message, error_code)


class FeatureArtifactLoadException(FeaturePreprocessingException):
    def __init__(self, message: str = "Failed to load raw feature artifact."):
        super().__init__(message, "FEATURE_ARTIFACT_LOAD_FAILED")


class FeatureArtifactMissingException(FeaturePreprocessingException):
    def __init__(self, message: str = "Raw feature artifact is missing."):
        super().__init__(message, "FEATURE_ARTIFACT_MISSING")


class TargetColumnMissingException(FeaturePreprocessingException):
    def __init__(self, message: str = "Target column is missing in the feature matrix."):
        super().__init__(message, "TARGET_COLUMN_MISSING")


class NoValidFeaturesException(FeaturePreprocessingException):
    def __init__(self, message: str = "No valid features remain after filtering."):
        super().__init__(message, "NO_VALID_FEATURES")


class ImputationFailedException(FeaturePreprocessingException):
    def __init__(self, message: str = "Imputation failed."):
        super().__init__(message, "IMPUTATION_FAILED")


class ScalingFailedException(FeaturePreprocessingException):
    def __init__(self, message: str = "Scaling failed."):
        super().__init__(message, "SCALING_FAILED")


class EncodingFailedException(FeaturePreprocessingException):
    def __init__(self, message: str = "Encoding failed."):
        super().__init__(message, "ENCODING_FAILED")


class FeatureSelectionFailedException(FeaturePreprocessingException):
    def __init__(self, message: str = "Feature selection failed."):
        super().__init__(message, "FEATURE_SELECTION_FAILED")


class ModelReadyArtifactSaveException(FeaturePreprocessingException):
    def __init__(self, message: str = "Failed to save model-ready artifact."):
        super().__init__(message, "MODEL_READY_ARTIFACT_SAVE_FAILED")


class PreprocessorArtifactSaveException(FeaturePreprocessingException):
    def __init__(self, message: str = "Failed to save preprocessor artifact."):
        super().__init__(message, "PREPROCESSOR_ARTIFACT_SAVE_FAILED")
