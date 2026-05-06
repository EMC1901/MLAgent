import json
import os
import logging
from typing import Dict, Any
from app.modules.workflow_refinement.exceptions import WorkflowRefinementArtifactSaveException

logger = logging.getLogger(__name__)

ARTIFACT_BASE_DIR = "/app/artifacts/workflow_refinement"


def save_refinement_artifacts(
    workflow_refinement_id: str,
    refinement_result: Dict[str, Any],
    llm_context: Dict[str, Any],
    llm_request: Dict[str, Any],
    llm_response: Dict[str, Any],
    revised_workflow_plan: Dict[str, Any],
    workflow_plan_delta: Dict[str, Any],
    iteration_rerun_plan: Dict[str, Any],
    final_pipeline_selection_input: Dict[str, Any],
    validation_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Save all workflow refinement artifacts to disk."""
    artifact_dir = os.path.join(ARTIFACT_BASE_DIR, workflow_refinement_id)

    try:
        os.makedirs(artifact_dir, exist_ok=True)

        files = {
            "workflow_refinement_result.json": refinement_result,
            "llm_refinement_context.json": llm_context,
            "llm_request.json": llm_request,
            "llm_response.json": llm_response,
            "revised_workflow_plan.json": revised_workflow_plan,
            "workflow_plan_delta.json": workflow_plan_delta,
            "iteration_rerun_plan.json": iteration_rerun_plan,
            "final_pipeline_selection_input.json": final_pipeline_selection_input,
            "validation_result.json": validation_result,
        }

        manifest: Dict[str, str] = {}
        for filename, data in files.items():
            filepath = os.path.join(artifact_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, default=str, indent=2)
            manifest[filename.replace(".json", "")] = filepath

        manifest_path = os.path.join(artifact_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        logger.info("Saved workflow refinement artifacts to %s", artifact_dir)

        return {
            "manifest_path": manifest_path,
            "workflow_refinement_result_path": manifest.get("workflow_refinement_result"),
            "llm_refinement_context_path": manifest.get("llm_refinement_context"),
            "llm_request_path": manifest.get("llm_request"),
            "llm_response_path": manifest.get("llm_response"),
            "revised_workflow_plan_path": manifest.get("revised_workflow_plan"),
            "workflow_plan_delta_path": manifest.get("workflow_plan_delta"),
            "iteration_rerun_plan_path": manifest.get("iteration_rerun_plan"),
            "final_pipeline_selection_input_path": manifest.get("final_pipeline_selection_input"),
            "validation_result_path": manifest.get("validation_result"),
        }

    except Exception as e:
        logger.error("Failed to save workflow refinement artifacts: %s", str(e))
        raise WorkflowRefinementArtifactSaveException(
            f"Failed to save artifacts for '{workflow_refinement_id}': {str(e)}"
        )
