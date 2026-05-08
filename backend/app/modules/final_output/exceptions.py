from app.shared.common.exceptions import BusinessException


class FinalOutputNotFoundException(BusinessException):
    def __init__(self, message: str = "Final output not found."):
        super().__init__(message, "FINAL_OUTPUT_NOT_FOUND")


class InterpretabilityAnalysisRequiredException(BusinessException):
    def __init__(self, message: str = "Interpretability analysis is required before final output."):
        super().__init__(message, "INTERPRETABILITY_ANALYSIS_REQUIRED")


class InterpretabilityAnalysisNotReadyException(BusinessException):
    def __init__(self, message: str = "Interpretability analysis is not ready for final output."):
        super().__init__(message, "INTERPRETABILITY_ANALYSIS_NOT_READY_FOR_FINAL_OUTPUT")


class FinalOutputInputInvalidException(BusinessException):
    def __init__(self, message: str = "Final output input is invalid."):
        super().__init__(message, "FINAL_OUTPUT_INPUT_INVALID")


class WorkflowTraceCollectException(BusinessException):
    def __init__(self, message: str = "Failed to collect workflow trace."):
        super().__init__(message, "WORKFLOW_TRACE_COLLECT_FAILED")


class FinalArtifactResolveException(BusinessException):
    def __init__(self, message: str = "Failed to resolve final artifacts."):
        super().__init__(message, "FINAL_ARTIFACT_RESOLVE_FAILED")


class ReproducibilitySummaryBuildException(BusinessException):
    def __init__(self, message: str = "Failed to build reproducibility summary."):
        super().__init__(message, "REPRODUCIBILITY_SUMMARY_BUILD_FAILED")


class LLMReportWriterException(BusinessException):
    def __init__(self, message: str = "LLM report writer failed."):
        super().__init__(message, "LLM_REPORT_WRITER_FAILED")


class LLMReportValidationException(BusinessException):
    def __init__(self, message: str = "LLM report validation failed."):
        super().__init__(message, "LLM_REPORT_VALIDATION_FAILED")


class ReportRenderException(BusinessException):
    def __init__(self, message: str = "Failed to render final report."):
        super().__init__(message, "FINAL_REPORT_RENDER_FAILED")


class OutputPackageBuildException(BusinessException):
    def __init__(self, message: str = "Failed to build output package."):
        super().__init__(message, "OUTPUT_PACKAGE_BUILD_FAILED")


class FinalOutputArtifactSaveException(BusinessException):
    def __init__(self, message: str = "Failed to save final output artifacts."):
        super().__init__(message, "FINAL_OUTPUT_ARTIFACT_SAVE_FAILED")
