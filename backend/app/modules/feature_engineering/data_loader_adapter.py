import logging
import pandas as pd
from typing import Optional
from app.modules.dataset_profile.loaders.matbench_loader import MatbenchLoader
from app.modules.dataset_profile.loaders.file_loader import FileLoader
from app.modules.feature_engineering.exceptions import RawDataLoadException

logger = logging.getLogger(__name__)


def reload_raw_data(data_context: dict) -> tuple:
    """Reuse Dataset Profile loaders to reload the raw DataFrame.

    Returns (DataFrame, loading_summary_dict).
    """
    dataset_source = data_context.get("dataset_source") or {}
    source_type = dataset_source.get("source_type", "")

    if source_type == "public_benchmark":
        return _load_matbench(dataset_source)
    elif source_type == "uploaded_file":
        return _load_uploaded_file(dataset_source, data_context)
    else:
        raise RawDataLoadException(
            f"Unsupported data source type: '{source_type}'."
        )


def _load_matbench(dataset_source: dict) -> tuple:
    loader = MatbenchLoader()
    source_resolution = {
        "dataset_reference": dataset_source.get("dataset_reference", ""),
    }
    df, result = loader.load({}, source_resolution)

    if df is None or not result.get("is_loaded"):
        messages = result.get("load_messages", [])
        raise RawDataLoadException(
            f"Failed to load matbench dataset: {'; '.join(messages)}"
        )

    if isinstance(df, pd.DataFrame) and result.get("load_messages"):
        for msg in result["load_messages"]:
            if "sample" in msg.lower() or "not installed" in msg.lower():
                logger.warning("MatbenchLoader warning: %s", msg)

    loading_summary = {
        "is_loaded": True,
        "n_rows": len(df),
        "n_columns": len(df.columns),
        "columns": list(df.columns),
        "load_messages": result.get("load_messages", []),
    }

    return df, loading_summary


def _load_uploaded_file(dataset_source: dict, data_context: dict) -> tuple:
    loader = FileLoader()

    dataset_schema = data_context.get("dataset_schema") or {}
    source_resolution = {
        "file_id": dataset_source.get("file_id"),
        "file_path": dataset_source.get("file_path"),
    }

    context = {
        "dataset_schema": dataset_schema,
        "uploaded_file_id": dataset_source.get("file_id"),
        "uploaded_file_path": dataset_source.get("file_path"),
    }

    df, result = loader.load(context, source_resolution)

    if df is None or not result.get("is_loaded"):
        messages = result.get("load_messages", [])
        raise RawDataLoadException(
            f"Failed to load uploaded file: {'; '.join(messages)}"
        )

    loading_summary = {
        "is_loaded": True,
        "n_rows": len(df),
        "n_columns": len(df.columns),
        "columns": list(df.columns),
        "load_messages": result.get("load_messages", []),
    }

    return df, loading_summary
