class InterpretabilityAnalysisStatus:
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    ANALYZED_WITH_WARNING = "analyzed_with_warning"
    FAILED = "failed"


class InterpretabilityMethodStatus:
    COMPUTED = "computed"
    SKIPPED = "skipped"
    FAILED = "failed"
    FALLBACK_USED = "fallback_used"


class AnalysisProfile:
    COMPACT = "compact"
    STANDARD = "standard"
    FULL = "full"


class ImportanceDirection:
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NON_MONOTONIC = "non_monotonic"
    UNKNOWN = "unknown"


class FeatureGroup:
    COMPOSITION_DESCRIPTOR = "composition_descriptor"
    STRUCTURE_DESCRIPTOR = "structure_descriptor"
    STATISTICAL_DESCRIPTOR = "statistical_descriptor"
    ELEMENTAL_DESCRIPTOR = "elemental_descriptor"
    DERIVED_FEATURE = "derived_feature"
    OTHER = "other"


class ImportanceMethod:
    COEFFICIENT = "coefficient"
    NATIVE = "native_importance"
    PERMUTATION = "permutation_importance"
    SHAP = "shap"


class LLMInterpretabilityConfidence:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EvidenceStrength:
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


VALID_STATUSES = {
    InterpretabilityAnalysisStatus.ANALYZING,
    InterpretabilityAnalysisStatus.ANALYZED,
    InterpretabilityAnalysisStatus.ANALYZED_WITH_WARNING,
    InterpretabilityAnalysisStatus.FAILED,
}

VALID_METHOD_STATUSES = {
    InterpretabilityMethodStatus.COMPUTED,
    InterpretabilityMethodStatus.SKIPPED,
    InterpretabilityMethodStatus.FAILED,
    InterpretabilityMethodStatus.FALLBACK_USED,
}

VALID_PROFILES = {
    AnalysisProfile.COMPACT,
    AnalysisProfile.STANDARD,
    AnalysisProfile.FULL,
}

VALID_CONFIDENCE_LEVELS = {
    LLMInterpretabilityConfidence.LOW,
    LLMInterpretabilityConfidence.MEDIUM,
    LLMInterpretabilityConfidence.HIGH,
}

# Literal substring patterns — already specific enough to avoid false positives
DANGEROUS_PATTERNS_LITERAL = [
    "eval(", "exec(", "subprocess", "os.system",
    "model.fit", "model.predict", "Pipeline(",
    "__import__", "compile(", "globals()", "locals()",
    "shutil.",
]

# Regex patterns for Python keywords that are also common English words.
# Use word-boundary + name-followed-by syntax to avoid matching natural language
# (e.g. "class of materials" should NOT flag, but "class MyModel:" should).
DANGEROUS_PATTERNS_REGEX = [
    (r'\bclass\s+[A-Za-z_]\w*', 'class <Name>'),    # class definition
    (r'\bdef\s+[A-Za-z_]\w*', 'def <Name>'),         # function definition
    (r'\bimport\s+[A-Za-z_]\w*', 'import <Module>'),  # import statement
    (r'\bopen\s*\(', 'open(...)'),                     # open() call
    (r'\bwrite\s*\(', 'write(...)'),                   # write() call
    (r'\bdelete\s+', 'delete <target>'),               # delete statement
    (r'\bremove\s+', 'remove <target>'),               # remove statement
]

FORBIDDEN_LLM_FIELDS = [
    "python_code", "script", "shell_command", "sql",
    "modified_importance", "modified_shap_values", "causal_claim",
    "model_update", "feature_update",
]


class EvidenceType:
    SHAP_IMPORTANCE = "shap_importance"
    PERMUTATION_IMPORTANCE = "permutation_importance"
    COEFFICIENT_IMPORTANCE = "coefficient_importance"
    NATIVE_IMPORTANCE = "native_importance"
    PDP_1D = "pdp_1d"
    CORRELATION_LINEAR = "correlation_linear"
    CORRELATION_RANK = "correlation_rank"
    RESIDUAL_SEGMENT = "residual_segment"
    PHYSICS_CONSTRAINT = "physics_constraint"
    ERROR_CONCENTRATION = "error_concentration"
    SHAP_INTERACTION = "shap_interaction"
    SHAP_DEPENDENCE = "shap_dependence"


class HypothesisClaimType:
    ASSOCIATION = "association"
    MECHANISM_HYPOTHESIS = "mechanism_hypothesis"
    LIMITATION = "limitation"
    ANOMALY = "anomaly"


class ConfidenceTier:
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


CONFIDENCE_TIER_THRESHOLDS = [
    (0.0, ConfidenceTier.VERY_LOW),
    (0.2, ConfidenceTier.LOW),
    (0.4, ConfidenceTier.MEDIUM),
    (0.6, ConfidenceTier.HIGH),
    (0.8, ConfidenceTier.VERY_HIGH),
]

VALID_CLAIM_TYPES = {
    HypothesisClaimType.ASSOCIATION,
    HypothesisClaimType.MECHANISM_HYPOTHESIS,
    HypothesisClaimType.LIMITATION,
    HypothesisClaimType.ANOMALY,
}

VALID_EVIDENCE_TYPES = {
    EvidenceType.SHAP_IMPORTANCE,
    EvidenceType.PERMUTATION_IMPORTANCE,
    EvidenceType.COEFFICIENT_IMPORTANCE,
    EvidenceType.NATIVE_IMPORTANCE,
    EvidenceType.PDP_1D,
    EvidenceType.CORRELATION_LINEAR,
    EvidenceType.CORRELATION_RANK,
    EvidenceType.RESIDUAL_SEGMENT,
    EvidenceType.PHYSICS_CONSTRAINT,
    EvidenceType.ERROR_CONCENTRATION,
    EvidenceType.SHAP_INTERACTION,
    EvidenceType.SHAP_DEPENDENCE,
}

VALID_CONFIDENCE_TIERS = {
    ConfidenceTier.VERY_LOW,
    ConfidenceTier.LOW,
    ConfidenceTier.MEDIUM,
    ConfidenceTier.HIGH,
    ConfidenceTier.VERY_HIGH,
}
