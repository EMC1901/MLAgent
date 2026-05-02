"""Pymatgen-based composition parser featurizer.

Parses chemical formula strings into pymatgen Composition objects, providing
standardized composition representation for downstream matminer featurizers.

When pymatgen is not installed, returns 'unavailable' status.
"""
import logging
import time
import pandas as pd
from app.modules.feature_engineering.featurizers.base_featurizer import BaseFeaturizer

logger = logging.getLogger(__name__)

try:
    from pymatgen.core import Composition
    _PYMATGEN_AVAILABLE = True
except ImportError:
    _PYMATGEN_AVAILABLE = False
    Composition = None


class PymatgenCompositionParserFeaturizer(BaseFeaturizer):

    def featurizer_name(self) -> str:
        return "pymatgen_composition_parser"

    def featurize(self, raw_dataframe, context, resolved_strategy) -> dict:
        start_time = time.time()
        dep_versions = {}

        if not _PYMATGEN_AVAILABLE:
            return {
                "status": "unavailable",
                "feature_dataframe": pd.DataFrame(index=raw_dataframe.index),
                "feature_columns": [],
                "executed_featurizers": [{
                    "name": self.featurizer_name(),
                    "display_name": "Pymatgen Composition Parser",
                    "status": "unavailable",
                    "n_features_generated": 0,
                    "failed_sample_count": 0,
                    "execution_time_ms": 0,
                    "dependency_versions": {},
                }],
                "failed_samples": [],
                "failed_sample_count": 0,
                "warnings": ["pymatgen not installed; composition parsing unavailable."],
                "errors": [],
            }

        try:
            import pymatgen
            dep_versions["pymatgen"] = getattr(pymatgen, "__version__", "unknown")
        except Exception:
            dep_versions["pymatgen"] = "unknown"

        data_context = context.get("data_context") or {}
        input_columns = data_context.get("input_columns", [])
        composition_col = self._find_composition_column(raw_dataframe, input_columns)

        if composition_col is None:
            return {
                "status": "failed",
                "feature_dataframe": pd.DataFrame(index=raw_dataframe.index),
                "feature_columns": [],
                "executed_featurizers": [{
                    "name": self.featurizer_name(),
                    "display_name": "Pymatgen Composition Parser",
                    "status": "failed",
                    "n_features_generated": 0,
                    "failed_sample_count": len(raw_dataframe),
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    "dependency_versions": dep_versions,
                }],
                "failed_samples": list(raw_dataframe.index.astype(str)[:50]),
                "failed_sample_count": len(raw_dataframe),
                "warnings": [],
                "errors": [f"No composition column found. Input columns: {input_columns}"],
            }

        parsed = []
        failed = []
        for idx, val in raw_dataframe[composition_col].items():
            try:
                comp = Composition(str(val))
                parsed.append(comp)
            except Exception:
                parsed.append(None)
                failed.append(str(idx))

        n_failed = len(failed)
        n_total = len(raw_dataframe)

        elapsed_ms = int((time.time() - start_time) * 1000)
        warnings = []
        if n_failed > 0:
            warnings.append(
                f"{n_failed}/{n_total} composition parsing failures "
                f"({n_failed / max(n_total, 1) * 100:.1f}%)."
            )

        status = "success" if n_failed / max(n_total, 1) <= 0.2 else "failed"

        result_df = pd.DataFrame(index=raw_dataframe.index)
        result_df["_pymatgen_composition"] = parsed

        return {
            "status": status,
            "feature_dataframe": result_df,
            "feature_columns": ["_pymatgen_composition"],
            "executed_featurizers": [{
                "name": self.featurizer_name(),
                "display_name": "Pymatgen Composition Parser",
                "status": status,
                "n_features_generated": 1,
                "failed_sample_count": n_failed,
                "execution_time_ms": elapsed_ms,
                "dependency_versions": dep_versions,
            }],
            "failed_samples": failed[:50],
            "failed_sample_count": n_failed,
            "warnings": warnings,
            "errors": [],
        }

    def _find_composition_column(self, df, input_columns):
        """Find the composition column from the dataframe."""
        candidates = ["composition", "formula", "chemical_formula", "material_formula",
                      "pretty_formula", "reduced_formula", "cif", "structure"]
        for col in candidates:
            if col in df.columns:
                return col
        for col in input_columns:
            if col in df.columns:
                return col
        return None
