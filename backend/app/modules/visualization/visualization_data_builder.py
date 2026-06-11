import logging
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
        section.predicted_vs_actual = _build_predicted_vs_actual(ia, me)
        section.residual_plot = _build_residual_plot(ia, me)
    elif task_type == "classification":
        section.confusion_matrix = _build_confusion_matrix(pe, me)
        section.roc_curve = _build_roc_curve(pe, me)
        section.pr_curve = _build_pr_curve(pe, me)
    return section


def _build_predicted_vs_actual(
    ia: Optional[InterpretabilityAnalysis],
    me: Optional[MetricEvaluation] = None,
) -> Optional[PredictedVsActualData]:
    if not ia or not ia.residual_analysis_json:
        return None
    data = _safe_json(ia.residual_analysis_json)
    residuals = data.get("residuals", [])
    predicted = data.get("predicted_values", [])
    if not residuals or not predicted or len(residuals) != len(predicted):
        return None
    n = min(len(residuals), MAX_SCATTER_POINTS)
    step = max(1, len(residuals) // n)
    indices = list(range(0, len(residuals), step))[:n]
    sampled_residuals = [residuals[i] for i in indices]
    sampled_predicted = [predicted[i] for i in indices]
    points = [
        {"actual": float(p + r), "predicted": float(p), "residual": float(r)}
        for p, r in zip(sampled_predicted, sampled_residuals)
    ]

    # Compute MAE from residuals as baseline
    mae = round(float(np.mean(np.abs(np.asarray(residuals, dtype=float)))), 6)

    # Override R² / RMSE / MAE with authoritative values from MetricEvaluation.
    # The residual_analysis_json values come from InterpretabilityAnalysis which
    # may pair y_true (from feature matrix) with y_pred (from prediction files)
    # in misaligned row order.  MetricEvaluation is the single source of truth.
    r_squared = float(data.get("r_squared", 0))
    rmse = float(data.get("rmse", 0))
    me_metrics = _extract_metrics_from_metric_evaluation(me, ia)
    if me_metrics:
        if me_metrics.get("r2") is not None:
            r_squared = me_metrics["r2"]
        if me_metrics.get("rmse") is not None:
            rmse = me_metrics["rmse"]
        if me_metrics.get("mae") is not None:
            mae = me_metrics["mae"]

    # Build histogram bins
    hist_bins = [
        {"bin_start": float(b["bin_start"]), "bin_end": float(b["bin_end"]), "count": int(b["count"])}
        for b in (data.get("histogram_bins") or [])
    ]

    return PredictedVsActualData(
        points=points,
        r_squared=r_squared,
        rmse=rmse,
        mae=mae,
        residual_mean=float(data.get("residual_mean", 0)),
        residual_std=float(data.get("residual_std", 0)),
        histogram_bins=hist_bins,
    )


def _extract_metrics_from_metric_evaluation(
    me: Optional[MetricEvaluation],
    ia: Optional[InterpretabilityAnalysis],
) -> Optional[dict]:
    """Extract R², RMSE, MAE from MetricEvaluation for the best trial.

    MetricEvaluation is the authoritative source — it pairs y_true and y_pred
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


def _build_residual_plot(
    ia: Optional[InterpretabilityAnalysis],
    me: Optional[MetricEvaluation] = None,
) -> Optional[ResidualPlotData]:
    if not ia or not ia.residual_analysis_json:
        return None
    data = _safe_json(ia.residual_analysis_json)
    residuals = data.get("residuals", [])
    predicted = data.get("predicted_values", [])
    if not residuals or not predicted or len(residuals) != len(predicted):
        return None
    n = min(len(residuals), MAX_SCATTER_POINTS)
    step = max(1, len(residuals) // n)
    sampled_residuals = residuals[::step][:n]
    sampled_predicted = predicted[::step][:n]
    points = [
        {"predicted": float(p), "residual": float(r)}
        for p, r in zip(sampled_predicted, sampled_residuals)
    ]

    r_squared = float(data.get("r_squared", 0))
    rmse = float(data.get("rmse", 0))
    # Override R² / RMSE with authoritative values from MetricEvaluation
    me_metrics = _extract_metrics_from_metric_evaluation(me, ia)
    if me_metrics:
        if me_metrics.get("r2") is not None:
            r_squared = me_metrics["r2"]
        if me_metrics.get("rmse") is not None:
            rmse = me_metrics["rmse"]

    return ResidualPlotData(
        points=points,
        r_squared=r_squared,
        rmse=rmse,
    )


def _build_train_test_comparison(me: Optional[MetricEvaluation]) -> Optional[TrainTestComparisonData]:
    if not me or not me.evaluation_json:
        return None
    eval_data = _safe_json(me.evaluation_json)
    trial_results = eval_data.get("trial_metric_results", [])
    if not trial_results:
        return None

    best_trial_id = me.best_trial_id
    target_trial = None
    for trial in trial_results:
        if isinstance(trial, dict) and trial.get("trial_id") == best_trial_id:
            target_trial = trial
            break
    if target_trial is None:
        target_trial = trial_results[0] if isinstance(trial_results[0], dict) else None
    if target_trial is None:
        return None

    fold_metrics = target_trial.get("fold_metrics", [])
    comparisons: List[Dict[str, Any]] = []
    for fm in fold_metrics:
        if isinstance(fm, dict):
            comparisons.append({
                "fold_index": fm.get("fold_index", 0),
                "test_value": fm.get("primary_metric_value", 0),
                "n_samples": fm.get("n_samples", 0),
            })
    return TrainTestComparisonData(comparisons=comparisons)


def _build_cv_box_plot(me: Optional[MetricEvaluation]) -> Optional[CrossValidationBoxPlotData]:
    if not me or not me.evaluation_json:
        return None
    eval_data = _safe_json(me.evaluation_json)
    trial_results = eval_data.get("trial_metric_results", [])
    if not trial_results:
        return None

    metric_name = me.primary_metric or "metric"
    folds: List[Dict[str, Any]] = []

    for trial in trial_results:
        if not isinstance(trial, dict):
            continue
        fm_list = trial.get("fold_metrics", [])
        for fm in fm_list:
            if isinstance(fm, dict):
                folds.append({
                    "trial_id": trial.get("trial_id", ""),
                    "model_family": trial.get("model_family", ""),
                    "fold_index": fm.get("fold_index", 0),
                    "metric_value": fm.get("primary_metric_value", 0),
                })

    return CrossValidationBoxPlotData(folds=folds, metric_name=metric_name)


def _build_confusion_matrix(
    pe: Optional[PipelineExecution],
    me: Optional[MetricEvaluation],
) -> Optional[ConfusionMatrixData]:
    """Compute confusion matrix from prediction parquet files."""
    pred_path = _find_prediction_parquet(pe, me)
    if not pred_path:
        return None
    try:
        df = _load_parquet(pred_path)
        y_true_col = _find_column(df, ["y_true", "target", "actual", "ground_truth", "label"])
        y_pred_col = _find_column(df, ["y_pred", "prediction", "predicted", "predicted_label"])
        if y_true_col is None or y_pred_col is None:
            logger.warning("Could not find y_true/y_pred columns in parquet for confusion matrix.")
            return None
        from sklearn.metrics import confusion_matrix
        y_true = df[y_true_col].astype(str).values
        y_pred = df[y_pred_col].astype(str).values
        labels = sorted(set(list(y_true) + list(y_pred)))
        if len(labels) > 20:
            logger.warning("Too many unique classes (%d) for confusion matrix.", len(labels))
            return None
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        return ConfusionMatrixData(
            labels=[str(l) for l in labels],
            matrix=cm.tolist(),
        )
    except Exception as e:
        logger.warning("Failed to compute confusion matrix: %s", str(e))
        return None


def _build_roc_curve(
    pe: Optional[PipelineExecution],
    me: Optional[MetricEvaluation],
) -> Optional[ROCCurveData]:
    """Compute ROC curves from prediction parquet files."""
    pred_path = _find_prediction_parquet(pe, me)
    if not pred_path:
        logger.info("ROC curve: no prediction parquet found")
        return None
    try:
        df = _load_parquet(pred_path)
        y_true_col = _find_column(df, ["y_true", "target", "actual", "ground_truth", "label"])
        prob_cols = _find_prob_columns(df)
        if y_true_col is None:
            logger.warning(
                "ROC curve: y_true column not found in %s, columns=%s",
                pred_path, list(df.columns),
            )
            return None
        if not prob_cols:
            logger.warning(
                "ROC curve: no probability columns found in %s, columns=%s",
                pred_path, list(df.columns),
            )
            return None
        from sklearn.metrics import roc_curve, auc
        y_true = df[y_true_col].values
        classes = sorted(set(y_true))
        if len(classes) > 20:
            logger.warning("ROC curve: too many classes (%d)", len(classes))
            return None

        # Detect binary classification with a single proba column (e.g. y_pred_proba)
        is_binary_proba = (
            len(classes) == 2
            and len(prob_cols) == 1
            and not any("class" in c.lower() for c in prob_cols)
        )

        curves: List[Dict[str, Any]] = []
        for cls in classes:
            y_bin = (y_true == cls).astype(int)
            prob_col = _find_column(df, [
                f"y_pred_proba_class_{cls}",
                f"prob_{cls}", f"proba_{cls}", f"score_{cls}",
            ])
            if prob_col is not None:
                scores = df[prob_col].values.astype(float)
            elif is_binary_proba:
                # Single proba column holds P(positive class)
                proba = df[prob_cols[0]].values.astype(float)
                scores = proba if cls == classes[1] else 1.0 - proba
            else:
                continue
            try:
                fpr, tpr, _ = roc_curve(y_bin, scores)
                roc_auc = auc(fpr, tpr)
                curves.append({
                    "class_id": str(cls),
                    "fpr": fpr.tolist(),
                    "tpr": tpr.tolist(),
                    "auc": float(roc_auc),
                })
            except Exception:
                continue
        if not curves:
            logger.warning("ROC curve: no curves produced for classes=%s", classes)
        return ROCCurveData(curves=curves) if curves else None
    except Exception as e:
        logger.warning("Failed to compute ROC curves: %s", str(e))
        return None


def _build_pr_curve(
    pe: Optional[PipelineExecution],
    me: Optional[MetricEvaluation],
) -> Optional[PRCurveData]:
    """Compute PR curves from prediction parquet files."""
    pred_path = _find_prediction_parquet(pe, me)
    if not pred_path:
        logger.info("PR curve: no prediction parquet found")
        return None
    try:
        df = _load_parquet(pred_path)
        y_true_col = _find_column(df, ["y_true", "target", "actual", "ground_truth", "label"])
        if y_true_col is None:
            logger.warning(
                "PR curve: y_true column not found in %s, columns=%s",
                pred_path, list(df.columns),
            )
            return None
        prob_cols = _find_prob_columns(df)
        if not prob_cols:
            logger.warning(
                "PR curve: no probability columns found in %s, columns=%s",
                pred_path, list(df.columns),
            )
            return None
        y_true = df[y_true_col].values
        classes = sorted(set(y_true))
        if len(classes) > 20:
            logger.warning("PR curve: too many classes (%d)", len(classes))
            return None

        from sklearn.metrics import precision_recall_curve, average_precision_score

        # Detect binary classification with a single proba column
        is_binary_proba = (
            len(classes) == 2
            and len(prob_cols) == 1
            and not any("class" in c.lower() for c in prob_cols)
        )

        curves: List[Dict[str, Any]] = []
        for cls in classes:
            y_bin = (y_true == cls).astype(int)
            prob_col = _find_column(df, [
                f"y_pred_proba_class_{cls}",
                f"prob_{cls}", f"proba_{cls}", f"score_{cls}",
            ])
            if prob_col is not None:
                scores = df[prob_col].values.astype(float)
            elif is_binary_proba:
                proba = df[prob_cols[0]].values.astype(float)
                scores = proba if cls == classes[1] else 1.0 - proba
            else:
                continue
            try:
                precision, recall, _ = precision_recall_curve(y_bin, scores)
                ap = average_precision_score(y_bin, scores)
                curves.append({
                    "class_id": str(cls),
                    "recall": recall.tolist(),
                    "precision": precision.tolist(),
                    "average_precision": float(ap),
                })
            except Exception:
                continue
        if not curves:
            logger.warning("PR curve: no curves produced for classes=%s", classes)
        return PRCurveData(curves=curves) if curves else None
    except Exception as e:
        logger.warning("Failed to compute PR curves: %s", str(e))
        return None


# ---- Parquet helpers ----

def _find_prediction_parquet(
    pe: Optional[PipelineExecution],
    me: Optional[MetricEvaluation],
) -> Optional[str]:
    """Extract the best trial's prediction parquet path."""
    import os
    candidate: Optional[str] = None
    if me and me.evaluation_json:
        eval_data = _safe_json(me.evaluation_json)
        trial_results = eval_data.get("trial_metric_results", [])
        best_id = me.best_trial_id
        for trial in trial_results:
            if isinstance(trial, dict) and trial.get("trial_id") == best_id:
                fm_list = trial.get("fold_metrics", [])
                for fm in fm_list:
                    if isinstance(fm, dict):
                        path = fm.get("prediction_artifact_path", "")
                        if path and os.path.exists(path):
                            return path
    if pe and pe.execution_json:
        exec_data = _safe_json(pe.execution_json)
        for trial in exec_data.get("trial_results", []):
            if isinstance(trial, dict):
                for path_key in ("prediction_artifact_paths", "prediction_artifact_path"):
                    paths = trial.get(path_key, [])
                    if isinstance(paths, str):
                        paths = [paths]
                    for p in paths:
                        if p and os.path.exists(p):
                            return p
    if not candidate:
        logger.info(
            "No prediction parquet found: me.id=%s, me.evaluation_json_keys=%s, pe.id=%s",
            me.id if me else None,
            list(_safe_json(me.evaluation_json).keys()) if me and me.evaluation_json else None,
            pe.id if pe else None,
        )
    return candidate


def _load_parquet(path: str) -> pd.DataFrame:
    return pd.read_parquet(path) if path.endswith(".parquet") else pd.read_csv(path)


def _find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _find_prob_columns(df: pd.DataFrame) -> List[str]:
    """Find probability score columns.

    Matches the column naming conventions used by prediction_writer.py:
      - y_pred_proba            (binary classification)
      - y_pred_proba_class_0 .. N (multi-class classification)
    Also matches legacy prefixes for compatibility.
    """
    prob_cols: List[str] = []
    for col in df.columns:
        lower = col.lower()
        if lower.startswith(("prob", "proba", "score")):
            prob_cols.append(col)
        elif "proba" in lower:
            prob_cols.append(col)
    return prob_cols
