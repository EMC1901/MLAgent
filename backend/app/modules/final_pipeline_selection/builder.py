import logging
from typing import List, Optional

from app.modules.final_pipeline_selection.model import FinalPipelineSelection
from app.modules.final_pipeline_selection.schemas import (
    FinalPipelineSelectionResponse,
    CandidateSelectionItem,
    FinalSelectedPipeline,
    SelectionPolicy,
    SystemSelectionReason,
    LLMSelectionExplanation,
    FinalArtifactManifest,
    InterpretabilityAnalysisInput,
    ConstraintCheckResult,
    StabilitySummary,
    BaselineComparison,
    CandidateDifferenceSummary,
)

logger = logging.getLogger(__name__)


def build_response(
    record: FinalPipelineSelection,
    final_pipeline: Optional[FinalSelectedPipeline] = None,
    candidate_ranking: Optional[List[CandidateSelectionItem]] = None,
    selection_policy: Optional[SelectionPolicy] = None,
    constraint_check_result: Optional[ConstraintCheckResult] = None,
    system_selection_reason: Optional[SystemSelectionReason] = None,
    llm_selection_explanation: Optional[LLMSelectionExplanation] = None,
    candidate_difference_summary: Optional[List[CandidateDifferenceSummary]] = None,
    human_review_notes: Optional[List[str]] = None,
    risk_notes: Optional[List[str]] = None,
    final_artifact_manifest: Optional[FinalArtifactManifest] = None,
    interpretability_analysis_input: Optional[InterpretabilityAnalysisInput] = None,
    warnings: Optional[List[str]] = None,
    stability_summary: Optional[StabilitySummary] = None,
    baseline_comparison: Optional[BaselineComparison] = None,
    metric_direction: Optional[str] = None,
    secondary_metrics: Optional[dict] = None,
) -> FinalPipelineSelectionResponse:
    response = FinalPipelineSelectionResponse(
        final_pipeline_selection_id=record.id,
        task_id=record.task_id,
        workflow_refinement_id=record.workflow_refinement_id,
        metric_evaluation_id=record.metric_evaluation_id,
        pipeline_execution_id=record.pipeline_execution_id,
        pipeline_generation_id=record.pipeline_generation_id,
        status=record.status or "selecting",
        selection_profile=record.selection_profile or "balanced",
        primary_metric=record.primary_metric,
        primary_metric_value=record.primary_metric_value,
        metric_direction=metric_direction,
        secondary_metrics=secondary_metrics or {},
        selection_score=record.selection_score,
        llm_used=bool(record.llm_used),
        llm_confidence_level=record.llm_confidence_level,
        ready_for_interpretability_analysis=bool(record.ready_for_interpretability_analysis),
        warnings=warnings or [],
        error_message=record.error_message,
        created_at=record.created_at,
        updated_at=record.updated_at,
        stability_summary=stability_summary,
        baseline_comparison=baseline_comparison,
    )

    if final_pipeline:
        response.final_pipeline_spec_id = final_pipeline.final_pipeline_spec_id
        response.final_model_id = final_pipeline.final_model_id
        response.final_model_family = final_pipeline.final_model_family
        response.final_trial_id = final_pipeline.final_trial_id
        response.final_trial_type = final_pipeline.final_trial_type
        response.final_hyperparameters = final_pipeline.final_hyperparameters

    if candidate_ranking:
        response.candidate_ranking = candidate_ranking

    if constraint_check_result:
        response.constraint_check_result = constraint_check_result

    if system_selection_reason:
        response.system_selection_reason = system_selection_reason

    if llm_selection_explanation:
        response.llm_selection_explanation = llm_selection_explanation

    if candidate_difference_summary:
        response.candidate_difference_summary = candidate_difference_summary

    if human_review_notes:
        response.human_review_notes = human_review_notes

    if risk_notes:
        response.risk_notes = risk_notes

    if final_artifact_manifest:
        response.final_artifact_manifest = final_artifact_manifest

    if interpretability_analysis_input:
        response.interpretability_analysis_input = interpretability_analysis_input

    return response
