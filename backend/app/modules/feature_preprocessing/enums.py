class FeaturePreprocessingStatus:
    PENDING = "pending"
    LOADING_ARTIFACT = "loading_artifact"
    VALIDATING = "validating"
    FILTERING = "filtering"
    PREPROCESSING = "preprocessing"
    ARTIFACT_SAVING = "artifact_saving"
    PREPROCESSED = "preprocessed"
    PREPROCESSED_WITH_WARNING = "preprocessed_with_warning"
    FAILED = "failed"
    BLOCKED = "blocked"


class ImputationStrategy:
    MEDIAN = "median"
    MEAN = "mean"
    MOST_FREQUENT = "most_frequent"
    NONE = "none"


class ScalingStrategy:
    STANDARD_SCALER = "standard_scaler"
    ROBUST_SCALER = "robust_scaler"
    MINMAX_SCALER = "minmax_scaler"
    NONE = "none"


class EncodingStrategy:
    ONE_HOT = "one_hot"
    ORDINAL = "ordinal"
    NONE = "none"


class FeatureSelectionStrategy:
    VARIANCE_THRESHOLD = "variance_threshold"
    NONE = "none"


class FeatureDropReason:
    NON_NUMERIC_OBJECT = "non_numeric_object_column"
    ALL_MISSING = "all_missing"
    CONSTANT = "constant"
    HIGH_MISSING = "high_missing"
    INVALID_INF = "invalid_inf_values"


class FeatureGroupStatus:
    RETAINED = "retained"
    RETAINED_WITH_WARNING = "retained_with_warning"
    DROPPED = "dropped"
