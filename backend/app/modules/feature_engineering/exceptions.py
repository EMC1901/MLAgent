from app.shared.common.exceptions import BusinessException


class FeatureEngineeringException(BusinessException):
    def __init__(self, message: str, error_code: str = "FEATURE_ENGINEERING_ERROR"):
        super().__init__(message, error_code)


class FeatureEngineeringNotFoundException(FeatureEngineeringException):
    def __init__(self, message: str):
        super().__init__(message, "FEATURE_ENGINEERING_NOT_FOUND")


class FeatureEngineeringUpstreamNotReadyException(FeatureEngineeringException):
    def __init__(self, message: str, error_code: str = "UPSTREAM_NOT_READY"):
        super().__init__(message, error_code)


class FeatureStrategyMissingException(FeatureEngineeringException):
    def __init__(self, message: str = "Feature strategy is missing in the workflow plan."):
        super().__init__(message, "FEATURE_STRATEGY_MISSING")


class RawDataLoadException(FeatureEngineeringException):
    def __init__(self, message: str = "Failed to load raw data."):
        super().__init__(message, "RAW_DATA_LOAD_FAILED")


class InputModalityUnsupportedException(FeatureEngineeringException):
    def __init__(self, message: str = "Input modality is not supported."):
        super().__init__(message, "INPUT_MODALITY_UNSUPPORTED")


class FeaturizerNotAvailableException(FeatureEngineeringException):
    def __init__(self, message: str = "Requested featurizer is not available."):
        super().__init__(message, "FEATURIZER_NOT_AVAILABLE")


class FeatureGenerationException(FeatureEngineeringException):
    def __init__(self, message: str = "Feature generation failed."):
        super().__init__(message, "FEATURE_GENERATION_FAILED")


class FeatureMatrixInvalidException(FeatureEngineeringException):
    def __init__(self, message: str = "Feature matrix is invalid."):
        super().__init__(message, "FEATURE_MATRIX_INVALID")


class FeatureArtifactSaveException(FeatureEngineeringException):
    def __init__(self, message: str = "Failed to save feature artifact."):
        super().__init__(message, "FEATURE_ARTIFACT_SAVE_FAILED")


class PymatgenNotInstalledException(FeatureEngineeringException):
    def __init__(self, message: str = "pymatgen is not installed."):
        super().__init__(message, "PYMATGEN_NOT_INSTALLED")


class MatminerNotInstalledException(FeatureEngineeringException):
    def __init__(self, message: str = "matminer is not installed."):
        super().__init__(message, "MATMINER_NOT_INSTALLED")


class ExternalFeaturizerDependencyMissingException(FeatureEngineeringException):
    def __init__(self, message: str = "External featurizer dependency is missing."):
        super().__init__(message, "EXTERNAL_FEATURIZER_DEPENDENCY_MISSING")


class ExternalFeaturizerFailedException(FeatureEngineeringException):
    def __init__(self, message: str = "External featurizer execution failed."):
        super().__init__(message, "EXTERNAL_FEATURIZER_FAILED")


class CompositionParseFailedException(FeatureEngineeringException):
    def __init__(self, message: str = "Composition parsing failed."):
        super().__init__(message, "COMPOSITION_PARSE_FAILED")


class StructureParseFailedException(FeatureEngineeringException):
    def __init__(self, message: str = "Structure parsing failed."):
        super().__init__(message, "STRUCTURE_PARSE_FAILED")


class FeaturizerGroupFailedException(FeatureEngineeringException):
    def __init__(self, message: str = "Featurizer group execution failed."):
        super().__init__(message, "FEATURIZER_GROUP_FAILED")


class AllFeaturizersFailedException(FeatureEngineeringException):
    def __init__(self, message: str = "All featurizers failed."):
        super().__init__(message, "ALL_FEATURIZERS_FAILED")


class FeatureGroupMergeFailedException(FeatureEngineeringException):
    def __init__(self, message: str = "Feature group merge failed."):
        super().__init__(message, "FEATURE_GROUP_MERGE_FAILED")


class FeatureNameConflictException(FeatureEngineeringException):
    def __init__(self, message: str = "Feature name conflict detected."):
        super().__init__(message, "FEATURE_NAME_CONFLICT")


class FeatureDimensionTooHighException(FeatureEngineeringException):
    def __init__(self, message: str = "Feature dimension exceeds threshold."):
        super().__init__(message, "FEATURE_DIMENSION_TOO_HIGH")


class FeatureMissingRatioTooHighException(FeatureEngineeringException):
    def __init__(self, message: str = "Feature missing ratio exceeds threshold."):
        super().__init__(message, "FEATURE_MISSING_RATIO_TOO_HIGH")
