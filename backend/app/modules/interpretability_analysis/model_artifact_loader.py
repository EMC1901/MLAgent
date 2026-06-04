import os
import logging
import joblib
from typing import Any

from app.modules.interpretability_analysis.exceptions import ModelArtifactLoadException

logger = logging.getLogger(__name__)


def load_model_artifact(model_artifact_path: str) -> Any:
    if not os.path.exists(model_artifact_path):
        raise ModelArtifactLoadException(f"Model artifact not found at: {model_artifact_path}")

    file_size_mb = os.path.getsize(model_artifact_path) / (1024 * 1024)
    logger.info("Loading model artifact (%.1f MB) from %s ...", file_size_mb, model_artifact_path)

    allowed_dir = os.path.normpath("/app/artifacts")
    normalized = os.path.normpath(model_artifact_path)
    if ".." in normalized or not normalized.startswith(allowed_dir):
        raise ModelArtifactLoadException(
            f"Model artifact path is outside allowed directory: {model_artifact_path}"
        )

    try:
        model = joblib.load(normalized)
    except Exception as e:
        raise ModelArtifactLoadException(f"Failed to load model artifact: {str(e)}")

    logger.info("Loaded model artifact (type=%s) from %s", type(model).__name__, model_artifact_path)
    return model
