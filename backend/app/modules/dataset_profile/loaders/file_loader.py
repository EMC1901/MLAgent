import os
import logging
import pandas as pd

from app.modules.dataset_profile.loaders.base_loader import BaseLoader
from app.shared.config.settings import settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


class FileLoader(BaseLoader):

    def loader_name(self) -> str:
        return "file"

    def load(self, context: dict, source_resolution: dict) -> tuple:
        file_path = source_resolution.get("file_path")
        file_id = source_resolution.get("file_id")

        if not file_path and not file_id:
            return None, {
                "is_loaded": False,
                "loader_name": "file",
                "load_messages": ["No file path or file ID provided."],
            }

        if file_path:
            path = file_path
        elif file_id:
            upload_dir = settings.DATASET_UPLOAD_DIR
            # file_id may include the extension, e.g. "file_a1b2c3d4.csv"
            path = os.path.join(upload_dir, file_id)
            if not os.path.exists(path):
                # Try looking for any file starting with this file_id prefix
                if os.path.isdir(upload_dir):
                    for fname in os.listdir(upload_dir):
                        if fname.startswith(file_id):
                            path = os.path.join(upload_dir, fname)
                            break
                    else:
                        return None, {
                            "is_loaded": False,
                            "loader_name": "file",
                            "dataset_reference": file_id,
                            "load_messages": [
                                f"Uploaded file '{file_id}' not found in {upload_dir}."
                            ],
                        }
                else:
                    return None, {
                        "is_loaded": False,
                        "loader_name": "file",
                        "dataset_reference": file_id,
                        "load_messages": [
                            f"Upload directory {upload_dir} does not exist."
                        ],
                    }
        else:
            path = None

        if not os.path.exists(path):
            return None, {
                "is_loaded": False,
                "loader_name": "file",
                "dataset_reference": path,
                "load_messages": [f"File not found: {path}"],
            }

        ext = os.path.splitext(path)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return None, {
                "is_loaded": False,
                "loader_name": "file",
                "dataset_reference": path,
                "load_messages": [
                    f"Unsupported file format '{ext}'. Allowed: {ALLOWED_EXTENSIONS}"
                ],
            }

        file_size_mb = os.path.getsize(path) / (1024 * 1024)
        if file_size_mb > settings.DATASET_MAX_FILE_SIZE_MB:
            return None, {
                "is_loaded": False,
                "loader_name": "file",
                "dataset_reference": path,
                "load_messages": [
                    f"File size {file_size_mb:.1f}MB exceeds limit of {settings.DATASET_MAX_FILE_SIZE_MB}MB."
                ],
            }

        try:
            if ext == ".csv":
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
        except Exception as e:
            logger.error("Failed to read file %s: %s", path, str(e))
            return None, {
                "is_loaded": False,
                "loader_name": "file",
                "dataset_reference": path,
                "load_messages": [f"Failed to read file: {str(e)}"],
            }

        if df.empty:
            return None, {
                "is_loaded": False,
                "loader_name": "file",
                "dataset_reference": path,
                "load_messages": ["File is empty (no data rows)."],
            }

        return df, {
            "is_loaded": True,
            "loader_name": "file",
            "source_type": "uploaded_file",
            "file_name": os.path.basename(path),
            "dataset_reference": path,
            "n_rows": len(df),
            "n_columns": len(df.columns),
            "columns": list(df.columns),
            "load_messages": [],
        }
