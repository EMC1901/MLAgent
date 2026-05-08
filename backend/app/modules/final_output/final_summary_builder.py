import logging
from typing import List, Dict, Any, Optional

from app.modules.final_output.schemas import (
    FinalModelSummary,
    FinalMetricSummary,
    FinalSelectionSummary,
    InterpretabilitySummary,
)
from app.modules.final_output.final_output_input_loader import FinalOutputInput

logger = logging.getLogger(__name__)


class FinalOutputSummaries:
    def __init__(self):
        self.final_model_summary: Optional[FinalModelSummary] = None
        self.final_metric_summary: Optional[FinalMetricSummary] = None
        self.final_selection_summary: Optional[FinalSelectionSummary] = None
        self.interpretability_summary: Optional[InterpretabilitySummary] = None


def build_final_summaries(
    fo_input: FinalOutputInput,
    interpretability_analysis_id: str = "",
) -> FinalOutputSummaries:
    summaries = FinalOutputSummaries()

    # Build final model summary
    summaries.final_model_summary = _build_model_summary(fo_input)

    # Build final metric summary
    summaries.final_metric_summary = _build_metric_summary(fo_input)

    # Build final selection summary
    summaries.final_selection_summary = _build_selection_summary(fo_input)

    # Build interpretability summary
    summaries.interpretability_summary = _build_interpretability_summary(
        fo_input, interpretability_analysis_id
    )

    logger.info("Built final output system fact summaries")
    return summaries


def _build_model_summary(fo_input: FinalOutputInput) -> FinalModelSummary:
    return FinalModelSummary(
        final_model_id=fo_input.final_model_id,
        final_model_family=fo_input.final_model_id,
        final_trial_id=fo_input.final_trial_id,
        final_pipeline_spec_id="",
        final_hyperparameters=fo_input.selection_summary.get("hyperparameters", {}),
        model_artifact_path=fo_input.model_artifact_path,
        selection_reason_summary=fo_input.selection_summary.get(
            "selection_reason",
            "Selected for the best balance between metric performance, stability, interpretability, and cost.",
        ),
    )


def _build_metric_summary(fo_input: FinalOutputInput) -> FinalMetricSummary:
    metric_data = fo_input.metric_summary
    return FinalMetricSummary(
        primary_metric=metric_data.get("primary_metric", ""),
        primary_metric_value=metric_data.get("primary_metric_value"),
        metric_direction=metric_data.get("metric_direction", "minimize"),
        secondary_metrics=metric_data.get("secondary_metrics", {}),
        baseline_comparison=metric_data.get("baseline_comparison", {}),
        model_ranking_position=metric_data.get("model_ranking_position"),
        stability_summary=metric_data.get("stability_summary", {}),
    )


def _build_selection_summary(fo_input: FinalOutputInput) -> FinalSelectionSummary:
    sel_data = fo_input.selection_summary
    return FinalSelectionSummary(
        final_pipeline_selection_id=fo_input.final_pipeline_selection_id,
        selection_profile=sel_data.get("selection_profile", ""),
        selection_score=sel_data.get("selection_score"),
        system_selection_reason=sel_data.get("system_selection_reason", {}),
        llm_selection_explanation=sel_data.get("llm_selection_explanation", {}),
        candidate_difference_summary=sel_data.get("candidate_difference_summary", []),
        risk_notes=sel_data.get("risk_notes", []),
    )


def _build_interpretability_summary(
    fo_input: FinalOutputInput,
    interpretability_analysis_id: str,
) -> InterpretabilitySummary:
    top_features = []
    for fi in fo_input.global_feature_importance[:10]:
        top_features.append({
            "feature_name": fi.get("feature_name", ""),
            "importance_value": fi.get("importance_value", 0.0),
            "importance_rank": fi.get("importance_rank", 0),
            "importance_method": fi.get("importance_method", ""),
        })

    return InterpretabilitySummary(
        interpretability_analysis_id=interpretability_analysis_id,
        methods_used=fo_input.metric_summary.get("methods_used", []),
        top_features=top_features,
        shap_summary=fo_input.shap_summary,
        material_insight_summary=fo_input.material_insight_summary,
        interpretability_risk_notes=[],
        artifact_paths=fo_input.interpretability_artifacts,
    )


def build_summary_dicts(summaries: FinalOutputSummaries) -> Dict[str, Any]:
    return {
        "final_model_summary": summaries.final_model_summary.model_dump()
        if summaries.final_model_summary else {},
        "final_metric_summary": summaries.final_metric_summary.model_dump()
        if summaries.final_metric_summary else {},
        "final_selection_summary": summaries.final_selection_summary.model_dump()
        if summaries.final_selection_summary else {},
        "interpretability_summary": summaries.interpretability_summary.model_dump()
        if summaries.interpretability_summary else {},
    }
