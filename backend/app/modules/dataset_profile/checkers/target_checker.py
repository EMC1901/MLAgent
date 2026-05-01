import pandas as pd
import numpy as np
from typing import Optional


def check_target(
    df: pd.DataFrame,
    target_column: str,
    task_type: str,
) -> dict:
    if target_column not in df.columns:
        return {
            "target_column": target_column,
            "task_type": task_type,
            "dtype": None,
            "missing_count": 0,
            "missing_ratio": 0.0,
            "errors": [f"Target column '{target_column}' not found in dataset."],
        }

    series = df[target_column]
    missing_count = int(series.isna().sum())
    missing_ratio = missing_count / len(series) if len(series) > 0 else 0.0
    clean = series.dropna()

    base = {
        "target_column": target_column,
        "task_type": task_type,
        "dtype": str(series.dtype),
        "missing_count": missing_count,
        "missing_ratio": missing_ratio,
    }

    if task_type == "regression":
        return _profile_regression(clean, base)
    elif task_type == "classification":
        return _profile_classification(clean, base)
    else:
        base["warnings"] = [f"No specific target profiling for task_type '{task_type}'."]
        return base


def _profile_regression(series: pd.Series, base: dict) -> dict:
    numeric = pd.to_numeric(series, errors="coerce").dropna()

    if len(numeric) == 0:
        base["errors"] = ["Target column contains no numeric values for regression."]
        return base

    q1 = float(numeric.quantile(0.25))
    q3 = float(numeric.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outliers = int(((numeric < lower) | (numeric > upper)).sum())

    warnings = []
    if outliers > 0:
        warnings.append(
            f"Target column has {outliers} potential outliers "
            f"({outliers / len(numeric) * 100:.1f}%)."
        )

    skew_val = float(numeric.skew())
    if abs(skew_val) > 1:
        warnings.append(
            f"Target distribution is skewed (skewness={skew_val:.2f}). "
            "Target transformation may be needed."
        )

    result = {
        **base,
        "min": float(numeric.min()),
        "max": float(numeric.max()),
        "mean": float(numeric.mean()),
        "median": float(numeric.median()),
        "std": float(numeric.std()),
        "skewness": skew_val,
        "outlier_count": outliers,
    }
    if warnings:
        result["warnings"] = warnings
    return result


def _profile_classification(series: pd.Series, base: dict) -> dict:
    counts = series.value_counts()
    total = len(series)

    class_dist = []
    for label, cnt in counts.items():
        class_dist.append({
            "label": str(label),
            "count": int(cnt),
            "ratio": float(cnt / total) if total > 0 else 0.0,
        })

    majority = float(counts.iloc[0] / total) if total > 0 and len(counts) > 0 else 0.0
    minority_count = int(counts.iloc[-1]) if len(counts) > 0 else 0
    is_imbalanced = majority > 0.8 if len(counts) > 1 else False

    warnings = []
    if is_imbalanced:
        warnings.append(
            f"Classes are imbalanced: majority class ratio = {majority:.2f}. "
            "Consider stratification or class weighting."
        )
    if len(counts) > 20:
        warnings.append(f"Large number of classes ({len(counts)}).")

    result = {
        **base,
        "class_count": len(counts),
        "class_distribution": class_dist[:20],
        "majority_class_ratio": majority,
        "minority_class_count": minority_count,
        "is_imbalanced": is_imbalanced,
    }
    if warnings:
        result["warnings"] = warnings
    return result
