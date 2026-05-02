import os
import uuid
import json
import logging
import numpy as np
import pandas as pd
from app.shared.config.settings import settings
from app.modules.feature_engineering.exceptions import FeatureArtifactSaveException

logger = logging.getLogger(__name__)

FEATURE_ARTIFACT_DIR = getattr(settings, "FEATURE_ARTIFACT_DIR", "/app/artifacts/features")
FEATURE_ARTIFACT_FORMAT = getattr(settings, "FEATURE_ARTIFACT_FORMAT", "parquet")
FEATURE_PREVIEW_ROWS = getattr(settings, "FEATURE_PREVIEW_ROWS", 20)


def save_feature_artifact(feature_engineering_id: str, feature_matrix: pd.DataFrame) -> dict:
    artifact_id = f"artifact_features_{uuid.uuid4().hex[:8]}"
    artifact_dir = os.path.join(FEATURE_ARTIFACT_DIR, feature_engineering_id)

    try:
        os.makedirs(artifact_dir, exist_ok=True)
    except OSError as e:
        raise FeatureArtifactSaveException(f"Failed to create artifact directory: {e}")

    format_lower = FEATURE_ARTIFACT_FORMAT.lower()
    if format_lower == "parquet":
        try:
            import pyarrow  # noqa: F401
            file_path = os.path.join(artifact_dir, "features.parquet")
            feature_matrix.to_parquet(file_path, index=False)
        except ImportError:
            logger.warning("pyarrow not installed, falling back to CSV.")
            format_lower = "csv"

    if format_lower == "csv" or format_lower != "parquet":
        file_path = os.path.join(artifact_dir, "features.csv")
        feature_matrix.to_csv(file_path, index=False)

    try:
        n_samples, n_features_no_target = feature_matrix.shape
        target_col = None
        feature_cols = list(feature_matrix.columns)

        if "sample_id" in feature_cols:
            n_features_no_target -= 1
        if feature_cols and feature_cols[-1] not in ("sample_id",):
            target_col = feature_cols[-1]
            n_features_no_target -= 1

        n_features = max(0, n_features_no_target)
    except Exception:
        n_samples = len(feature_matrix)
        n_features = len(feature_matrix.columns)
        target_col = None

    metadata = {
        "artifact_id": artifact_id,
        "feature_engineering_id": feature_engineering_id,
        "file_path": file_path,
        "format": FEATURE_ARTIFACT_FORMAT,
        "n_samples": n_samples,
        "n_features": n_features,
        "target_column": target_col,
        "created_at": pd.Timestamp.now().isoformat(),
    }

    metadata_path = os.path.join(artifact_dir, "metadata.json")
    try:
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)
    except OSError:
        logger.warning("Failed to write artifact metadata.json")

    preview_rows = FEATURE_PREVIEW_ROWS
    preview_df = feature_matrix.head(preview_rows).copy()
    
    # Replace NaN/Inf with None for JSON/PostgreSQL JSONB compatibility
    # JSON standard does not support NaN or Infinity; PostgreSQL JSONB also rejects them
    preview_df = preview_df.replace({np.nan: None, float('inf'): None, float('-inf'): None})
    rows_data = preview_df.to_dict(orient="records")
    
    preview_json = {
        "columns": list(feature_matrix.columns),
        "preview_rows": len(preview_df),
        "total_rows": len(feature_matrix),
        "rows": rows_data,
    }

    return {
        "artifact_id": artifact_id,
        "storage_type": "local_file",
        "file_path": file_path,
        "n_samples": n_samples,
        "n_features": n_features,
        "preview_json": preview_json,
    }


def read_preview_from_artifact(feature_engineering_id: str, max_rows: int = 20) -> dict:
    artifact_dir = os.path.join(FEATURE_ARTIFACT_DIR, feature_engineering_id)

    parquet_path = os.path.join(artifact_dir, "features.parquet")
    csv_path = os.path.join(artifact_dir, "features.csv")

    file_path = None
    if os.path.exists(parquet_path):
        file_path = parquet_path
    elif os.path.exists(csv_path):
        file_path = csv_path
    else:
        return {"columns": [], "preview_rows": 0, "total_rows": 0, "rows": []}

    try:
        if file_path.endswith(".parquet"):
            df = pd.read_parquet(file_path)
        else:
            df = pd.read_csv(file_path)
    except Exception as e:
        logger.warning("Failed to read artifact for preview: %s", e)
        return {"columns": [], "preview_rows": 0, "total_rows": 0, "rows": []}

    preview_df = df.head(max_rows)
    return {
        "columns": list(df.columns),
        "preview_rows": len(preview_df),
        "total_rows": len(df),
        "rows": preview_df.to_dict(orient="records"),
    }
