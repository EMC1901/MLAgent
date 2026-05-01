import logging
import pandas as pd
import numpy as np

from app.modules.dataset_profile.loaders.base_loader import BaseLoader

logger = logging.getLogger(__name__)

# Known Matbench dataset schemas for generating sample data when matbench is not installed
_KNOWN_DATASETS = {
    "matbench_expt_gap": {
        "columns": ["composition", "band_gap"],
        "target": "band_gap",
        "n_samples": 4604,
    },
    "matbench_mp_e_form": {
        "columns": ["composition", "formation_energy"],
        "target": "formation_energy",
        "n_samples": 132752,
    },
    "matbench_log_gvrh": {
        "columns": ["composition", "log10_G_VRH"],
        "target": "log10_G_VRH",
        "n_samples": 10987,
    },
    "matbench_log_kvrh": {
        "columns": ["composition", "log10_K_VRH"],
        "target": "log10_K_VRH",
        "n_samples": 10987,
    },
}


class MatbenchLoader(BaseLoader):

    def loader_name(self) -> str:
        return "matbench"

    def load(self, context: dict, source_resolution: dict) -> tuple:
        dataset_ref = source_resolution.get("dataset_reference", "")

        try:
            from matbench import MatbenchBenchmark
            return self._load_from_matbench(dataset_ref)
        except ImportError:
            logger.warning(
                "matbench package not installed; using sample data for %s", dataset_ref
            )
            return self._load_sample(dataset_ref)

    def _load_from_matbench(self, dataset_ref: str) -> tuple:
        from matbench import MatbenchBenchmark

        mb = MatbenchBenchmark()
        found = None
        for ds in mb.datasets:
            if ds.name == dataset_ref:
                found = ds
                break

        if found is None:
            available = [ds.name for ds in mb.datasets]
            return None, {
                "is_loaded": False,
                "loader_name": "matbench",
                "dataset_reference": dataset_ref,
                "load_messages": [
                    f"Dataset '{dataset_ref}' not found in matbench. "
                    f"Available: {available[:10]}"
                ],
            }

        found.load()
        df = found.data
        if df is None:
            return None, {
                "is_loaded": False,
                "loader_name": "matbench",
                "dataset_reference": dataset_ref,
                "load_messages": [f"Dataset '{dataset_ref}' returned None from matbench."],
            }

        return df, {
            "is_loaded": True,
            "loader_name": "matbench",
            "dataset_reference": dataset_ref,
            "n_rows": len(df),
            "n_columns": len(df.columns),
            "columns": list(df.columns),
            "load_messages": [],
        }

    def _load_sample(self, dataset_ref: str) -> tuple:
        info = _KNOWN_DATASETS.get(dataset_ref)
        if info is None:
            return None, {
                "is_loaded": False,
                "loader_name": "matbench",
                "dataset_reference": dataset_ref,
                "load_messages": [
                    f"Unknown dataset '{dataset_ref}'. Known: {list(_KNOWN_DATASETS.keys())}"
                ],
            }

        n = min(info["n_samples"], 200)
        data = {}
        for col in info["columns"]:
            if col == info["target"]:
                data[col] = np.random.uniform(0, 12, n)
            else:
                data[col] = [f"Sample{i}" for i in range(n)]

        df = pd.DataFrame(data)
        logger.info("Generated %d sample rows for %s", n, dataset_ref)

        return df, {
            "is_loaded": True,
            "loader_name": "matbench",
            "dataset_reference": dataset_ref,
            "n_rows": n,
            "n_columns": len(df.columns),
            "columns": list(df.columns),
            "load_messages": ["Loaded sample data (matbench package not installed)."],
        }
