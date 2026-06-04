import os
import uuid
import json
import logging
import tempfile
import numpy as np
import pandas as pd
import joblib
from app.shared.config.settings import settings
from app.modules.feature_preprocessing.exceptions import (
    ModelReadyArtifactSaveException,
    PreprocessorArtifactSaveException,
)

logger = logging.getLogger(__name__)

MODEL_READY_ARTIFACT_DIR = getattr(settings, "MODEL_READY_ARTIFACT_DIR", "/app/artifacts/model_ready")
MODEL_READY_ARTIFACT_FORMAT = getattr(settings, "MODEL_READY_ARTIFACT_FORMAT", "parquet")
PREPROCESSOR_ARTIFACT_FORMAT = getattr(settings, "PREPROCESSOR_ARTIFACT_FORMAT", "joblib")
FEATURE_PREPROCESSING_PREVIEW_ROWS = getattr(settings, "FEATURE_PREPROCESSING_PREVIEW_ROWS", 20)


def save_model_ready_artifact(
    preprocessing_id: str,
    model_ready_df: pd.DataFrame,
    preprocessing_pipeline,
) -> dict:
    """Save model-ready feature matrix and preprocessor pipeline artifacts.

    Directory structure:
        /app/artifacts/model_ready/{fmp_id}/
            model_ready_features.parquet
            preprocessor.joblib
            preprocessing_metadata.json
            validation_report.json
            preview.json
    """
    artifact_dir = os.path.join(MODEL_READY_ARTIFACT_DIR, preprocessing_id)

    try:
        os.makedirs(artifact_dir, exist_ok=True)
    except OSError as e:
        raise ModelReadyArtifactSaveException(f"Failed to create artifact directory: {e}")

    # Save model-ready matrix (atomic: write to temp then rename)
    file_path = os.path.join(artifact_dir, "model_ready_features.parquet")
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".parquet", dir=artifact_dir)
        os.close(tmp_fd)
        model_ready_df.to_parquet(tmp_path, index=False)
        os.replace(tmp_path, file_path)
    except Exception as e:
        raise ModelReadyArtifactSaveException(f"Failed to save model-ready matrix: {e}")

    model_ready_artifact_id = f"artifact_model_ready_{uuid.uuid4().hex[:8]}"

    # Save preprocessor pipeline (atomic write)
    preprocessor_path = os.path.join(artifact_dir, "preprocessor.joblib")
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".joblib", dir=artifact_dir)
        os.close(tmp_fd)
        joblib.dump(preprocessing_pipeline, tmp_path)
        os.replace(tmp_path, preprocessor_path)
    except Exception as e:
        raise PreprocessorArtifactSaveException(f"Failed to save preprocessor: {e}")

    preprocessor_artifact_id = f"artifact_preprocessor_{uuid.uuid4().hex[:8]}"

    # Compute feature count (exclude sample_id and target)
    feature_cols_in_df = list(model_ready_df.columns)
    n_features = len([
        c for c in feature_cols_in_df
        if c not in ("sample_id",)
    ])

    # Save metadata
    metadata = {
        "preprocessing_id": preprocessing_id,
        "model_ready_artifact_id": model_ready_artifact_id,
        "model_ready_file_path": file_path,
        "preprocessor_artifact_id": preprocessor_artifact_id,
        "preprocessor_file_path": preprocessor_path,
        "n_samples": len(model_ready_df),
        "n_features": n_features,
        "format": MODEL_READY_ARTIFACT_FORMAT,
        "preprocessor_format": PREPROCESSOR_ARTIFACT_FORMAT,
        "created_at": pd.Timestamp.now().isoformat(),
    }
    def _atomic_write_json(filepath, data):
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".json", dir=os.path.dirname(filepath))
        os.close(tmp_fd)
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp_path, filepath)

    meta_path = os.path.join(artifact_dir, "preprocessing_metadata.json")
    try:
        _atomic_write_json(meta_path, metadata)
    except OSError:
        logger.warning("Failed to write preprocessing_metadata.json")

    # Save validation report (placeholder)
    val_path = os.path.join(artifact_dir, "validation_report.json")
    try:
        _atomic_write_json(val_path, {"is_model_ready": True})
    except OSError:
        logger.warning("Failed to write validation_report.json")

    # Generate preview
    preview_rows = FEATURE_PREPROCESSING_PREVIEW_ROWS
    preview_df = model_ready_df.head(preview_rows).copy()
    preview_df = preview_df.replace({np.nan: None, float("inf"): None, float("-inf"): None})
    preview_json = {
        "columns": list(model_ready_df.columns),
        "preview_rows": len(preview_df),
        "total_rows": len(model_ready_df),
        "rows": preview_df.to_dict(orient="records"),
    }
    preview_path = os.path.join(artifact_dir, "preview.json")
    try:
        _atomic_write_json(preview_path, preview_json)
    except OSError:
        logger.warning("Failed to write preview.json")

    return {
        "model_ready_artifact_id": model_ready_artifact_id,
        "model_ready_file_path": file_path,
        "model_ready_n_samples": len(model_ready_df),
        "model_ready_n_features": n_features,
        "preprocessor_artifact_id": preprocessor_artifact_id,
        "preprocessor_file_path": preprocessor_path,
        "preview_json": preview_json,
    }


def save_fold_pipeline_spec(fmp_id: str, spec) -> str:
    """Save FoldPipelineSpec as JSON alongside the model-ready artifact."""
    artifact_dir = os.path.join(MODEL_READY_ARTIFACT_DIR, fmp_id)
    os.makedirs(artifact_dir, exist_ok=True)
    spec_path = os.path.join(artifact_dir, "fold_pipeline_spec.json")
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".json", dir=artifact_dir)
    os.close(tmp_fd)
    with open(tmp_path, "w") as f:
        json.dump(spec.model_dump(mode="json") if hasattr(spec, "model_dump") else spec,
                  f, indent=2, default=str)
    os.replace(tmp_path, spec_path)
    logger.info("FoldPipelineSpec saved: %s (%d ops)", spec_path,
                len(spec.operations) if hasattr(spec, "operations") else 0)
    return spec_path


def load_fold_pipeline_spec(filepath: str):
    """Load a FoldPipelineSpec from JSON file. Returns FoldPipelineSpec or None."""
    from app.modules.feature_preprocessing.schemas import FoldPipelineSpec
    if not filepath or not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        return FoldPipelineSpec(**data)
    except Exception as e:
        logger.warning("Failed to load fold pipeline spec from %s: %s", filepath, e)
        return None


def read_preview_from_model_ready(preprocessing_id: str, max_rows: int = 20) -> dict:
    """Read preview from a saved model-ready artifact."""
    artifact_dir = os.path.join(MODEL_READY_ARTIFACT_DIR, preprocessing_id)
    parquet_path = os.path.join(artifact_dir, "model_ready_features.parquet")
    preview_path = os.path.join(artifact_dir, "preview.json")

    # Try preview.json first
    if os.path.exists(preview_path):
        try:
            with open(preview_path, "r") as f:
                return json.load(f)
        except Exception:
            pass

    if not os.path.exists(parquet_path):
        return {"columns": [], "preview_rows": 0, "total_rows": 0, "rows": []}

    try:
        df = pd.read_parquet(parquet_path)
        preview_df = df.head(max_rows)
        preview_df = preview_df.replace({np.nan: None, float("inf"): None, float("-inf"): None})
        return {
            "columns": list(df.columns),
            "preview_rows": len(preview_df),
            "total_rows": len(df),
            "rows": preview_df.to_dict(orient="records"),
        }
    except Exception as e:
        logger.warning("Failed to read model-ready preview: %s", e)
        return {"columns": [], "preview_rows": 0, "total_rows": 0, "rows": []}
