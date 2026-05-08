class FinalOutputStatus:
    GENERATING = "generating"
    GENERATED = "generated"
    GENERATED_WITH_WARNING = "generated_with_warning"
    FAILED = "failed"


class ReportProfile:
    COMPACT = "compact"
    STANDARD = "standard"
    FULL = "full"


class OutputFormat:
    JSON = "json"
    MARKDOWN = "markdown"


class LLMConfidenceLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ArtifactIntegrityStatus:
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


VALID_STATUSES = {
    FinalOutputStatus.GENERATING,
    FinalOutputStatus.GENERATED,
    FinalOutputStatus.GENERATED_WITH_WARNING,
    FinalOutputStatus.FAILED,
}

VALID_PROFILES = {
    ReportProfile.COMPACT,
    ReportProfile.STANDARD,
    ReportProfile.FULL,
}

VALID_OUTPUT_FORMATS = {
    OutputFormat.JSON,
    OutputFormat.MARKDOWN,
}

VALID_CONFIDENCE_LEVELS = {
    LLMConfidenceLevel.LOW,
    LLMConfidenceLevel.MEDIUM,
    LLMConfidenceLevel.HIGH,
}

FORBIDDEN_PATTERNS = [
    "import ",
    "def ",
    "class ",
    "eval(",
    "exec(",
    "subprocess",
    "os.system",
    "open(",
    "write(",
    "delete ",
    "remove(",
    "shutil",
    "model.fit",
    "model.predict",
    "Pipeline(",
    "__import__",
    "compile(",
    "globals()",
    "locals()",
]

FORBIDDEN_LLM_FIELDS = [
    "python_code",
    "script",
    "shell_command",
    "sql",
    "modified_metric",
    "modified_model",
    "modified_artifact",
    "modified_shap_values",
    "causal_claim_without_evidence",
]
