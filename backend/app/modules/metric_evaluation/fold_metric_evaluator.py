import uuid
from typing import Dict, List, Any
import numpy as np
from app.modules.metric_evaluation.schemas import FoldMetricResult
from app.modules.metric_evaluation.metric_calculator import calculate_all_metrics
from app.modules.metric_evaluation.metric_registry import get_default_metrics


def evaluate_fold_metrics(
    trial_fold_map: Dict[str, Dict[int, Any]],
    task_type: str,
    primary_metric: str,
) -> List[FoldMetricResult]:
    results: List[FoldMetricResult] = []
    default_metrics = get_default_metrics(task_type)

    for trial_id, fold_dict in trial_fold_map.items():
        for fold_index, df in sorted(fold_dict.items()):
            fold_metric_id = f"fm_{uuid.uuid4().hex[:8]}"
            warnings: List[str] = []
            error_message = None
            status = "evaluated"

            y_true = df["y_true"].values
            y_pred = df["y_pred"].values

            model_id = str(df["model_id"].iloc[0]) if "model_id" in df.columns else "unknown"
            pipeline_spec_id = (
                str(df["pipeline_spec_id"].iloc[0])
                if "pipeline_spec_id" in df.columns
                else "unknown"
            )

            try:
                metrics = calculate_all_metrics(y_true, y_pred, task_type, default_metrics)
            except Exception as e:
                metrics = {}
                warnings.append(f"Metric calculation failed: {str(e)}")
                status = "failed"
                error_message = str(e)

            primary_value = metrics.get(primary_metric) if primary_metric else None

            results.append(FoldMetricResult(
                fold_metric_id=fold_metric_id,
                trial_id=trial_id,
                pipeline_spec_id=pipeline_spec_id,
                model_id=model_id,
                fold_index=fold_index,
                n_samples=len(df),
                metrics=metrics,
                primary_metric_value=primary_value,
                prediction_artifact_path=None,
                status=status,
                warnings=warnings,
                error_message=error_message,
            ))

    return results
