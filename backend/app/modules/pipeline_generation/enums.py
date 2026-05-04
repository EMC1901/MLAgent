class PipelineGenerationStatus:
    GENERATED = "generated"
    GENERATED_WITH_WARNING = "generated_with_warning"
    FAILED = "failed"


class GenerationMode:
    SYSTEM_TEMPLATE_BASED = "system_template_based"
    SYSTEM_TEMPLATE_WITH_LLM_REVIEW = "system_template_with_llm_review"


class PipelineRole:
    BASELINE = "baseline"
    CANDIDATE = "candidate"
    HPO_CANDIDATE = "hpo_candidate"


class PipelineProfile:
    COMPACT = "compact"
    STANDARD = "standard"
    FULL = "full"


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


class ModelPriority:
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComponentType:
    INPUT_LOADER = "input_loader"
    PREPROCESSOR = "preprocessor"
    ESTIMATOR = "estimator"
    VALIDATION_SPLITTER = "validation_splitter"
    METRIC_EVALUATOR = "metric_evaluator"
    HPO_CONTROLLER = "hpo_controller"
