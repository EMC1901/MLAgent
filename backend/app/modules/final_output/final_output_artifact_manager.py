import os
import json
import logging
from typing import Dict, Any, Optional

from app.modules.final_output.schemas import (
    FinalOutputResponse,
    OutputPackageManifest,
    FinalArtifactManifest,
)
from app.modules.final_output.exceptions import FinalOutputArtifactSaveException

logger = logging.getLogger(__name__)

ARTIFACT_BASE_DIR = "/app/artifacts/final_output"


def save_final_output_artifacts(
    final_output_id: str,
    final_output_result: Dict[str, Any],
    final_report: Dict[str, Any],
    llm_report: Optional[Dict[str, Any]],
    workflow_trace: Dict[str, Any],
    reproducibility_summary: Dict[str, Any],
    artifact_manifest: Dict[str, Any],
    output_package_manifest: Dict[str, Any],
) -> str:
    artifact_dir = os.path.join(ARTIFACT_BASE_DIR, final_output_id)

    try:
        os.makedirs(artifact_dir, exist_ok=True)

        if llm_report:
            _save_json(os.path.join(artifact_dir, "llm_report.json"), llm_report)

        logger.info("Saved final output artifacts to %s", artifact_dir)
        return artifact_dir

    except Exception as e:
        logger.error("Failed to save final output artifacts: %s", str(e))
        raise FinalOutputArtifactSaveException(str(e))


def _save_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
