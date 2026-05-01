from app.shared.common.exceptions import BusinessException


class DatasetProfileException(BusinessException):
    def __init__(self, message: str, error_code: str = "DATASET_PROFILE_ERROR"):
        super().__init__(message, error_code)


class DatasetProfileNotFoundException(DatasetProfileException):
    def __init__(self, message: str = "Dataset profile not found."):
        super().__init__(message, error_code="DATASET_PROFILE_NOT_FOUND")


class DatasetContextBuildException(DatasetProfileException):
    def __init__(self, message: str):
        super().__init__(message, error_code="DATASET_CONTEXT_BUILD_FAILED")


class DatasetSourceUnresolvedException(DatasetProfileException):
    def __init__(self, message: str = "Unable to resolve dataset source."):
        super().__init__(message, error_code="DATASET_SOURCE_UNRESOLVED")


class DatasetSourceUnsupportedException(DatasetProfileException):
    def __init__(self, message: str = "Dataset source type is not currently supported."):
        super().__init__(message, error_code="DATASET_SOURCE_UNSUPPORTED")


class DatasetLoadException(DatasetProfileException):
    def __init__(self, message: str = "Failed to load dataset."):
        super().__init__(message, error_code="DATASET_LOAD_FAILED")


class DatasetSchemaException(DatasetProfileException):
    def __init__(self, message: str):
        super().__init__(message, error_code="DATASET_SCHEMA_ERROR")


class DatasetModalityMismatchException(DatasetProfileException):
    def __init__(self, message: str = "Input modality does not match dataset content."):
        super().__init__(message, error_code="MODALITY_MISMATCH")
