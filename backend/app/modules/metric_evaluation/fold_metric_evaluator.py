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

            # Extract y_score for ROC-AUC (binary classification only)
            y_score = None
            if "y_pred_proba" in df.columns:
                y_score = df["y_pred_proba"].values
            else:
                proba_cols = sorted(
                    [c for c in df.columns if c.startswith("y_pred_proba_class_")],
                    key=lambda c: int(c.rsplit("_", 1)[-1]),
                )
                if len(proba_cols) == 2:
                    y_score = df["y_pred_proba_class_1"].values
                # > 2 columns → multi-class; y_score stays None
                # (ROC_AUC will return NaN with a warning)

            model_id = str(df["model_id"].iloc[0]) if "model_id" in df.columns else "unknown"
            pipeline_spec_id = (
                str(df["pipeline_spec_id"].iloc[0])
                if "pipeline_spec_id" in df.columns
                else "unknown"
            )

            # Ensure primary_metric is computed alongside defaults (canonicalised)
            canonical_primary = primary_metric.replace("-", "_") if primary_metric else None
            metrics_to_compute = list(default_metrics)
            if canonical_primary and canonical_primary not in metrics_to_compute:
                metrics_to_compute.append(canonical_primary)

            try:
                metrics = calculate_all_metrics(
                    y_true, y_pred, task_type, metrics_to_compute, y_score=y_score,
                )
            except Exception as e:
                metrics = {}
                warnings.append(f"Metric calculation failed: {str(e)}")
                status = "failed"
                error_message = str(e)

            # Look up primary_metric value.  Keys in *metrics* are canonical
            # ("ROC_AUC") but *primary_metric* may arrive with hyphens ("ROC-AUC").
            primary_value = None
            if primary_metric:
                primary_value = metrics.get(canonical_primary)
                if primary_value is None:
                    pm_normalised = primary_metric.replace("-", "_").lower()
                    for k, v in metrics.items():
                        if k.lower() == pm_normalised:
                            primary_value = v
                            break

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
