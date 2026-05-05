import json
import os
import logging
from typing import Dict, Any
from app.modules.result_diagnosis.schemas import DiagnosisArtifactManifest
from app.modules.result_diagnosis.exceptions import DiagnosisArtifactSaveException

logger = logging.getLogger(__name__)

DEFAULT_ARTIFACT_BASE = "/app/artifacts/diagnosis"


def save_diagnosis_artifacts(
    result_diagnosis_id: str,
    diagnosis_result: Dict[str, Any],
    diagnostic_context: Dict[str, Any] = None,
    system_checks: Dict[str, Any] = None,
    llm_diagnosis: Dict[str, Any] = None,
    evidence_summary: Dict[str, Any] = None,
    refinement_input: Dict[str, Any] = None,
    artifact_base: str = DEFAULT_ARTIFACT_BASE,
) -> DiagnosisArtifactManifest:
    artifact_dir = os.path.join(artifact_base, result_diagnosis_id)
    try:
        os.makedirs(artifact_dir, exist_ok=True)
    except OSError as e:
        raise DiagnosisArtifactSaveException(f"Failed to create artifact directory: {str(e)}")

    manifest = DiagnosisArtifactManifest()
    manifest.manifest_path = _write_json(artifact_dir, "manifest.json", {"result_diagnosis_id": result_diagnosis_id})

    if diagnosis_result:
        manifest.diagnosis_result_path = _write_json(artifact_dir, "diagnosis_result.json", diagnosis_result)

    if diagnostic_context:
        manifest.diagnostic_context_path = _write_json(artifact_dir, "diagnostic_context.json", diagnostic_context)

    if system_checks:
        manifest.system_diagnostic_checks_path = _write_json(artifact_dir, "system_diagnostic_checks.json", system_checks)

    if llm_diagnosis:
        manifest.llm_diagnosis_path = _write_json(artifact_dir, "llm_diagnosis.json", llm_diagnosis)

    if evidence_summary:
        manifest.evidence_summary_path = _write_json(artifact_dir, "evidence_summary.json", evidence_summary)

    if refinement_input:
        manifest.closed_loop_refinement_input_path = _write_json(artifact_dir, "closed_loop_refinement_input.json", refinement_input)

    return manifest


def _write_json(directory: str, filename: str, data: Any) -> str:
    filepath = os.path.join(directory, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return filepath
    except Exception as e:
        logger.warning("Failed to write artifact %s: %s", filename, str(e))
        return ""
