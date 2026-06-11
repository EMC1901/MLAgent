"""Matminer basic structure featurizer.

Generates basic structure features (density, volume, n_sites, lattice params,
space group, etc.) using pymatgen Structure objects.

Currently planned — returns 'unavailable' unless pymatgen is installed and
structure data is available in the input.
"""
import logging
import time
import pandas as pd
import numpy as np
from app.modules.feature_engineering.featurizers.base_featurizer import BaseFeaturizer
from app.modules.feature_engineering.featurizers.structure_parsing_utils import (
    parse_structure_value,
)

logger = logging.getLogger(__name__)

try:
    from pymatgen.core import Structure
    _PYMATGEN_AVAILABLE = True
except ImportError:
    _PYMATGEN_AVAILABLE = False
    Structure = None


class MatminerStructureBasicFeaturizer(BaseFeaturizer):

    def featurizer_name(self) -> str:
        return "matminer_structure_basic"

    def featurize(self, raw_dataframe, context, resolved_strategy) -> dict:
        start_time = time.time()

        if not _PYMATGEN_AVAILABLE:
            return {
                "status": "unavailable",
                "feature_dataframe": pd.DataFrame(index=raw_dataframe.index),
                "feature_columns": [],
                "executed_featurizers": [{
                    "name": self.featurizer_name(),
                    "display_name": "Matminer Basic Structure Features",
                    "status": "unavailable",
                    "n_features_generated": 0,
                    "failed_sample_count": 0,
                    "execution_time_ms": 0,
                    "dependency_versions": {"pymatgen": "not_installed"},
                }],
                "failed_samples": [],
                "failed_sample_count": 0,
                "warnings": ["pymatgen not installed; structure featurizer unavailable."],
                "errors": [],
            }

        data_context = context.get("data_context") or {}
        input_columns = data_context.get("input_columns", [])

        structure_col = self._find_structure_column(raw_dataframe, input_columns)
        if structure_col is None:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "skipped",
                "feature_dataframe": pd.DataFrame(index=raw_dataframe.index),
                "feature_columns": [],
                "executed_featurizers": [{
                    "name": self.featurizer_name(),
                    "display_name": "Matminer Basic Structure Features",
                    "status": "skipped",
                    "n_features_generated": 0,
                    "failed_sample_count": 0,
                    "execution_time_ms": elapsed_ms,
                    "dependency_versions": self._get_dep_versions(),
                }],
                "failed_samples": [],
                "failed_sample_count": 0,
                "warnings": ["No structure column or file found; structure featurizer skipped."],
                "errors": [],
            }

        features_list = []
        failed = []
        for idx, val in raw_dataframe[structure_col].items():
            try:
                struct = parse_structure_value(val)
                row_features = self._compute_basic_descriptors(struct)
                features_list.append(row_features)
            except Exception:
                features_list.append({})
                failed.append(str(idx))

        if not features_list or all(len(f) == 0 for f in features_list):
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "failed",
                "feature_dataframe": pd.DataFrame(index=raw_dataframe.index),
                "feature_columns": [],
                "executed_featurizers": [{
                    "name": self.featurizer_name(),
                    "display_name": "Matminer Basic Structure Features",
                    "status": "failed",
                    "n_features_generated": 0,
                    "failed_sample_count": len(raw_dataframe),
                    "execution_time_ms": elapsed_ms,
                    "dependency_versions": self._get_dep_versions(),
                }],
                "failed_samples": failed[:50],
                "failed_sample_count": len(failed),
                "warnings": [],
                "errors": ["All structure parsing attempts failed."],
            }

        feature_df = pd.DataFrame(features_list, index=raw_dataframe.index)
        feature_df = feature_df.fillna(0)

        prefix = f"{self.featurizer_name()}__"
        rename_map = {c: f"{prefix}{c}" for c in feature_df.columns}
        feature_df = feature_df.rename(columns=rename_map)
        feature_columns = list(feature_df.columns)

        n_failed = len(failed)
        n_total = len(raw_dataframe)
        elapsed_ms = int((time.time() - start_time) * 1000)

        status = "success" if n_failed / max(n_total, 1) <= 0.2 else "failed"

        return {
            "status": status,
            "feature_dataframe": feature_df,
            "feature_columns": feature_columns,
            "executed_featurizers": [{
                "name": self.featurizer_name(),
                "display_name": "Matminer Basic Structure Features",
                "status": status,
                "n_features_generated": len(feature_columns),
                "failed_sample_count": n_failed,
                "execution_time_ms": elapsed_ms,
                "dependency_versions": self._get_dep_versions(),
            }],
            "failed_samples": failed[:50],
            "failed_sample_count": n_failed,
            "warnings": [],
            "errors": [],
        }

    def _compute_basic_descriptors(self, struct) -> dict:
        """Compute basic structure descriptors from a pymatgen Structure."""
        descriptors = {}
        try:
            descriptors["density"] = float(struct.density)
        except Exception:
            descriptors["density"] = 0.0
        try:
            descriptors["volume"] = float(struct.volume)
        except Exception:
            descriptors["volume"] = 0.0
        try:
            descriptors["n_sites"] = len(struct)
        except Exception:
            descriptors["n_sites"] = 0
        try:
            descriptors["n_species"] = len(struct.composition.elements)
        except Exception:
            descriptors["n_species"] = 0
        try:
            lattice = struct.lattice
            descriptors["lattice_a"] = float(lattice.a)
            descriptors["lattice_b"] = float(lattice.b)
            descriptors["lattice_c"] = float(lattice.c)
            descriptors["lattice_alpha"] = float(lattice.alpha)
            descriptors["lattice_beta"] = float(lattice.beta)
            descriptors["lattice_gamma"] = float(lattice.gamma)
        except Exception:
            pass
        try:
            sg = struct.get_space_group_info()
            descriptors["space_group_number"] = float(sg[1]) if sg else 0.0
        except Exception:
            pass
        return descriptors

    def _find_structure_column(self, df, input_columns):
        candidates = ["structure", "cif", "structure_str", "structure_string",
                      "poscar", "structure_data"]
        for col in candidates:
            if col in df.columns:
                return col
        for col in (input_columns or []):
            if col in df.columns:
                return col
        return None

    def _get_dep_versions(self):
        versions = {}
        if _PYMATGEN_AVAILABLE:
            try:
                import pymatgen
                versions["pymatgen"] = getattr(pymatgen, "__version__", "unknown")
            except Exception:
                versions["pymatgen"] = "unknown"
        else:
            versions["pymatgen"] = "not_installed"
        return versions
