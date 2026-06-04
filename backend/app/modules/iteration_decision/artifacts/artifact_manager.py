import json
import os
import logging
from typing import Dict, Any
from app.modules.iteration_decision.schemas import ArtifactManifest
from app.modules.iteration_decision.exceptions import ArtifactSaveFailedException

logger = logging.getLogger(__name__)
DEFAULT_ARTIFACT_BASE = "/app/artifacts/iteration_decision"


def save_decision_artifacts(
    iteration_decision_id: str,
    decision_result: Dict[str, Any],
    context: Dict[str, Any] = None,
    evidence: Dict[str, Any] = None,
    system_checks: Dict[str, Any] = None,
    llm_request: Dict[str, Any] = None,
    llm_response: Dict[str, Any] = None,
    iteration_plan: Dict[str, Any] = None,
    revised_workflow_plan: Dict[str, Any] = None,
    stop_output: Dict[str, Any] = None,
    artifact_base: str = DEFAULT_ARTIFACT_BASE,
) -> ArtifactManifest:
    artifact_dir = os.path.join(artifact_base, iteration_decision_id)
    try:
        os.makedirs(artifact_dir, exist_ok=True)
    except OSError as e:
        raise ArtifactSaveFailedException(f"Failed to create artifact directory: {str(e)}")

    manifest = ArtifactManifest()
    manifest.manifest_path = _write_json(artifact_dir, "manifest.json", {"iteration_decision_id": iteration_decision_id})

    if decision_result:
        manifest.decision_result_path = _write_json(artifact_dir, "decision_result.json", decision_result)
    if context:
        manifest.context_path = _write_json(artifact_dir, "context.json", context)
    if evidence:
        manifest.evidence_path = _write_json(artifact_dir, "evidence.json", evidence)
    if system_checks:
        manifest.system_checks_path = _write_json(artifact_dir, "system_checks.json", system_checks)
    if llm_request:
        manifest.llm_request_path = _write_json(artifact_dir, "llm_request.json", llm_request)
    if llm_response:
        manifest.llm_response_path = _write_json(artifact_dir, "llm_response.json", llm_response)
    if iteration_plan:
        manifest.iteration_plan_path = _write_json(artifact_dir, "iteration_plan.json", iteration_plan)
    if revised_workflow_plan:
        manifest.revised_workflow_plan_path = _write_json(artifact_dir, "revised_workflow_plan.json", revised_workflow_plan)
    if stop_output:
        manifest.stop_output_path = _write_json(artifact_dir, "stop_output.json", stop_output)

    saved_count = sum(1 for p in [
        manifest.decision_result_path, manifest.context_path, manifest.evidence_path,
        manifest.system_checks_path, manifest.llm_request_path, manifest.llm_response_path,
        manifest.iteration_plan_path, manifest.revised_workflow_plan_path,
        manifest.stop_output_path,
    ] if p)
    logger.info("Artifacts saved — %d files → %s", saved_count, artifact_dir)

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
