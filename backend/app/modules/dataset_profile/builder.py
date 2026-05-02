import uuid
import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from app.modules.dataset_profile.profiler import (
    aggregate_profiling_summary,
    build_workflow_planning_input,
)

logger = logging.getLogger(__name__)


def build_dataset_profile(
    context: dict,
    loading_result: dict,
    df: Optional[pd.DataFrame],
    schema_result: dict,
    modality_result: dict,
    quality_result: dict,
    target_result: dict,
    source_resolution: dict,
    max_preview_rows: int = 20,
) -> dict:
    profile_id = f"profile_{uuid.uuid4().hex[:8]}"
    now = datetime.now()

    is_loaded = loading_result.get("is_loaded", False)
    n_samples = loading_result.get("n_rows", 0)
    n_columns = loading_result.get("n_columns", 0)

    input_columns = context.get("dataset_context", {}).get("expected_input_columns", [])
    target_column = context.get("expected_target_column", "")

    columns_info = []
    if df is not None and not df.empty:
        for col in df.columns:
            role = "other"
            if col == target_column:
                role = "target"
            elif col in input_columns:
                role = "input"
            missing_count = int(df[col].isna().sum())
            columns_info.append({
                "name": col,
                "role": role,
                "dtype": str(df[col].dtype),
                "missing_count": missing_count,
                "missing_ratio": missing_count / n_samples if n_samples > 0 else 0.0,
            })

    source_type = source_resolution.get("source_type", "unknown")
    dataset_source = {
        "source_type": source_type,
        "dataset_reference": source_resolution.get("dataset_reference"),
        "loader": source_resolution.get("loader_name"),
        "loaded_from": source_resolution.get("dataset_reference"),
    }
    if source_type == "uploaded_file":
        dataset_source["file_name"] = loading_result.get("file_name")
        dataset_source["file_id"] = source_resolution.get("file_id")
        dataset_source["file_path"] = source_resolution.get("file_path")

    dataset_schema = {
        "n_samples": n_samples,
        "n_columns": n_columns,
        "columns": columns_info,
        "input_columns": input_columns,
        "target_column": target_column,
    }

    modality_check = {
        "expected_input_modality": modality_result.get("expected_input_modality"),
        "detected_input_modality": modality_result.get("detected_input_modality"),
        "is_consistent": modality_result.get("is_consistent", True),
        "messages": modality_result.get("messages", []),
    }

    target_profile = {
        "target_column": target_column,
        "task_type": context.get("expected_task_type"),
        "dtype": target_result.get("dtype"),
        "missing_count": target_result.get("missing_count", 0),
        "missing_ratio": target_result.get("missing_ratio", 0.0),
    }
    if context.get("expected_task_type") == "regression":
        target_profile.update({
            "min": target_result.get("min"),
            "max": target_result.get("max"),
            "mean": target_result.get("mean"),
            "median": target_result.get("median"),
            "std": target_result.get("std"),
            "skewness": target_result.get("skewness"),
            "outlier_count": target_result.get("outlier_count", 0),
        })
    elif context.get("expected_task_type") == "classification":
        target_profile.update({
            "class_count": target_result.get("class_count"),
            "class_distribution": target_result.get("class_distribution"),
            "majority_class_ratio": target_result.get("majority_class_ratio"),
            "minority_class_count": target_result.get("minority_class_count"),
            "is_imbalanced": target_result.get("is_imbalanced"),
        })

    data_quality = {
        "missing_values": quality_result.get("missing_values", {}),
        "duplicates": quality_result.get("duplicates", {}),
        "invalid_rows": quality_result.get("invalid_rows", {}),
        "warnings": quality_result.get("warnings", []),
        "errors": quality_result.get("errors", []),
    }

    schema_errors = schema_result.get("schema_errors", [])
    profiling_summary = aggregate_profiling_summary(
        is_loaded=is_loaded,
        n_samples=n_samples,
        schema_errors=schema_errors,
        modality_consistent=modality_result.get("is_consistent", True),
        quality_result=quality_result,
        target_result=target_result,
    )

    wf_input = build_workflow_planning_input(
        context=context,
        n_samples=n_samples,
        n_columns=n_columns,
        input_columns=input_columns,
        target_column=target_column,
        quality_result=quality_result,
        target_result=target_result,
        quality_level=profiling_summary["quality_level"],
        is_usable=profiling_summary["is_usable_for_ml"],
    )

    # Determine status
    all_errors = schema_errors + quality_result.get("errors", []) + target_result.get("errors", [])
    all_warnings = (
        quality_result.get("warnings", [])
        + modality_result.get("messages", [])
        + target_result.get("warnings", [])
    )

    if not is_loaded or len(schema_errors) > 0 or len(target_result.get("errors", [])) > 0:
        status = "failed"
    elif all_warnings:
        status = "profiled_with_warning"
    else:
        status = "profiled"

    preview_rows = []
    if df is not None and not df.empty:
        preview_df = df.head(max_preview_rows)
        preview_rows = preview_df.fillna("").to_dict(orient="records")

    profile = {
        "dataset_profile_id": profile_id,
        "task_id": context["task_id"],
        "interpretation_id": context["interpretation_id"],
        "status": status,
        "dataset_source": dataset_source,
        "dataset_schema": dataset_schema,
        "modality_check": modality_check,
        "target_profile": target_profile,
        "data_quality": data_quality,
        "profiling_summary": profiling_summary,
        "workflow_planning_input": wf_input,
        "preview": {
            "columns": list(df.columns) if df is not None else [],
            "rows": preview_rows,
            "total_rows": n_samples,
            "preview_rows": len(preview_rows),
        },
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    return profile
