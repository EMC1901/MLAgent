class PipelineExecutionStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNING = "completed_with_warning"
    PARTIALLY_FAILED = "partially_failed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrialStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TrialType:
    BASELINE = "baseline"
    FIXED_PARAMS = "fixed_params"
    HPO = "hpo"


class ExecutionMode:
    SEQUENTIAL = "sequential"
    LIMITED_PARALLEL = "limited_parallel"


class PipelineRole:
    BASELINE = "baseline"
    CANDIDATE = "candidate"
    HPO_CANDIDATE = "hpo_candidate"


class SplitStrategy:
    TRAIN_TEST_SPLIT = "train_test_split"
    K_FOLD_CV = "k_fold_cross_validation"
    K_FOLD = "k_fold"
    STRATIFIED_K_FOLD = "stratified_k_fold"
    HOLDOUT = "holdout"
