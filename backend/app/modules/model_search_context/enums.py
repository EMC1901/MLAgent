class ModelSearchContextStatus:
    PENDING = "pending"
    ANALYZING = "analyzing"
    LLM_ADVISING = "llm_advising"
    VALIDATING_ADVICE = "validating_advice"
    UPDATING = "updating"
    UPDATED = "updated"
    UPDATED_WITH_WARNING = "updated_with_warning"
    FAILED = "failed"
    BLOCKED = "blocked"


class UpdateMode:
    LLM_GUIDED_WITH_SYSTEM_VALIDATION = "llm_guided_with_system_validation"
    SYSTEM_ONLY = "system_only"


class HPOBudgetLevel:
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class SplitStrategy:
    TRAIN_TEST_SPLIT = "train_test_split"
    K_FOLD_CV = "k_fold_cross_validation"
    STRATIFIED_K_FOLD = "stratified_k_fold"
    REPEATED_CV = "repeated_cv"


class MetricDirection:
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class TaskType:
    REGRESSION = "regression"
    CLASSIFICATION = "classification"


class SearchSpaceProfile:
    NARROW = "narrow"
    MODERATE = "moderate"
    WIDE = "wide"


class ModelPriority:
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
