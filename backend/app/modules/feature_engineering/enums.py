class FeatureEngineeringStatus:
    PENDING = "pending"
    LOADING_DATA = "loading_data"
    FEATURIZING = "featurizing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNING = "completed_with_warning"
    FAILED = "failed"
    BLOCKED = "blocked"


class FeatureType:
    COMPOSITION_DESCRIPTORS = "composition_descriptors"
    EXISTING_DESCRIPTORS = "existing_descriptors"
    STRUCTURE_DESCRIPTORS = "structure_descriptors"


class InputModality:
    COMPOSITION = "composition"
    DESCRIPTOR = "descriptor"
    STRUCTURE = "structure"


class ArtifactStorageType:
    LOCAL_FILE = "local_file"
