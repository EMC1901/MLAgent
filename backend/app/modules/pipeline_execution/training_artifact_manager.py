"""Training Artifact Manager — saves models, metadata, manifest, and execution logs."""

import logging
import os
import json
import joblib
from datetime import datetime
from app.modules.pipeline_execution.exceptions import TrainingArtifactSaveException

logger = logging.getLogger(__name__)


class ExecutionLogHandler(logging.Handler):
    """Dual-purpose handler: writes log lines to a file AND collects structured
    event dicts in memory (for DB persistence and the /logs API)."""

    def __init__(self, log_file_path: str):
        super().__init__()
        self.log_file_path = log_file_path
        self.events: list = []
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        self._file = open(log_file_path, "a", encoding="utf-8")
        fmt = logging.Formatter(
            "%(asctime)s  %(levelname)-5s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.setFormatter(fmt)
        self.setLevel(logging.DEBUG)

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        try:
            self._file.write(msg + "\n")
            self._file.flush()
        except Exception:
            pass  # never let a file write break training
        self.events.append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        })

    def close(self) -> None:
        try:
            self._file.close()
        except Exception:
            pass
        super().close()

TRAINING_ARTIFACT_ROOT = "/app/artifacts/training"


def get_execution_log_path(exec_dir: str) -> str:
    return os.path.join(exec_dir, "logs", "execution.log")


def ensure_execution_dir(pipeline_execution_id: str) -> str:
    """Create and return the artifact directory for this execution."""
    exec_dir = os.path.join(TRAINING_ARTIFACT_ROOT, pipeline_execution_id)
    os.makedirs(exec_dir, exist_ok=True)
    for sub in ["predictions", "models", "logs", "splits"]:
        os.makedirs(os.path.join(exec_dir, sub), exist_ok=True)
    logger.info("artifact dir created: %s", exec_dir)
    return exec_dir


def save_model(model, trial_id: str, fold_index: int, exec_dir: str) -> str:
    """Save a trained model to disk. Returns the file path."""
    models_dir = os.path.join(exec_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    filename = f"{trial_id}_fold_{fold_index}.joblib"
    filepath = os.path.join(models_dir, filename)
    try:
        joblib.dump(model, filepath)
        logger.info("model saved: %s (%s)", filename, type(model).__name__)
    except Exception as e:
        raise TrainingArtifactSaveException(
            f"Failed to save model for {trial_id} fold {fold_index}: {e}"
        )
    return filepath


def save_manifest(exec_dir: str, manifest: dict) -> str:
    """Save execution manifest.json. Returns the file path."""
    filepath = os.path.join(exec_dir, "manifest.json")
    try:
        with open(filepath, "w") as f:
            json.dump(manifest, f, indent=2, default=str)
    except Exception as e:
        raise TrainingArtifactSaveException(f"Failed to save manifest: {e}")
    return filepath


def save_trial_results(exec_dir: str, trial_results: list) -> str:
    """Save trial_results.json. Returns the file path."""
    filepath = os.path.join(exec_dir, "trial_results.json")
    try:
        serializable = []
        for t in trial_results:
            d = t.copy() if isinstance(t, dict) else t.model_dump() if hasattr(t, "model_dump") else str(t)
            serializable.append(_make_serializable(d))
        with open(filepath, "w") as f:
            json.dump(serializable, f, indent=2, default=str)
    except Exception as e:
        raise TrainingArtifactSaveException(f"Failed to save trial results: {e}")
    return filepath


def save_split_metadata(exec_dir: str, splits: list) -> str:
    """Save split metadata. Returns the file path."""
    splits_dir = os.path.join(exec_dir, "splits")
    filepath = os.path.join(splits_dir, "split_metadata.json")
    try:
        metadata = []
        for s in splits:
            meta = {
                "fold_index": s.get("fold_index"),
                "train_size": s.get("train_size"),
                "validation_size": s.get("validation_size"),
            }
            metadata.append(meta)
        with open(filepath, "w") as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        raise TrainingArtifactSaveException(f"Failed to save split metadata: {e}")
    return filepath


def save_execution_result(exec_dir: str, result: dict) -> str:
    """Save execution_result.json. Returns the file path."""
    filepath = os.path.join(exec_dir, "execution_result.json")
    try:
        with open(filepath, "w") as f:
            json.dump(_make_serializable(result), f, indent=2, default=str)
    except Exception as e:
        raise TrainingArtifactSaveException(f"Failed to save execution result: {e}")
    return filepath


def save_metric_evaluation_input(exec_dir: str, metric_input: dict) -> str:
    """Save metric_evaluation_input.json. Returns the file path."""
    filepath = os.path.join(exec_dir, "metric_evaluation_input.json")
    try:
        with open(filepath, "w") as f:
            json.dump(_make_serializable(metric_input), f, indent=2, default=str)
    except Exception as e:
        raise TrainingArtifactSaveException(f"Failed to save metric evaluation input: {e}")
    return filepath


def _make_serializable(obj):
    """Recursively convert objects to JSON-serializable types."""
    import numpy as np
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_serializable(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj
