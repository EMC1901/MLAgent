import logging
from typing import List, Optional, TYPE_CHECKING

from app.modules.interpretability_analysis.model import InterpretabilityAnalysis
from app.modules.interpretability_analysis.schemas import (
    InterpretabilityAnalysisResponse,
    DebugTrace,
    DebugWarning,
)

if TYPE_CHECKING:
    from app.modules.interpretability_analysis.debug_tracker import InterpretabilityDebugTracker

logger = logging.getLogger(__name__)


def _safe_extract_methods(methods_json) -> list:
    if isinstance(methods_json, dict):
        return methods_json.get("methods", [])
    return []


def _safe_extract_items(json_data) -> list:
    if isinstance(json_data, dict):
        return json_data.get("items", [])
    return []


def _safe_extract_debug_warnings(warnings_json) -> List[DebugWarning]:
    """Extract structured warnings from DB JSON."""
    if isinstance(warnings_json, dict):
        items = warnings_json.get("items", [])
        return [DebugWarning(**w) if isinstance(w, dict) else w for w in items]
    return []


def _safe_extract_debug_trace(debug_trace_json) -> Optional[DebugTrace]:
    """Extract debug trace from DB JSON."""
    if isinstance(debug_trace_json, dict):
        try:
            return DebugTrace(**debug_trace_json)
        except Exception:
            logger.debug("Failed to parse debug_trace_json", exc_info=True)
            return None
    return None


def build_response(
    record: InterpretabilityAnalysis,
    warnings: Optional[List[str]] = None,
    tracker: Optional["InterpretabilityDebugTracker"] = None,
    risk_notes: Optional[List[dict]] = None,
) -> InterpretabilityAnalysisResponse:
    # Prefer tracker over DB-stored debug data when available (latest state)
    if tracker is not None:
        debug_trace = tracker.to_debug_trace()
        debug_warnings = tracker.get_all_warnings()
        current_step = tracker.current_step
        last_completed_step = tracker.last_completed_step
    else:
        debug_trace = _safe_extract_debug_trace(record.debug_trace_json)
        debug_warnings = _safe_extract_debug_warnings(record.warnings_json)
        current_step = record.current_step
        last_completed_step = record.last_completed_step

    return InterpretabilityAnalysisResponse(
        interpretability_analysis_id=record.id,
        task_id=record.task_id,
        metric_evaluation_id=record.metric_evaluation_id,
        pipeline_execution_id=record.pipeline_execution_id,
        status=record.status or "analyzing",
        analysis_profile=record.analysis_profile or "standard",
        final_model_id=record.final_model_id,
        final_model_family=record.final_model_family,
        final_trial_id=record.final_trial_id,
        interpretability_methods_used=_safe_extract_methods(record.methods_used_json),
        global_feature_importance=_safe_extract_items(record.global_feature_importance_json),
        permutation_importance=_safe_extract_items(record.permutation_importance_json),
        shap_summary=record.shap_summary_json,
        local_explanations=_safe_extract_items(record.local_explanations_json),
        high_error_sample_analysis=_safe_extract_items(record.high_error_sample_analysis_json),
        feature_group_summary=record.feature_group_summary_json,
        material_insight_summary=record.material_insight_summary_json,
        llm_interpretability_summary=record.llm_summary_json,
        cross_method_consensus=record.cross_method_consensus_json,
        partial_dependence=record.partial_dependence_json,
        residual_analysis=record.residual_analysis_json,
        correlation_analysis=record.correlation_analysis_json,
        physics_constraint_check=record.physics_constraint_check_json,
        interpretability_risk_notes=risk_notes or [],
        analysis_artifact_manifest=record.artifact_manifest_json,
        scientific_insight_report=record.scientific_insight_report_json,
        final_output_input=record.final_output_input_json,
        ready_for_final_output=bool(record.ready_for_final_output),
        warnings=warnings or [],
        debug_warnings=debug_warnings,
        debug_trace=debug_trace,
        current_step=current_step,
        last_completed_step=last_completed_step,
        duration_seconds=record.duration_seconds,
        started_at=record.started_at,
        finished_at=record.finished_at,
        error_message=record.error_message,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
