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

DANGEROUS_PATTERNS = [
    "import ", "def ", "class ", "eval(", "exec(", "subprocess", "os.system",
    "open(", "write(", "delete", "remove", "shutil", "model.fit", "model.predict",
    "Pipeline(", "__import__", "compile(", "globals()", "locals()",
]

FORBIDDEN_LLM_FIELDS = [
    "python_code", "script", "shell_command", "sql",
    "modified_importance", "modified_shap_values", "causal_claim",
    "model_update", "feature_update",
]
