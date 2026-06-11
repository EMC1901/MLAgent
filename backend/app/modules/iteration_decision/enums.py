class DecisionStatus:
    DECIDING = "deciding"
    DECIDED = "decided"
    DECIDED_WITH_WARNING = "decided_with_warning"
    FALLBACK = "fallback"
    FAILED = "failed"


class Decision:
    ITERATE = "iterate"
    STOP = "stop"


class Confidence:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PerformanceLevel:
    EXCELLENT = "excellent"
    ACCEPTABLE = "acceptable"
    WEAK = "weak"
    FAILED = "failed"


class ImprovementLevel:
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NONE = "none"
    UNKNOWN = "unknown"


class StabilityLevel:
    STABLE = "stable"
    MODERATELY_UNSTABLE = "moderately_unstable"
    UNSTABLE = "unstable"


class DiagnosisDimension:
    DATA_SIDE = "data_side"
    FEATURE_SIDE = "feature_side"
    MODEL_SIDE = "model_side"
    EVALUATION_SIDE = "evaluation_side"


class TargetStage:
    WORKFLOW_PLANNING = "workflow_planning"
    FEATURE_ENGINEERING = "feature_engineering"
    FEATURE_PREPROCESSING = "feature_preprocessing"
    MODEL_SEARCH_CONTEXT = "model_search_context"
    PIPELINE_GENERATION = "pipeline_generation"
    PIPELINE_EXECUTION = "pipeline_execution"
    METRIC_EVALUATION = "metric_evaluation"


class RecommendationType:
    EXPAND_FEATURES = "expand_features"
    CHANGE_MODELS = "change_models"
    INCREASE_HPO = "increase_hpo"
    ADJUST_VALIDATION = "adjust_validation"
    CHANGE_METRIC = "change_metric"
    ADJUST_PREPROCESSING = "adjust_preprocessing"
    EXPAND_DATA = "expand_data"


class EvidenceType:
    METRIC = "metric"
    RANKING = "ranking"
    BASELINE = "baseline"
    FOLD_STABILITY = "fold_stability"
    DATA_PROFILE = "data_profile"
    FEATURE_PROFILE = "feature_profile"
    PIPELINE_LOG = "pipeline_log"
    MATERIALS_CONSTRAINT = "materials_constraint"
    WORKFLOW_QUALITY = "workflow_quality"


VALID_DECISIONS = {Decision.ITERATE, Decision.STOP}
VALID_CONFIDENCE_VALUES = {Confidence.LOW, Confidence.MEDIUM, Confidence.HIGH}
VALID_PERFORMANCE_LEVELS = {PerformanceLevel.EXCELLENT, PerformanceLevel.ACCEPTABLE, PerformanceLevel.WEAK, PerformanceLevel.FAILED}
VALID_IMPROVEMENT_LEVELS = {ImprovementLevel.STRONG, ImprovementLevel.MODERATE, ImprovementLevel.WEAK, ImprovementLevel.NONE, ImprovementLevel.UNKNOWN}

VALID_TARGET_STAGES = {
    TargetStage.WORKFLOW_PLANNING,
    TargetStage.FEATURE_ENGINEERING,
    TargetStage.FEATURE_PREPROCESSING,
    TargetStage.MODEL_SEARCH_CONTEXT,
    TargetStage.PIPELINE_GENERATION,
    TargetStage.PIPELINE_EXECUTION,
    TargetStage.METRIC_EVALUATION,
}

VALID_RECOMMENDATION_TYPES = {
    RecommendationType.EXPAND_FEATURES,
    RecommendationType.CHANGE_MODELS,
    RecommendationType.INCREASE_HPO,
    RecommendationType.ADJUST_VALIDATION,
    RecommendationType.CHANGE_METRIC,
    RecommendationType.ADJUST_PREPROCESSING,
    RecommendationType.EXPAND_DATA,
}

STAGE_ALIASES: dict[str, str] = {
    "feature_eng": TargetStage.FEATURE_ENGINEERING,
    "fe": TargetStage.FEATURE_ENGINEERING,
    "features": TargetStage.FEATURE_ENGINEERING,
    "preprocessing": TargetStage.FEATURE_PREPROCESSING,
    "feature_preprocess": TargetStage.FEATURE_PREPROCESSING,
    "fp": TargetStage.FEATURE_PREPROCESSING,
    "models": TargetStage.MODEL_SEARCH_CONTEXT,
    "model_search": TargetStage.MODEL_SEARCH_CONTEXT,
    "hpo": TargetStage.MODEL_SEARCH_CONTEXT,
    "pipeline": TargetStage.PIPELINE_EXECUTION,
    "training": TargetStage.PIPELINE_EXECUTION,
    "workflow": TargetStage.WORKFLOW_PLANNING,
    "planning": TargetStage.WORKFLOW_PLANNING,
    "evaluation": TargetStage.METRIC_EVALUATION,
    "metrics": TargetStage.METRIC_EVALUATION,
    "msc": TargetStage.MODEL_SEARCH_CONTEXT,
    "pg": TargetStage.PIPELINE_GENERATION,
    "pe": TargetStage.PIPELINE_EXECUTION,
    "me": TargetStage.METRIC_EVALUATION,
}


def canonical_target_stage(raw: str) -> str:
    if raw in VALID_TARGET_STAGES:
        return raw
    return STAGE_ALIASES.get(raw, raw)
