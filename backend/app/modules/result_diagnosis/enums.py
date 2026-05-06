class ResultDiagnosisStatus:
    DIAGNOSING = "diagnosing"
    DIAGNOSED = "diagnosed"
    DIAGNOSED_WITH_WARNING = "diagnosed_with_warning"
    FALLBACK_DIAGNOSED = "fallback_diagnosed"
    FAILED = "failed"


class DiagnosisMode:
    LLM_BASED = "llm_based"
    HYBRID = "hybrid"
    SYSTEM_RULE_BASED = "system_rule_based"


class DiagnosisType:
    UNDERFITTING = "underfitting"
    OVERFITTING_RISK = "overfitting_risk"
    FEATURE_INSUFFICIENCY = "feature_insufficiency"
    FEATURE_NOISE = "feature_noise"
    MODEL_MISMATCH = "model_mismatch"
    HPO_INSUFFICIENT = "hpo_insufficient"
    VALIDATION_INSTABILITY = "validation_instability"
    WEAK_BASELINE_IMPROVEMENT = "weak_baseline_improvement"
    DATA_QUALITY_LIMITATION = "data_quality_limitation"
    METRIC_MISMATCH = "metric_mismatch"
    LIMITED_PIPELINE_GAIN = "limited_pipeline_gain"


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


class Severity:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceStrength:
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class ConfidenceLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Likelihood:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Actionability:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EvidenceType:
    METRIC = "metric"
    RANKING = "ranking"
    BASELINE = "baseline"
    FOLD_STABILITY = "fold_stability"
    DATA_PROFILE = "data_profile"
    FEATURE_PROFILE = "feature_profile"
    PIPELINE_LOG = "pipeline_log"


class TargetStage:
    WORKFLOW_PLANNING = "workflow_planning"
    FEATURE_ENGINEERING = "feature_engineering"
    PREPROCESSING = "preprocessing"
    MODEL_SEARCH = "model_search"
    HPO = "hpo"
    VALIDATION = "validation"


class RecommendationType:
    EXPAND_FEATURES = "expand_features"
    CHANGE_MODELS = "change_models"
    INCREASE_HPO = "increase_hpo"
    ADJUST_VALIDATION = "adjust_validation"
    CHANGE_METRIC = "change_metric"


class Priority:
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


VALID_DIAGNOSIS_TYPES = {
    DiagnosisType.UNDERFITTING,
    DiagnosisType.OVERFITTING_RISK,
    DiagnosisType.FEATURE_INSUFFICIENCY,
    DiagnosisType.FEATURE_NOISE,
    DiagnosisType.MODEL_MISMATCH,
    DiagnosisType.HPO_INSUFFICIENT,
    DiagnosisType.VALIDATION_INSTABILITY,
    DiagnosisType.WEAK_BASELINE_IMPROVEMENT,
    DiagnosisType.DATA_QUALITY_LIMITATION,
    DiagnosisType.METRIC_MISMATCH,
    DiagnosisType.LIMITED_PIPELINE_GAIN,
}

VALID_SEVERITY_VALUES = {Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL}
VALID_CONFIDENCE_VALUES = {ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH}
VALID_EVIDENCE_STRENGTH_VALUES = {EvidenceStrength.WEAK, EvidenceStrength.MODERATE, EvidenceStrength.STRONG}
VALID_TARGET_STAGES = {
    TargetStage.WORKFLOW_PLANNING,
    TargetStage.FEATURE_ENGINEERING,
    TargetStage.PREPROCESSING,
    TargetStage.MODEL_SEARCH,
    TargetStage.HPO,
    TargetStage.VALIDATION,
}
VALID_RECOMMENDATION_TYPES = {
    RecommendationType.EXPAND_FEATURES,
    RecommendationType.CHANGE_MODELS,
    RecommendationType.INCREASE_HPO,
    RecommendationType.ADJUST_VALIDATION,
    RecommendationType.CHANGE_METRIC,
}

# LLM often produces near-miss variations of canonical enum values.
# This mapping normalises common LLM variants to the canonical diagnosis_type.
DIAGNOSIS_TYPE_ALIASES: dict[str, str] = {
    "baseline_improvement": DiagnosisType.WEAK_BASELINE_IMPROVEMENT,
    "weak_baseline": DiagnosisType.WEAK_BASELINE_IMPROVEMENT,
    "no_baseline_improvement": DiagnosisType.WEAK_BASELINE_IMPROVEMENT,
    "overfitting": DiagnosisType.OVERFITTING_RISK,
    "overfit": DiagnosisType.OVERFITTING_RISK,
    "underfit": DiagnosisType.UNDERFITTING,
    "feature_insufficient": DiagnosisType.FEATURE_INSUFFICIENCY,
    "insufficient_features": DiagnosisType.FEATURE_INSUFFICIENCY,
    "feature_noisy": DiagnosisType.FEATURE_NOISE,
    "noisy_features": DiagnosisType.FEATURE_NOISE,
    "model_unsuitable": DiagnosisType.MODEL_MISMATCH,
    "model_not_suitable": DiagnosisType.MODEL_MISMATCH,
    "hpo_limited": DiagnosisType.HPO_INSUFFICIENT,
    "insufficient_hpo": DiagnosisType.HPO_INSUFFICIENT,
    "hpo_insufficiency": DiagnosisType.HPO_INSUFFICIENT,
    "validation_unstable": DiagnosisType.VALIDATION_INSTABILITY,
    "unstable_validation": DiagnosisType.VALIDATION_INSTABILITY,
    "data_quality": DiagnosisType.DATA_QUALITY_LIMITATION,
    "poor_data_quality": DiagnosisType.DATA_QUALITY_LIMITATION,
    "small_dataset": DiagnosisType.DATA_QUALITY_LIMITATION,
    "metric_unsuitable": DiagnosisType.METRIC_MISMATCH,
    "metric_mismatched": DiagnosisType.METRIC_MISMATCH,
    "pipeline_limited": DiagnosisType.LIMITED_PIPELINE_GAIN,
    "limited_gain": DiagnosisType.LIMITED_PIPELINE_GAIN,
    "high_variance": DiagnosisType.VALIDATION_INSTABILITY,
    "fold_variance": DiagnosisType.VALIDATION_INSTABILITY,
}


def canonical_diagnosis_type(raw: str) -> str:
    """Return the canonical diagnosis_type for *raw*, or *raw* unchanged if unknown."""
    if raw in VALID_DIAGNOSIS_TYPES:
        return raw
    return DIAGNOSIS_TYPE_ALIASES.get(raw, raw)
