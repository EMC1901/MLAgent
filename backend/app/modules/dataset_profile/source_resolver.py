from typing import Optional


def resolve_source(
    dataset_intent: dict,
    dataset_description: Optional[str] = None,
    uploaded_file_id: Optional[str] = None,
    uploaded_file_path: Optional[str] = None,
) -> dict:
    """Determine the dataset source type and loader from upstream context."""

    if uploaded_file_id or uploaded_file_path:
        return {
            "source_type": "uploaded_file",
            "dataset_reference": uploaded_file_path or uploaded_file_id,
            "loader_name": "file",
            "is_supported": True,
            "requires_file_upload": True,
            "file_id": uploaded_file_id,
            "file_path": uploaded_file_path,
            "messages": [],
        }

    loading_hint = dataset_intent.get("dataset_loading_hint") or {}
    hint_source_type = loading_hint.get("source_type")

    if hint_source_type == "public_benchmark":
        return {
            "source_type": "public_benchmark",
            "dataset_reference": dataset_intent.get("dataset_reference"),
            "loader_name": loading_hint.get("possible_loader", "matbench"),
            "is_supported": True,
            "requires_file_upload": False,
            "messages": [],
        }

    if hint_source_type:
        return {
            "source_type": hint_source_type,
            "dataset_reference": dataset_intent.get("dataset_reference"),
            "loader_name": loading_hint.get("possible_loader"),
            "is_supported": hint_source_type in ("public_benchmark", "uploaded_file"),
            "requires_file_upload": hint_source_type == "uploaded_file",
            "messages": (
                []
                if hint_source_type in ("public_benchmark", "uploaded_file")
                else [f"Source type '{hint_source_type}' is not yet supported in MVP."]
            ),
        }

    dataset_ref = dataset_intent.get("dataset_reference", "")
    desc = dataset_description or ""

    if "matbench" in str(dataset_ref).lower() or "matbench" in desc.lower():
        return {
            "source_type": "public_benchmark",
            "dataset_reference": dataset_intent.get("dataset_reference"),
            "loader_name": "matbench",
            "is_supported": True,
            "requires_file_upload": False,
            "messages": [],
        }

    if any(kw in desc.lower() for kw in ("csv", "xlsx", "excel", "file", "upload")):
        return {
            "source_type": "uploaded_file",
            "dataset_reference": None,
            "loader_name": "file",
            "is_supported": True,
            "requires_file_upload": True,
            "messages": ["Inferred uploaded_file from dataset description."],
        }

    return {
        "source_type": "unknown",
        "dataset_reference": dataset_intent.get("dataset_reference"),
        "loader_name": None,
        "is_supported": False,
        "requires_file_upload": False,
        "messages": ["Unable to determine dataset source from provided information."],
    }
