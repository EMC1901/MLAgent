import os
import json
from datetime import datetime
from typing import Dict, Any
from app.modules.metric_evaluation.exceptions import EvaluationArtifactSaveException

EVALUATION_ARTIFACT_ROOT = "/app/artifacts/evaluation"


def _make_serializable(obj: Any) -> Any:
    import numpy as np
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        val = float(obj)
        return None if np.isnan(val) else val
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_serializable(v) for v in obj]
    return obj


def ensure_evaluation_dir(metric_evaluation_id: str) -> str:
    eval_dir = os.path.join(EVALUATION_ARTIFACT_ROOT, metric_evaluation_id)
    subdirs = ["", "metrics", "ranking", "diagnosis"]
    for sub in subdirs:
        path = os.path.join(eval_dir, sub) if sub else eval_dir
        os.makedirs(path, exist_ok=True)
    return eval_dir


def _save_json(eval_dir: str, filename: str, data: Any) -> str:
    try:
        filepath = os.path.join(eval_dir, filename)
        serialized = _make_serializable(data)
        with open(filepath, "w") as f:
            json.dump(serialized, f, indent=2, default=str)
        return filepath
    except Exception as e:
        raise EvaluationArtifactSaveException(
            f"Failed to save {filename}: {str(e)}"
        )


def save_metric_results(eval_dir: str, data: Any) -> str:
    return _save_json(eval_dir, "metric_results.json", data)


def save_fold_metrics(eval_dir: str, data: Any) -> str:
    return _save_json(eval_dir, "fold_metrics.json", data)


def save_trial_metrics(eval_dir: str, data: Any) -> str:
    return _save_json(eval_dir, "trial_metrics.json", data)


def save_pipeline_metrics(eval_dir: str, data: Any) -> str:
    return _save_json(eval_dir, "pipeline_metrics.json", data)


def save_model_ranking(eval_dir: str, data: Any) -> str:
    return _save_json(eval_dir, "model_ranking.json", data)


def save_baseline_comparison(eval_dir: str, data: Any) -> str:
    return _save_json(eval_dir, "baseline_comparison.json", data)


def save_result_diagnosis_input(eval_dir: str, data: Any) -> str:
    return _save_json(eval_dir, "result_diagnosis_input.json", data)


def save_manifest(eval_dir: str, data: Dict[str, Any]) -> str:
    return _save_json(eval_dir, "manifest.json", data)
