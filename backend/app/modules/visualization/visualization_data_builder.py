import ast
import logging
import os
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from app.modules.interpretability_analysis.model import InterpretabilityAnalysis
from app.modules.metric_evaluation.model import MetricEvaluation
from app.modules.dataset_profile.model import DatasetProfile
from app.modules.pipeline_execution.model import PipelineExecution
from app.modules.feature_preprocessing.model import FeaturePreprocessing
from app.modules.visualization.schemas import (
    CorrelationMatrixData,
    TargetCorrelationItem,
    FeatureImportanceItem,
    DescriptorDistributionItem,
    PredictedVsActualData,
    ResidualPlotData,
    TrainTestComparisonData,
    CrossValidationBoxPlotData,
    ConfusionMatrixData,
    ROCCurveData,
    PRCurveData,
    FeatureAnalysisSection,
    ModelPerformanceSection,
    VisualizationDataResponse,
)

logger = logging.getLogger(__name__)

MAX_SCATTER_POINTS = 2000
MAX_FEATURES_HEATMAP = 30


def build_visualization_data(
    task_id: str,
    ia: Optional[InterpretabilityAnalysis],
    me: Optional[MetricEvaluation],
    dp: Optional[DatasetProfile],
    pe: Optional[PipelineExecution],
    fp: Optional[FeaturePreprocessing],
) -> VisualizationDataResponse:
    task_type = _resolve_task_type(me, pe)
    feature_analysis = _build_feature_analysis(ia, fp, dp)
    model_performance = _build_model_performance(ia, me, pe, task_type)

    return VisualizationDataResponse(
        task_id=task_id,
        task_type=task_type,
        feature_analysis=feature_analysis,
        model_performance=model_performance,
    )


# ---- Helpers ----

def _resolve_task_type(
    me: Optional[MetricEvaluation],
    pe: Optional[PipelineExecution],
) -> str:
    if me and me.task_type:
        return _normalize_task_type(me.task_type)
    if pe and pe.task_type:
        return _normalize_task_type(pe.task_type)
    return "regression"


def _normalize_task_type(raw: str) -> str:
    """Normalize task_type to canonical 'regression' or 'classification'."""
    lower = raw.strip().lower()
    if "classif" in lower:
        return "classification"
    if "regress" in lower:
        return "regression"
    return lower


def _safe_json(val: Any) -> dict:
    if val is None:
        return {}
    if isinstance(val, dict):
        return val
    if isinstance(val, list):
        return {}
    return {}


# ---- Feature Analysis ----

def _build_feature_analysis(
    ia: Optional[InterpretabilityAnalysis],
    fp: Optional[FeaturePreprocessing],
    dp: Optional[DatasetProfile],
) -> FeatureAnalysisSection:
    return FeatureAnalysisSection(
        correlation_matrix=_build_correlation_matrix(ia),
        target_correlations=_build_target_correlations(ia),
        feature_importance=_build_feature_importance(ia),
        descriptor_distribution=_build_descriptor_distribution(ia, fp),
    )


def _build_correlation_matrix(ia: Optional[InterpretabilityAnalysis]) -> Optional[CorrelationMatrixData]:
    if not ia or not ia.correlation_analysis_json:
        return None
    data = _safe_json(ia.correlation_analysis_json)
    matrix = data.get("feature_correlation_matrix", [])
    names = data.get("feature_names", [])
    if not matrix or not names:
        return None
    if len(names) > MAX_FEATURES_HEATMAP:
        names = names[:MAX_FEATURES_HEATMAP]
        matrix = [row[:MAX_FEATURES_HEATMAP] for row in matrix[:MAX_FEATURES_HEATMAP]]
    return CorrelationMatrixData(feature_names=names, matrix=matrix)


def _build_target_correlations(ia: Optional[InterpretabilityAnalysis]) -> List[TargetCorrelationItem]:
    if not ia or not ia.correlation_analysis_json:
        return []
    data = _safe_json(ia.correlation_analysis_json)
    items = data.get("target_correlations", [])
    result: List[TargetCorrelationItem] = []
    for item in items:
        if isinstance(item, dict):
            result.append(TargetCorrelationItem(
                feature_name=item.get("feature_name", ""),
                pearson_r=float(item.get("pearson_r", 0)),
                spearman_rho=float(item.get("spearman_rho", 0)),
            ))
    return result


def _build_feature_importance(ia: Optional[InterpretabilityAnalysis]) -> List[FeatureImportanceItem]:
    if not ia or not ia.global_feature_importance_json:
        return []
    raw = ia.global_feature_importance_json
    items: List[dict] = []
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = raw.get("items", raw.get("features", []))
    result: List[FeatureImportanceItem] = []
    for item in items:
        if isinstance(item, dict):
            result.append(FeatureImportanceItem(
                feature_name=item.get("feature_name", ""),
                importance_value=float(item.get("importance_value", 0)),
                importance_method=item.get("importance_method", ""),
                direction=item.get("direction", ""),
                feature_group=item.get("feature_group", ""),
            ))
    result.sort(key=lambda x: x.importance_value, reverse=True)
    return result


def _build_descriptor_distribution(
    ia: Optional[InterpretabilityAnalysis],
    fp: Optional[FeaturePreprocessing],
) -> List[DescriptorDistributionItem]:
    """Compute per-feature descriptive stats from the model-ready matrix."""
    if fp is None:
        logger.info("Descriptor distribution: FeaturePreprocessing record not available, using fallback.")
        return _fallback_descriptor_stats(ia)

    matrix_path = fp.model_ready_artifact_path
    feature_names = _get_feature_names_from_ia(ia)

    if not matrix_path:
        logger.info(
            "Descriptor distribution: model_ready_artifact_path is empty (fp.id=%s), using fallback.",
            fp.id,
        )
        return _fallback_descriptor_stats(ia)

    if not feature_names:
        logger.info("Descriptor distribution: no feature names from IA, using fallback.")
        return _fallback_descriptor_stats(ia)

    try:
        import os
        if not os.path.exists(matrix_path):
            logger.warning("Descriptor distribution: file not found at %s, using fallback.", matrix_path)
            return _fallback_descriptor_stats(ia)

        df = pd.read_parquet(matrix_path) if matrix_path.endswith(".parquet") else pd.read_csv(matrix_path)
        cols = [c for c in feature_names if c in df.columns]
        if not cols:
            logger.info(
                "Descriptor distribution: no feature columns matched in matrix (%d features, %d df cols), using fallback.",
                len(feature_names), len(df.columns),
            )
            return _fallback_descriptor_stats(ia)

        sub = df[cols]
        result: List[DescriptorDistributionItem] = []
        for col in cols:
            series = sub[col]
            if isinstance(series, pd.DataFrame):
                series = series.iloc[:, 0]
            series = series.dropna()
            if len(series) < 2:
                result.append(DescriptorDistributionItem(feature_name=col))
                continue
            try:
                result.append(DescriptorDistributionItem(
                    feature_name=col,
                    variance=float(series.var()),
                    skewness=float(series.skew()) if hasattr(series, "skew") else 0.0,
                    mean=float(series.mean()),
                    std=float(series.std()),
                    min_val=float(series.min()),
                    max_val=float(series.max()),
                ))
            except Exception:
                result.append(DescriptorDistributionItem(feature_name=col, mean=float(series.mean())))
        return result
    except Exception as e:
        logger.warning("Failed to compute descriptor stats from matrix: %s", str(e))
        return _fallback_descriptor_stats(ia)


def _get_feature_names_from_ia(ia: Optional[InterpretabilityAnalysis]) -> List[str]:
    if not ia:
        return []
    raw = ia.global_feature_importance_json
    if isinstance(raw, list):
        return [item.get("feature_name", "") for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        items = raw.get("items", raw.get("features", []))
        if isinstance(items, list):
            return [item.get("feature_name", "") for item in items if isinstance(item, dict)]
    corr = _safe_json(ia.correlation_analysis_json) if ia.correlation_analysis_json else {}
    names = corr.get("feature_names", [])
    if isinstance(names, list):
        return [str(n) for n in names]
    return []


def _fallback_descriptor_stats(ia: Optional[InterpretabilityAnalysis]) -> List[DescriptorDistributionItem]:
    """Use feature importance values as a minimal descriptor baseline."""
    fi = _build_feature_importance(ia)
    result: List[DescriptorDistributionItem] = []
    for item in fi[:MAX_FEATURES_HEATMAP]:
        result.append(DescriptorDistributionItem(
            feature_name=item.feature_name,
            mean=item.importance_value,
        ))
    return result


# ---- Model Performance ----

def _build_model_performance(
    ia: Optional[InterpretabilityAnalysis],
    me: Optional[MetricEvaluation],
    pe: Optional[PipelineExecution],
    task_type: str,
) -> ModelPerformanceSection:
    section = ModelPerformanceSection(
        model_id=(ia.final_model_id if ia else None) or (me.best_model_id if me else None),
        model_family=(ia.final_model_family if ia else None) or None,
        model_trial_id=(ia.final_trial_id if ia else None) or (me.best_trial_id if me else None),
        predicted_vs_actual=None,
        residual_plot=None,
        train_test_comparison=_build_train_test_comparison(me),
        cross_validation_box_plot=_build_cv_box_plot(me),
    )
    if task_type == "regression":
        section.predicted_vs_actual = _build_predicted_vs_actual(ia, me, pe)
        section.residual_plot = _build_residual_plot(ia, me, pe)
    elif task_type == "classification":
        section.confusion_matrix = _build_confusion_matrix(pe, me)
        section.roc_curve = _build_roc_curve(pe, me)
        section.pr_curve = _build_pr_curve(pe, me)
    return section



def _build_predicted_vs_actual(
    ia: Optional[InterpretabilityAnalysis],
    me: Optional[MetricEvaluation] = None,
    pe: Optional[PipelineExecution] = None,
) -> Optional[PredictedVsActualData]:
    pred_df = _load_external_test_prediction_dataframe(pe)
    if pred_df is not None:
        from_predictions = _predicted_vs_actual_from_predictions(pred_df, me, ia)
        if from_predictions is not None:
            return from_predictions

    return None

def _extract_metrics_from_metric_evaluation(
    me: Optional[MetricEvaluation],
    ia: Optional[InterpretabilityAnalysis],
) -> Optional[dict]:
    """Extract R2, RMSE, MAE from MetricEvaluation for the best trial.

    MetricEvaluation is the authoritative source: it pairs y_true and y_pred
    from the same prediction artifact row by row.
    """
    if not me or not me.evaluation_json:
        return None
    try:
        trial_results = me.evaluation_json.get("trial_metric_results", [])
        if not trial_results:
            return None
        best_id = ia.final_trial_id if ia else me.best_trial_id
        for tr in trial_results:
            if isinstance(tr, dict) and tr.get("trial_id") == best_id:
                result: dict = {}
                agg = tr.get("aggregated_metrics", {})
                if isinstance(agg, dict):
                    for key, val in agg.items():
                        upper = key.upper()
                        if upper.startswith("MAE_"):
                            result["mae"] = round(float(val), 6)
                        elif upper.startswith("R2_"):
                            result["r2"] = round(float(val), 6)
                        elif upper.startswith("RMSE_"):
                            result["rmse"] = round(float(val), 6)
                # Fallback: compute from fold_metrics
                folds = tr.get("fold_metrics", [])
                for key_name, result_key in [("MAE", "mae"), ("R2", "r2"), ("RMSE", "rmse")]:
                    if result_key not in result:
                        vals = []
                        for f in folds:
                            if isinstance(f, dict):
                                fm = f.get("metrics", {})
                                if isinstance(fm, dict):
                                    for k, v in fm.items():
                                        if k.upper() == key_name.upper():
                                            vals.append(float(v))
                        if vals:
                            result[result_key] = round(sum(vals) / len(vals), 6)
                return result if result else None
    except Exception:
        pass
    return None


def _primary_metric_name(me: Optional[MetricEvaluation]) -> str:
    if me and getattr(me, "primary_metric", None):
        return str(getattr(me, "primary_metric", None))
    return "R2"


def _metric_key(metric_name: str) -> str:
    normalised = (metric_name or "").strip().lower()
    normalised = normalised.replace("-", "_").replace(" ", "_").replace(".", "_")
    normalised = normalised.replace("r_squared", "r2").replace("rsquared", "r2")
    if normalised in {"r2", "r_2"}:
        return "r2"
    if normalised in {"mae", "mean_absolute_error"}:
        return "mae"
    if normalised in {"mse", "mean_squared_error"}:
        return "mse"
    if normalised in {"rmse", "root_mean_squared_error"}:
        return "rmse"
    if normalised in {"mape", "mean_absolute_percentage_error"}:
        return "mape"
    return normalised


def _calculate_regression_metric(
    actual: np.ndarray,
    predicted: np.ndarray,
    metric_name: str,
) -> Optional[float]:
    if actual.size == 0 or predicted.size == 0:
        return None
    key = _metric_key(metric_name)
    residuals = actual - predicted
    if key == "mae":
        return float(np.mean(np.abs(residuals)))
    if key == "mse":
        return float(np.mean(np.square(residuals)))
    if key == "rmse":
        return float(np.sqrt(np.mean(np.square(residuals))))
    if key == "r2":
        ss_tot = float(np.sum(np.square(actual - np.mean(actual))))
        if ss_tot == 0:
            return None
        return float(1 - np.sum(np.square(residuals)) / ss_tot)
    if key == "mape":
        non_zero = actual != 0
        if not np.any(non_zero):
            return None
        return float(np.mean(np.abs((actual[non_zero] - predicted[non_zero]) / actual[non_zero])) * 100)
    return None


def _primary_metric_value_from_metric_evaluation(me: Optional[MetricEvaluation]) -> Optional[float]:
    if not me or getattr(me, "best_primary_metric_value", None) is None:
        return None
    try:
        return float(getattr(me, "best_primary_metric_value", None))
    except Exception:
        return None


def _build_primary_split_metrics(valid: pd.DataFrame, primary_metric: str) -> List[Dict[str, Any]]:
    split_metrics: List[Dict[str, Any]] = []
    if valid.empty:
        return split_metrics
    for split, group in valid.groupby("split", sort=False):
        metric_value = _calculate_regression_metric(
            group["actual"].to_numpy(dtype=float),
            group["predicted"].to_numpy(dtype=float),
            primary_metric,
        )
        if metric_value is not None:
            split_metrics.append({
                "split": str(split or "test"),
                "metric_name": primary_metric,
                "metric_value": round(float(metric_value), 6),
            })
    return split_metrics


def _best_display_primary_metric_value(
    split_metrics: List[Dict[str, Any]],
    fallback: Optional[float],
) -> Optional[float]:
    preferred = {"test", "validation", "valid", "val", "holdout"}
    for metric in split_metrics:
        split = str(metric.get("split", "")).lower()
        if split in preferred:
            return float(metric["metric_value"])
    if split_metrics:
        return float(split_metrics[0]["metric_value"])
    return fallback


def _build_residual_plot(
    ia: Optional[InterpretabilityAnalysis],
    me: Optional[MetricEvaluation] = None,
    pe: Optional[PipelineExecution] = None,
) -> Optional[ResidualPlotData]:
    pred_df = _load_external_test_prediction_dataframe(pe)
    if pred_df is not None:
        from_predictions = _residual_plot_from_predictions(pred_df, me, ia)
        if from_predictions is not None:
            return from_predictions

    return None

def _build_train_test_comparison(me: Optional[MetricEvaluation]) -> Optional[TrainTestComparisonData]:
    if not me or not me.evaluation_json:
        return None
    try:
        eval_data = _safe_json(me.evaluation_json)
        trial_results = eval_data.get("trial_metric_results", [])
        if not isinstance(trial_results, list) or not trial_results:
            return None

        best_trial_id = getattr(me, "best_trial_id", None)
        target_trial = None
        for trial in trial_results:
            if isinstance(trial, dict) and trial.get("trial_id") == best_trial_id:
                target_trial = trial
                break
        if target_trial is None:
            target_trial = next((trial for trial in trial_results if isinstance(trial, dict)), None)
        if target_trial is None:
            return None

        metric_name = _primary_metric_name(me)
        fold_metrics = target_trial.get("fold_metrics", [])
        if not isinstance(fold_metrics, list) or not fold_metrics:
            return None

        comparisons: List[Dict[str, Any]] = []
        for index, fm in enumerate(fold_metrics):
            if not isinstance(fm, dict):
                continue
            test_value = _extract_fold_primary_metric_value(fm, metric_name)
            if test_value is None:
                continue
            comparisons.append({
                "fold_index": _safe_int(fm.get("fold_index"), index),
                "test_value": test_value,
                "n_samples": _safe_int(fm.get("n_samples"), 0),
                "metric_name": metric_name,
                "split": "validation",
            })

        return TrainTestComparisonData(comparisons=comparisons) if comparisons else None
    except Exception as exc:
        logger.warning("Failed to build train/test comparison data: %s", exc)
        return None


def _extract_fold_primary_metric_value(
    fold_metric: Dict[str, Any],
    metric_name: str,
) -> Optional[float]:
    value = fold_metric.get("primary_metric_value")
    if value is not None:
        parsed = _safe_float(value)
        if parsed is not None:
            return parsed

    metrics = fold_metric.get("metrics", {})
    if not isinstance(metrics, dict) or not metrics:
        return None

    wanted_key = _metric_key(metric_name)
    for key, candidate in metrics.items():
        if _metric_key(str(key)) == wanted_key:
            parsed = _safe_float(candidate)
            if parsed is not None:
                return parsed
    return None


def _safe_float(value: Any) -> Optional[float]:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(parsed):
        return None
    return parsed


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _build_cv_box_plot(me: Optional[MetricEvaluation]) -> Optional[CrossValidationBoxPlotData]:
    if not me or not me.evaluation_json:
        return None
    eval_data = _safe_json(me.evaluation_json)
    trial_results = eval_data.get("trial_metric_results", [])
    if not isinstance(trial_results, list) or not trial_results:
        return None

    metric_name = _primary_metric_name(me)
    folds: List[Dict[str, Any]] = []
    for trial in trial_results:
        if not isinstance(trial, dict):
            continue
        for fm in trial.get("fold_metrics", []):
            if not isinstance(fm, dict):
                continue
            metric_value = _extract_fold_primary_metric_value(fm, metric_name)
            if metric_value is None:
                continue
            folds.append({
                "trial_id": trial.get("trial_id", ""),
                "model_family": trial.get("model_family", ""),
                "fold_index": _safe_int(fm.get("fold_index"), 0),
                "metric_value": metric_value,
            })

    return CrossValidationBoxPlotData(folds=folds, metric_name=metric_name) if folds else None


def _prediction_columns(df: pd.DataFrame) -> Optional[tuple[str, str]]:
    actual_col = _find_column(df, ["actual", "y_true", "target", "ground_truth", "label"])
    predicted_col = _find_column(df, ["predicted", "y_pred", "prediction", "predicted_value"])
    if actual_col is None or predicted_col is None:
        logger.warning("Prediction artifact is missing actual/predicted columns: %s", list(df.columns))
        return None
    return actual_col, predicted_col


def _predicted_vs_actual_from_predictions(
    pred_df: pd.DataFrame,
    me: Optional[MetricEvaluation],
    ia: Optional[InterpretabilityAnalysis],
) -> Optional[PredictedVsActualData]:
    columns = _prediction_columns(pred_df)
    if columns is None:
        return None
    actual_col, predicted_col = columns
    valid = pred_df[[actual_col, predicted_col]].copy()
    valid.columns = ["actual", "predicted"]
    valid = valid.apply(pd.to_numeric, errors="coerce").dropna()
    if valid.empty:
        return None

    residuals = valid["actual"] - valid["predicted"]
    valid["residual"] = residuals
    n = min(len(valid), MAX_SCATTER_POINTS)
    step = max(1, len(valid) // n)
    sampled = valid.iloc[::step].head(n)
    points = [
        {
            "actual": float(row.actual),
            "predicted": float(row.predicted),
            "residual": float(row.residual),
        }
        for row in sampled.itertuples(index=False)
    ]

    actual = valid["actual"].to_numpy(dtype=float)
    predicted = valid["predicted"].to_numpy(dtype=float)
    r_squared = _calculate_regression_metric(actual, predicted, "r2") or 0.0
    rmse = _calculate_regression_metric(actual, predicted, "rmse") or 0.0
    mae = _calculate_regression_metric(actual, predicted, "mae") or 0.0
    primary_metric = _primary_metric_name(me)

    split_frame = valid.copy()
    if "split" in pred_df.columns:
        split_frame["split"] = pred_df.loc[valid.index, "split"].astype(str).values
    else:
        split_frame["split"] = "test"
    split_metrics = _build_primary_split_metrics(split_frame, primary_metric)

    return PredictedVsActualData(
        points=points,
        r_squared=round(float(r_squared), 6),
        rmse=round(float(rmse), 6),
        mae=round(float(mae), 6),
        residual_mean=round(float(residuals.mean()), 6),
        residual_std=round(float(residuals.std()), 6) if len(residuals) > 1 else 0.0,
        histogram_bins=_build_histogram_bins(residuals.to_numpy(dtype=float)),
        primary_metric=primary_metric,
        primary_metric_value=_best_display_primary_metric_value(
            split_metrics,
            _primary_metric_value_from_metric_evaluation(me),
        ),
        split_metrics=split_metrics,
    )


def _residual_plot_from_predictions(
    pred_df: pd.DataFrame,
    me: Optional[MetricEvaluation],
    ia: Optional[InterpretabilityAnalysis],
) -> Optional[ResidualPlotData]:
    columns = _prediction_columns(pred_df)
    if columns is None:
        return None
    actual_col, predicted_col = columns
    valid = pred_df[[actual_col, predicted_col]].copy()
    valid.columns = ["actual", "predicted"]
    valid = valid.apply(pd.to_numeric, errors="coerce").dropna()
    if valid.empty:
        return None

    residuals = valid["actual"] - valid["predicted"]
    n = min(len(valid), MAX_SCATTER_POINTS)
    step = max(1, len(valid) // n)
    sampled = valid.assign(residual=residuals).iloc[::step].head(n)
    points = [
        {"predicted": float(row.predicted), "residual": float(row.residual)}
        for row in sampled.itertuples(index=False)
    ]

    actual = valid["actual"].to_numpy(dtype=float)
    predicted = valid["predicted"].to_numpy(dtype=float)
    return ResidualPlotData(
        points=points,
        r_squared=round(float(_calculate_regression_metric(actual, predicted, "r2") or 0.0), 6),
        rmse=round(float(_calculate_regression_metric(actual, predicted, "rmse") or 0.0), 6),
    )


def _build_confusion_matrix(
    pe: Optional[PipelineExecution],
    me: Optional[MetricEvaluation],
) -> Optional[ConfusionMatrixData]:
    pred_df = _load_prediction_dataframe(pe, me, None)
    if pred_df is None:
        return None
    try:
        y_true_col = _find_column(pred_df, ["y_true", "target", "actual", "ground_truth", "label"])
        y_pred_col = _find_column(pred_df, ["y_pred", "prediction", "predicted", "predicted_label"])
        if y_true_col is None or y_pred_col is None:
            return None
        from sklearn.metrics import confusion_matrix
        y_true = pred_df[y_true_col].astype(str).values
        y_pred = pred_df[y_pred_col].astype(str).values
        labels = sorted(set(list(y_true) + list(y_pred)))
        if len(labels) > 20:
            logger.warning("Too many unique classes (%d) for confusion matrix.", len(labels))
            return None
        matrix = confusion_matrix(y_true, y_pred, labels=labels)
        return ConfusionMatrixData(labels=[str(label) for label in labels], matrix=matrix.tolist())
    except Exception as exc:
        logger.warning("Failed to compute confusion matrix: %s", exc)
        return None


def _build_roc_curve(
    pe: Optional[PipelineExecution],
    me: Optional[MetricEvaluation],
) -> Optional[ROCCurveData]:
    pred_df = _load_prediction_dataframe(pe, me, None)
    if pred_df is None:
        return None
    try:
        y_true_col = _find_column(pred_df, ["y_true", "target", "actual", "ground_truth", "label"])
        prob_cols = _find_prob_columns(pred_df)
        if y_true_col is None or not prob_cols:
            return None
        from sklearn.metrics import auc, roc_curve
        y_true = pred_df[y_true_col].values
        classes = _extract_class_labels(pred_df, y_true)
        if len(classes) > 20:
            logger.warning("ROC curve: too many classes (%d)", len(classes))
            return None
        curves: List[Dict[str, Any]] = []
        for class_index, cls in enumerate(classes):
            scores = _scores_for_class(pred_df, cls, class_index, classes, prob_cols)
            if scores is None:
                continue
            y_bin = (y_true == cls).astype(int)
            try:
                fpr, tpr, _ = roc_curve(y_bin, scores)
                curves.append({
                    "class_id": str(cls),
                    "fpr": fpr.tolist(),
                    "tpr": tpr.tolist(),
                    "auc": float(auc(fpr, tpr)),
                })
            except Exception:
                continue
        return ROCCurveData(curves=curves) if curves else None
    except Exception as exc:
        logger.warning("Failed to compute ROC curves: %s", exc)
        return None


def _build_pr_curve(
    pe: Optional[PipelineExecution],
    me: Optional[MetricEvaluation],
) -> Optional[PRCurveData]:
    pred_df = _load_prediction_dataframe(pe, me, None)
    if pred_df is None:
        return None
    try:
        y_true_col = _find_column(pred_df, ["y_true", "target", "actual", "ground_truth", "label"])
        prob_cols = _find_prob_columns(pred_df)
        if y_true_col is None or not prob_cols:
            return None
        from sklearn.metrics import average_precision_score, precision_recall_curve
        y_true = pred_df[y_true_col].values
        classes = _extract_class_labels(pred_df, y_true)
        if len(classes) > 20:
            logger.warning("PR curve: too many classes (%d)", len(classes))
            return None
        curves: List[Dict[str, Any]] = []
        for class_index, cls in enumerate(classes):
            scores = _scores_for_class(pred_df, cls, class_index, classes, prob_cols)
            if scores is None:
                continue
            y_bin = (y_true == cls).astype(int)
            try:
                precision, recall, _ = precision_recall_curve(y_bin, scores)
                curves.append({
                    "class_id": str(cls),
                    "recall": recall.tolist(),
                    "precision": precision.tolist(),
                    "average_precision": float(average_precision_score(y_bin, scores)),
                })
            except Exception:
                continue
        return PRCurveData(curves=curves) if curves else None
    except Exception as exc:
        logger.warning("Failed to compute PR curves: %s", exc)
        return None

def _build_histogram_bins(values: np.ndarray, bins: int = 20) -> List[Dict[str, float]]:
    if values.size == 0:
        return []
    counts, edges = np.histogram(values, bins=min(bins, max(1, values.size)))
    return [
        {"bin_start": float(edges[i]), "bin_end": float(edges[i + 1]), "count": int(counts[i])}
        for i in range(len(counts))
    ]


def _load_external_test_prediction_dataframe(
    pe: Optional[PipelineExecution],
) -> Optional[pd.DataFrame]:
    """Load final external-test predictions only.

    Regression performance charts must not silently fall back to CV/OOF
    prediction artifacts, because those do not represent the final external
    test set.
    """
    path = _external_test_prediction_path(pe)
    if not path:
        logger.info("External test prediction artifact is not available for visualization.")
        return None
    if not os.path.exists(path):
        logger.warning("External test prediction artifact does not exist: %s", path)
        return None

    try:
        df = _load_table(path)
    except Exception as exc:
        logger.warning("Failed to load external test prediction artifact %s: %s", path, exc)
        return None

    if "is_final_external_test" in df.columns:
        df = df[df["is_final_external_test"].astype(bool)]
    if "split" in df.columns:
        df = df[df["split"].astype(str).str.lower().eq("test")]

    if df.empty:
        logger.warning("External test prediction artifact has no final test rows: %s", path)
        return None
    return df


def _external_test_prediction_path(pe: Optional[PipelineExecution]) -> Optional[str]:
    if not pe or not pe.execution_json:
        return None
    execution_json = _safe_json(pe.execution_json)
    manifest = execution_json.get("training_artifact_manifest") or {}
    path = manifest.get("external_test_prediction_path")
    if path:
        return path

    # Backward/diagnostic fallback for partially materialized responses.
    artifact_manifest = execution_json.get("artifact_manifest") or {}
    return artifact_manifest.get("external_test_prediction_path")

def _load_prediction_dataframe(
    pe: Optional[PipelineExecution],
    me: Optional[MetricEvaluation],
    ia: Optional[InterpretabilityAnalysis],
) -> Optional[pd.DataFrame]:
    paths = _find_prediction_paths(pe, me, ia)
    if not paths:
        return None
    frames: List[pd.DataFrame] = []
    for path in paths:
        try:
            frames.append(_load_table(path))
        except Exception as exc:
            logger.warning("Failed to load prediction artifact %s: %s", path, exc)
    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


def _find_prediction_paths(
    pe: Optional[PipelineExecution],
    me: Optional[MetricEvaluation],
    ia: Optional[InterpretabilityAnalysis] = None,
) -> List[str]:
    best_id = _best_trial_id(me, ia)
    paths: List[str] = []

    if me and me.evaluation_json:
        eval_data = _safe_json(me.evaluation_json)
        for trial in eval_data.get("trial_metric_results", []):
            if not isinstance(trial, dict) or (best_id and trial.get("trial_id") != best_id):
                continue
            for fm in trial.get("fold_metrics", []):
                if isinstance(fm, dict):
                    _append_existing_path(paths, fm.get("prediction_artifact_path"))
            for key in ("prediction_artifact_paths", "prediction_artifact_path"):
                _append_existing_path(paths, trial.get(key))

    if pe:
        for source in (_safe_json(pe.execution_json), _safe_json(pe.metric_evaluation_input_json)):
            for trial in source.get("trial_results", []):
                if not isinstance(trial, dict) or (best_id and trial.get("trial_id") != best_id):
                    continue
                for fold in trial.get("fold_results", []):
                    if isinstance(fold, dict):
                        _append_existing_path(paths, fold.get("prediction_artifact_path"))
                for key in ("prediction_artifact_paths", "prediction_artifact_path"):
                    _append_existing_path(paths, trial.get(key))
            if not best_id:
                _append_existing_path(paths, source.get("prediction_artifacts"))

    unique: List[str] = []
    seen = set()
    for path in paths:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    if not unique:
        logger.info(
            "No prediction artifacts found: best_trial_id=%s me.id=%s pe.id=%s",
            best_id,
            getattr(me, "id", None) if me else None,
            getattr(pe, "id", None) if pe else None,
        )
    return unique


def _append_existing_path(paths: List[str], value: Any) -> None:
    if not value:
        return
    values = value if isinstance(value, list) else [value]
    for item in values:
        if isinstance(item, str) and item and os.path.exists(item):
            paths.append(item)


def _best_trial_id(me: Optional[MetricEvaluation], ia: Optional[InterpretabilityAnalysis]) -> Optional[str]:
    return (getattr(ia, "final_trial_id", None) if ia and getattr(ia, "final_trial_id", None) else None) or (getattr(me, "best_trial_id", None) if me else None)


def _load_table(path: str) -> pd.DataFrame:
    return pd.read_parquet(path) if path.endswith(".parquet") else pd.read_csv(path)


def _extract_class_labels(df: pd.DataFrame, y_true: np.ndarray) -> List[Any]:
    if "class_labels" in df.columns:
        for value in df["class_labels"].dropna():
            try:
                parsed = ast.literal_eval(str(value))
                if isinstance(parsed, list) and parsed:
                    return parsed
            except Exception:
                continue
    return sorted(set(y_true.tolist()))


def _scores_for_class(
    df: pd.DataFrame,
    cls: Any,
    class_index: int,
    classes: List[Any],
    prob_cols: List[str],
) -> Optional[np.ndarray]:
    direct_col = _find_column(df, [
        f"y_pred_proba_class_{cls}",
        f"prob_{cls}",
        f"proba_{cls}",
        f"score_{cls}",
    ])
    if direct_col is not None:
        return df[direct_col].values.astype(float)

    indexed_col = f"y_pred_proba_class_{class_index}"
    if indexed_col in df.columns:
        return df[indexed_col].values.astype(float)

    is_binary_single_proba = (
        len(classes) == 2
        and len(prob_cols) == 1
        and not any("class" in c.lower() for c in prob_cols)
    )
    if is_binary_single_proba:
        proba = df[prob_cols[0]].values.astype(float)
        return proba if class_index == 1 else 1.0 - proba
    return None


def _find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _find_prob_columns(df: pd.DataFrame) -> List[str]:
    """Find probability score columns, keeping class-indexed columns in numeric order."""
    prob_cols: List[str] = []
    for col in df.columns:
        lower = col.lower()
        if lower.startswith(("prob", "proba", "score")) or "proba" in lower:
            prob_cols.append(col)

    def sort_key(col: str):
        if col.startswith("y_pred_proba_class_"):
            suffix = col.rsplit("_", 1)[-1]
            if suffix.isdigit():
                return (0, int(suffix), col)
        return (1, 0, col)

    return sorted(prob_cols, key=sort_key)
