class ModelSearchPlanStatus:
    PENDING = "pending"
    LOADING_CONTEXT = "loading_context"
    LLM_ADVISING = "llm_advising"
    VALIDATING_ADVICE = "validating_advice"
    GENERATING_PLAN = "generating_plan"
    PLANNED = "planned"
    PLANNED_WITH_WARNING = "planned_with_warning"
    FAILED = "failed"
    BLOCKED = "blocked"


class PlanningMode:
    LLM_GUIDED_WITH_REGISTRY_VALIDATION = "llm_guided_with_registry_validation"
    SYSTEM_ONLY = "system_only"


class HPOBudgetLevel:
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class SearchSpaceProfile:
    NARROW = "narrow"
    MODERATE = "moderate"
    WIDE = "wide"


class TaskType:
    REGRESSION = "regression"
    CLASSIFICATION = "classification"


class MetricDirection:
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class SplitStrategy:
    TRAIN_TEST_SPLIT = "train_test_split"
    K_FOLD_CV = "k_fold_cross_validation"
    STRATIFIED_K_FOLD = "stratified_k_fold"
    REPEATED_CV = "repeated_cv"


class ModelPriority:
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
