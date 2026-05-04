import os
import logging
from app.modules.pipeline_generation.schemas import ArtifactManifest
from app.modules.pipeline_generation.exceptions import ArtifactResolveException

logger = logging.getLogger(__name__)

# Allowed artifact root directory names for path safety checks.
# Paths must reside under one of these directory trees.
ALLOWED_ARTIFACT_ROOTS = [
    "artifacts",
    "app",
    "data",
    "output",
    "tmp",
]


def resolve_artifacts(context: dict) -> ArtifactManifest:
    raw_model_ready_path = context.get("model_ready_matrix_path") or ""
    raw_preprocessor_path = context.get("preprocessor_artifact_path") or ""

    # Normalize mixed separators (e.g. /app/artifacts\fmp\...) upfront
    model_ready_path = os.path.normpath(raw_model_ready_path) if raw_model_ready_path else None
    preprocessor_path = os.path.normpath(raw_preprocessor_path) if raw_preprocessor_path else None

    manifest = ArtifactManifest(
        model_ready_matrix_path=model_ready_path,
        preprocessor_artifact_path=preprocessor_path,
        feature_columns=context.get("feature_columns", []),
        n_features=context.get("n_features", 0),
        target_column=context.get("target_column"),
    )

    errors = []

    if model_ready_path:
        if not _is_safe_path(model_ready_path):
            errors.append(f"Model ready path is not in an allowed directory: {model_ready_path}")
        elif not os.path.exists(model_ready_path):
            errors.append(f"Model ready artifact not found: {model_ready_path}")
        else:
            manifest.model_ready_exists = True
    else:
        errors.append("Model ready matrix path is missing.")

    if preprocessor_path:
        if not _is_safe_path(preprocessor_path):
            errors.append(f"Preprocessor path is not in an allowed directory: {preprocessor_path}")
        elif not os.path.exists(preprocessor_path):
            errors.append(f"Preprocessor artifact not found: {preprocessor_path}")
        else:
            manifest.preprocessor_exists = True
    else:
        manifest.preprocessor_artifact_path = None

    manifest.is_complete = manifest.model_ready_exists and bool(manifest.feature_columns)

    if errors:
        raise ArtifactResolveException("; ".join(errors))

    return manifest


def _is_safe_path(path: str) -> bool:
    """Return True if the path is safe: no parent-dir escapes AND
    contains a whitelisted artifact root component (or is relative)."""
    if not path:
        return False
    # Reject parent-dir escapes — check raw string BEFORE normpath resolves them
    if ".." in path:
        return False

    normalized = os.path.normpath(path)
    parts = normalized.replace("\\", "/").lstrip("/").split("/")

    # Relative paths are always safe (can't escape without "..", already checked)
    if not os.path.isabs(normalized):
        return True

    # Absolute paths: must contain a whitelisted root directory component.
    # Since ".." is blocked, a path under e.g. /app/artifacts/... can only
    # stay within that tree.
    for allowed_root in ALLOWED_ARTIFACT_ROOTS:
        if allowed_root in parts:
            return True

    return False
