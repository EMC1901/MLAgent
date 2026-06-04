import os
import logging
from typing import List, Optional, Dict, Any
from sqlmodel import Session

from app.modules.final_output.schemas import FinalArtifactManifest
from app.modules.final_output.final_output_input_loader import FinalOutputInput
from app.modules.final_output.exceptions import FinalArtifactResolveException
from app.modules.final_output.enums import ArtifactIntegrityStatus

logger = logging.getLogger(__name__)

ALLOWED_BASE_DIR = "/app/artifacts"


def resolve_final_artifacts(
    session: Session,
    fo_input: FinalOutputInput,
) -> FinalArtifactManifest:
    manifest = FinalArtifactManifest(
        artifact_integrity_status=ArtifactIntegrityStatus.COMPLETE,
    )

    missing: List[str] = []
    warnings_list: List[str] = []

    # Validate model artifact
    manifest.model_artifact_path = _validate_path(
        fo_input.model_artifact_path, "model_artifact"
    )
    if not manifest.model_artifact_path:
        missing.append("model_artifact_path")

    # Validate prediction artifacts
    for path in fo_input.prediction_artifact_paths:
        validated = _validate_path(path, "prediction_artifact")
        if validated:
            manifest.prediction_artifact_paths.append(validated)
        else:
            warnings_list.append(f"Prediction artifact not found: {path}")

    # Validate interpretability artifacts
    ia_artifacts: Dict[str, str] = {}
    for key, path in fo_input.interpretability_artifacts.items():
        validated = _validate_path(path, f"interpretability_{key}")
        if validated:
            ia_artifacts[key] = validated
        else:
            warnings_list.append(f"Interpretability artifact '{key}' not found: {path}")
    manifest.interpretability_artifact_paths = ia_artifacts

    # Resolve additional artifact paths from upstream modules
    _resolve_upstream_artifacts(session, fo_input, manifest, warnings_list)

    # Determine integrity status
    if missing:
        manifest.artifact_integrity_status = ArtifactIntegrityStatus.PARTIAL
        manifest.missing_artifacts = missing
    if not manifest.model_artifact_path and not manifest.prediction_artifact_paths:
        manifest.artifact_integrity_status = ArtifactIntegrityStatus.FAILED

    manifest.warnings = warnings_list

    logger.info(
        "Artifact resolution complete: status=%s model=%s predictions=%d",
        manifest.artifact_integrity_status,
        bool(manifest.model_artifact_path),
        len(manifest.prediction_artifact_paths),
    )
    return manifest


def _validate_path(path: Optional[str], label: str = "artifact") -> Optional[str]:
    if not path:
        return None
    normalized = os.path.normpath(path)
    if ".." in normalized:
        logger.warning("Rejected path with '..' for %s: %s", label, path)
        return None
    if os.path.exists(normalized):
        return normalized
    logger.warning("%s path does not exist: %s", label, path)
    return normalized


def _resolve_upstream_artifacts(
    session: Session,
    fo_input: FinalOutputInput,
    manifest: FinalArtifactManifest,
    warnings_list: List[str],
):
    # Upstream artifact resolution: FPS module has been removed.
    # Pipeline execution artifacts are no longer resolved through this path.
    pass
