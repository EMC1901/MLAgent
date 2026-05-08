from app.shared.common.exceptions import BusinessException


class FinalPipelineSelectionNotFoundException(BusinessException):
    def __init__(self, message: str = "Final pipeline selection not found."):
        super().__init__(message, "FINAL_PIPELINE_SELECTION_NOT_FOUND")


class WorkflowRefinementRequiredException(BusinessException):
    def __init__(self, message: str = "Workflow refinement is required before final pipeline selection."):
        super().__init__(message, "WORKFLOW_REFINEMENT_REQUIRED")


class WorkflowRefinementNotReadyException(BusinessException):
    def __init__(self, message: str = "Workflow refinement is not ready for final pipeline selection."):
        super().__init__(message, "WORKFLOW_REFINEMENT_NOT_READY_FOR_FINAL_SELECTION")


class WorkflowRefinementDecisionInvalidException(BusinessException):
    def __init__(self, message: str = "Workflow refinement decision is not proceed_next_stage."):
        super().__init__(message, "WORKFLOW_REFINEMENT_DECISION_INVALID")


class FinalSelectionInputInvalidException(BusinessException):
    def __init__(self, message: str = "Final pipeline selection input is invalid."):
        super().__init__(message, "FINAL_SELECTION_INPUT_INVALID")


class CandidateCollectionException(BusinessException):
    def __init__(self, message: str = "Failed to collect candidates."):
        super().__init__(message, "FINAL_SELECTION_CANDIDATE_COLLECTION_FAILED")


class CandidateValidationException(BusinessException):
    def __init__(self, message: str = "Candidate validation failed."):
        super().__init__(message, "FINAL_SELECTION_CANDIDATE_VALIDATION_FAILED")


class SelectionPolicyException(BusinessException):
    def __init__(self, message: str = "Selection policy is invalid."):
        super().__init__(message, "FINAL_SELECTION_POLICY_INVALID")


class CandidateScoringException(BusinessException):
    def __init__(self, message: str = "Candidate scoring failed."):
        super().__init__(message, "FINAL_SELECTION_SCORING_FAILED")


class FinalRankingException(BusinessException):
    def __init__(self, message: str = "Final ranking failed."):
        super().__init__(message, "FINAL_SELECTION_RANKING_FAILED")


class FinalArtifactResolveException(BusinessException):
    def __init__(self, message: str = "Final artifact resolution failed."):
        super().__init__(message, "FINAL_SELECTION_ARTIFACT_RESOLVE_FAILED")


class LLMSelectionExplanationException(BusinessException):
    def __init__(self, message: str = "LLM selection explanation failed."):
        super().__init__(message, "LLM_SELECTION_EXPLANATION_FAILED")


class LLMSelectionExplanationValidationException(BusinessException):
    def __init__(self, message: str = "LLM selection explanation validation failed."):
        super().__init__(message, "LLM_SELECTION_EXPLANATION_VALIDATION_FAILED")


class InterpretabilityInputBuildException(BusinessException):
    def __init__(self, message: str = "Failed to build interpretability analysis input."):
        super().__init__(message, "INTERPRETABILITY_INPUT_BUILD_FAILED")


class FinalSelectionArtifactSaveException(BusinessException):
    def __init__(self, message: str = "Failed to save final selection artifacts."):
        super().__init__(message, "FINAL_SELECTION_ARTIFACT_SAVE_FAILED")
