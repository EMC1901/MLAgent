class WorkflowPlanStatus:
    PENDING = "pending"
    PLANNING = "planning"
    PLANNED = "planned"
    PLANNED_WITH_WARNING = "planned_with_warning"
    FAILED = "failed"
    BLOCKED = "blocked"


class PlanningMode:
    LLM_GUIDED = "llm_guided"


class SplitStrategy:
    TRAIN_TEST_SPLIT = "train_test_split"
    K_FOLD_CV = "k_fold_cross_validation"
    STRATIFIED_K_FOLD = "stratified_k_fold"
    REPEATED_CV = "repeated_cv"


class HPOSearchMethod:
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN_OPT = "bayesian_optimization"


class BudgetLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InterpretabilityMethod:
    FEATURE_IMPORTANCE = "feature_importance"
    SHAP = "shap"
    PERMUTATION_IMPORTANCE = "permutation_importance"


class MetricDirection:
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class FeatureType:
    COMPOSITION_DESCRIPTORS = "composition_descriptors"
    STRUCTURE_DESCRIPTORS = "structure_descriptors"
    NUMERIC_DESCRIPTORS = "numeric_descriptors"
    GRAPH_REPRESENTATION = "graph_representation"
