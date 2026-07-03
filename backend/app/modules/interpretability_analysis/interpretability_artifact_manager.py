import os
import json
import logging
from typing import Dict, Any, List, Optional

from app.modules.interpretability_analysis.schemas import ArtifactManifest
from app.modules.interpretability_analysis.exceptions import InterpretabilityArtifactSaveException

logger = logging.getLogger(__name__)

ARTIFACT_BASE_DIR = "/app/artifacts/interpretability"


def save_interpretability_artifacts(
    interpretability_analysis_id: str,
    analysis_result: Dict[str, Any],
    global_feature_importance: Optional[Dict[str, Any]] = None,
    permutation_importance: Optional[Dict[str, Any]] = None,
    shap_summary: Optional[Dict[str, Any]] = None,
    shap_values_data: Optional[Dict[str, Any]] = None,
    local_explanations: Optional[Dict[str, Any]] = None,
    high_error_sample_analysis: Optional[Dict[str, Any]] = None,
    feature_group_summary: Optional[Dict[str, Any]] = None,
    material_insight_summary: Optional[Dict[str, Any]] = None,
    llm_interpretability_summary: Optional[Dict[str, Any]] = None,
    final_output_input: Optional[Dict[str, Any]] = None,
    cross_method_consensus: Optional[Dict[str, Any]] = None,
    partial_dependence: Optional[Dict[str, Any]] = None,
    residual_analysis: Optional[Dict[str, Any]] = None,
    correlation_analysis: Optional[Dict[str, Any]] = None,
    physics_constraints: Optional[Dict[str, Any]] = None,
    shap_interactions: Optional[List[Dict[str, Any]]] = None,
    shap_dependence: Optional[List[Dict[str, Any]]] = None,
    scientific_insight_report: Optional[Dict[str, Any]] = None,
    material_patterns: Optional[List[Dict[str, Any]]] = None,
    material_pattern_validation: Optional[Dict[str, Any]] = None,
    material_mechanisms: Optional[List[Dict[str, Any]]] = None,
    debug_trace: Optional[Dict[str, Any]] = None,
    debug_warnings: Optional[Dict[str, Any]] = None,
    request_snapshot: Optional[Dict[str, Any]] = None,
    input_snapshot: Optional[Dict[str, Any]] = None,
) -> ArtifactManifest:
    ia_dir = os.path.join(ARTIFACT_BASE_DIR, interpretability_analysis_id)
    shap_dir = os.path.join(ia_dir, "shap")
    os.makedirs(shap_dir, exist_ok=True)

    manifest = ArtifactManifest(manifest_path=os.path.join(ia_dir, "manifest.json"))

    try:
        manifest.interpretability_analysis_result_path = _write_json(
            ia_dir, "interpretability_analysis_result.json", analysis_result
        )
        if global_feature_importance:
            manifest.global_feature_importance_path = _write_json(
                ia_dir, "global_feature_importance.json", global_feature_importance
            )
        if permutation_importance:
            manifest.permutation_importance_path = _write_json(
                ia_dir, "permutation_importance.json", permutation_importance
            )
        if shap_summary:
            manifest.shap_summary_path = _write_json(
                shap_dir, "shap_summary.json", shap_summary
            )
        if shap_values_data:
            manifest.shap_values_path = _write_json(
                shap_dir, "shap_values_meta.json", shap_values_data
            )
        if local_explanations:
            manifest.local_explanations_path = _write_json(
                ia_dir, "local_explanations.json", local_explanations
            )
        if high_error_sample_analysis:
            manifest.high_error_sample_analysis_path = _write_json(
                ia_dir, "high_error_sample_analysis.json", high_error_sample_analysis
            )
        if feature_group_summary:
            manifest.feature_group_summary_path = _write_json(
                ia_dir, "feature_group_summary.json", feature_group_summary
            )
        if material_insight_summary:
            manifest.material_insight_summary_path = _write_json(
                ia_dir, "material_insight_summary.json", material_insight_summary
            )
        if llm_interpretability_summary:
            manifest.llm_interpretability_summary_path = _write_json(
                ia_dir, "llm_interpretability_summary.json", llm_interpretability_summary
            )
        if scientific_insight_report:
            manifest.scientific_insight_report_path = _write_json(
                ia_dir, "scientific_insight_report.json", scientific_insight_report
            )
        if material_patterns:
            manifest.material_patterns_path = _write_json(
                ia_dir, "material_patterns.json", material_patterns
            )
        if material_pattern_validation:
            manifest.material_pattern_validation_path = _write_json(
                ia_dir, "material_pattern_validation.json", material_pattern_validation
            )
        if material_mechanisms:
            manifest.material_mechanisms_path = _write_json(
                ia_dir, "material_mechanisms.json", material_mechanisms
            )
        if final_output_input:
            manifest.final_output_input_path = _write_json(
                ia_dir, "final_output_input.json", final_output_input
            )
        if cross_method_consensus:
            manifest.cross_method_consensus_path = _write_json(
                ia_dir, "cross_method_consensus.json", cross_method_consensus
            )
        if partial_dependence:
            manifest.partial_dependence_path = _write_json(
                ia_dir, "partial_dependence.json", partial_dependence
            )
        if residual_analysis:
            manifest.residual_analysis_path = _write_json(
                ia_dir, "residual_analysis.json", residual_analysis
            )
        if correlation_analysis:
            manifest.correlation_analysis_path = _write_json(
                ia_dir, "correlation_analysis.json", correlation_analysis
            )
        if physics_constraints:
            manifest.physics_constraint_check_path = _write_json(
                ia_dir, "physics_constraint_check.json", physics_constraints
            )
        if shap_interactions:
            manifest.shap_values_path = _write_json(
                shap_dir, "shap_interactions.json", shap_interactions
            )
        if shap_dependence:
            _write_json(
                shap_dir, "shap_dependence.json", shap_dependence
            )

        # ── Debug artifacts ──
        if debug_trace:
            _write_json(ia_dir, "debug_trace.json", debug_trace)
        if debug_warnings:
            _write_json(ia_dir, "warnings.json", debug_warnings)
        if request_snapshot:
            _write_json(ia_dir, "request_snapshot.json", request_snapshot)
        if input_snapshot:
            _write_json(ia_dir, "input_snapshot.json", input_snapshot)

        _write_json(ia_dir, "manifest.json", manifest.model_dump())

    except Exception as e:
        raise InterpretabilityArtifactSaveException(
            f"Failed to save interpretability artifacts: {str(e)}"
        )

    logger.info("Saved interpretability artifacts to %s", ia_dir)
    return manifest


def _write_json(dir_path: str, filename: str, data: Any) -> str:
    path = os.path.join(dir_path, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_safe_serialize(data), f, indent=2, default=str)
    return path


def _safe_serialize(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return _safe_serialize(obj.model_dump())
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_safe_serialize(item) for item in obj]
    return obj
