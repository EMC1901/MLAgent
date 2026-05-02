from app.shared.common.exceptions import BusinessException


class FeaturizerRegistryException(BusinessException):
    def __init__(self, message: str, error_code: str = "FEATURIZER_REGISTRY_ERROR"):
        super().__init__(message, error_code)


class FeaturizerNotFoundException(FeaturizerRegistryException):
    def __init__(self, name: str):
        super().__init__(
            f"Featurizer '{name}' not found in registry.",
            "FEATURIZER_NOT_FOUND",
        )


class FeaturizerNotAvailableException(FeaturizerRegistryException):
    def __init__(self, name: str, status: str):
        super().__init__(
            f"Featurizer '{name}' has status '{status}', not 'available'.",
            "FEATURIZER_NOT_AVAILABLE",
        )


class FeaturizerModalityMismatchException(FeaturizerRegistryException):
    def __init__(self, name: str, input_modality: str):
        super().__init__(
            f"Featurizer '{name}' does not support input modality '{input_modality}'.",
            "FEATURIZER_MODALITY_MISMATCH",
        )


class NoAvailableFeaturizerException(FeaturizerRegistryException):
    def __init__(self, input_modality: str):
        super().__init__(
            f"No available featurizer for input modality '{input_modality}'.",
            "NO_AVAILABLE_FEATURIZER",
        )
