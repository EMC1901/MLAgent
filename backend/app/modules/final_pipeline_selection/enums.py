class FinalPipelineSelectionStatus:
    SELECTING = "selecting"
    SELECTED = "selected"
    SELECTED_WITH_WARNING = "selected_with_warning"
    FAILED = "failed"


class CandidateStatus:
    ELIGIBLE = "eligible"
    SELECTED = "selected"
    REJECTED = "rejected"
    WARNING = "warning"


class SelectionProfile:
    METRIC_FIRST = "metric_first"
    BALANCED = "balanced"
    INTERPRETABLE = "interpretable"
    EFFICIENT = "efficient"


class TrialType:
    BASELINE = "baseline"
    FIXED_PARAMS = "fixed_params"
    HPO = "hpo"


class PipelineRole:
    BASELINE = "baseline"
    CANDIDATE = "candidate"
    HPO_CANDIDATE = "hpo_candidate"


class LLMConfidenceLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ArtifactIntegrityStatus:
    COMPLETE = "complete"
    PARTIAL = "partial"
    MISSING = "missing"


class LLMExplanationReviewStatus:
    SUCCEEDED = "succeeded"
    FAILED_OR_FALLBACK = "failed_or_fallback"


VALID_STATUSES = {
    FinalPipelineSelectionStatus.SELECTING,
    FinalPipelineSelectionStatus.SELECTED,
    FinalPipelineSelectionStatus.SELECTED_WITH_WARNING,
    FinalPipelineSelectionStatus.FAILED,
}

VALID_CANDIDATE_STATUSES = {
    CandidateStatus.ELIGIBLE,
    CandidateStatus.SELECTED,
    CandidateStatus.REJECTED,
    CandidateStatus.WARNING,
}

VALID_SELECTION_PROFILES = {
    SelectionProfile.METRIC_FIRST,
    SelectionProfile.BALANCED,
    SelectionProfile.INTERPRETABLE,
    SelectionProfile.EFFICIENT,
}

VALID_TRIAL_TYPES = {
    TrialType.BASELINE,
    TrialType.FIXED_PARAMS,
    TrialType.HPO,
}

VALID_CONFIDENCE_LEVELS = {
    LLMConfidenceLevel.LOW,
    LLMConfidenceLevel.MEDIUM,
    LLMConfidenceLevel.HIGH,
}


# Interpretability score lookup by model family
INTERPRETABILITY_SCORE_MAP = {
    "linear": 1.0,
    "ridge": 1.0,
    "lasso": 1.0,
    "elastic_net": 1.0,
    "elasticnet": 1.0,
    "random_forest": 0.7,
    "randomforest": 0.7,
    "gradient_boosting": 0.5,
    "gradientboosting": 0.5,
    "xgboost": 0.5,
    "xgb": 0.5,
    "svr": 0.4,
    "svm": 0.4,
    "svc": 0.4,
    "logistic_regression": 1.0,
    "logisticregression": 1.0,
    "knn": 0.4,
    "kneighbors": 0.4,
    "gaussian_process": 0.6,
    "gaussianprocess": 0.6,
    "gp": 0.6,
    "decision_tree": 1.0,
    "decisiontree": 1.0,
    "lightgbm": 0.5,
    "lgbm": 0.5,
    "mlp": 0.3,
    "extra_trees": 0.7,
    "extratrees": 0.7,
    "dummy_mean": 0.8,
    "dummy": 0.8,
}

# Default selection policy weights per profile
PROFILE_WEIGHTS = {
    SelectionProfile.METRIC_FIRST: {
        "primary_metric_weight": 0.6,
        "stability_weight": 0.15,
        "baseline_improvement_weight": 0.1,
        "interpretability_weight": 0.1,
        "cost_weight": 0.05,
        "constraint_weight": 0.0,
    },
    SelectionProfile.BALANCED: {
        "primary_metric_weight": 0.5,
        "stability_weight": 0.2,
        "baseline_improvement_weight": 0.15,
        "interpretability_weight": 0.1,
        "cost_weight": 0.05,
        "constraint_weight": 0.0,
    },
    SelectionProfile.INTERPRETABLE: {
        "primary_metric_weight": 0.35,
        "stability_weight": 0.15,
        "baseline_improvement_weight": 0.1,
        "interpretability_weight": 0.3,
        "cost_weight": 0.1,
        "constraint_weight": 0.0,
    },
    SelectionProfile.EFFICIENT: {
        "primary_metric_weight": 0.4,
        "stability_weight": 0.1,
        "baseline_improvement_weight": 0.1,
        "interpretability_weight": 0.1,
        "cost_weight": 0.3,
        "constraint_weight": 0.0,
    },
}

# Tie-breaker order per profile
TIE_BREAKER_ORDER = ["primary_metric", "stability", "interpretability", "cost"]
