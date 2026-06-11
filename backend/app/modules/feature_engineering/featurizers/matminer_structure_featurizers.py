"""Matminer-based structure featurizers.

Wraps structure-level matminer featurizers (density, site stats, symmetry, etc.)
that consume pymatgen Structure objects.
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

try:
    import matminer
    _MATMINER_AVAILABLE = True
    _MATMINER_VERSION = getattr(matminer, "__version__", "unknown")
except ImportError:
    _MATMINER_AVAILABLE = False
    _MATMINER_VERSION = None

_DEPS_OK = _PYMATGEN_AVAILABLE and _MATMINER_AVAILABLE

_STRUCTURE_FEATURIZERS = {}


def _get_default_site_featurizer():
    """Return a fresh default site featurizer instance for SiteStatsFingerprint."""
    from matminer.featurizers.site import AGNIFingerprints
    return AGNIFingerprints()


def _get_matminer_structure_featurizer(key):
    if key in _STRUCTURE_FEATURIZERS:
        return _STRUCTURE_FEATURIZERS[key]

    try:
        if key == "site_stats":
            from matminer.featurizers.structure.sites import SiteStatsFingerprint
            cls = SiteStatsFingerprint
        else:
            return None
        _STRUCTURE_FEATURIZERS[key] = cls
        return cls
    except ImportError as e:
        logger.warning("Cannot import matminer structure featurizer '%s': %s", key, e)
        return None


def _find_structure_column(df, input_columns):
    candidates = ["structure", "cif", "cif_string", "poscar",
                  "structure_str", "_pymatgen_structure"]
    for col in candidates:
        if col in df.columns:
            return col
    for col in (input_columns or []):
        if col in df.columns:
            return col
    return None


def _parse_structures(series, start_time):
    """Parse a series of values into pymatgen Structure objects."""
    structures = []
    failed = []
    for idx, val in series.items():
        try:
            struct = parse_structure_value(val)
            structures.append(struct)
        except Exception:
            structures.append(None)
            failed.append(str(idx))
    return structures, failed


def _run_matminer_structure_featurizer(
    featurizer_name,
    display_name,
    raw_dataframe,
    context,
    matminer_key,
    matminer_kwargs=None,
) -> dict:
    start_time = time.time()

    try:
        import pymatgen
        pymatgen_ver = getattr(pymatgen, "__version__", "unknown")
    except Exception:
        pymatgen_ver = "unknown"
    dep_versions = {
        "pymatgen": pymatgen_ver if _PYMATGEN_AVAILABLE else "not_installed",
        "matminer": _MATMINER_VERSION or "unknown" if _MATMINER_AVAILABLE else "not_installed",
    }

    if not _DEPS_OK:
        missing = []
        if not _PYMATGEN_AVAILABLE:
            missing.append("pymatgen")
        if not _MATMINER_AVAILABLE:
            missing.append("matminer")
        return {
            "status": "unavailable",
            "feature_dataframe": pd.DataFrame(index=raw_dataframe.index),
            "feature_columns": [],
            "executed_featurizers": [{
                "name": featurizer_name,
                "display_name": display_name,
                "status": "unavailable",
                "n_features_generated": 0,
                "failed_sample_count": 0,
                "execution_time_ms": 0,
                "dependency_versions": dep_versions,
            }],
            "failed_samples": [],
            "failed_sample_count": 0,
            "warnings": [f"Dependencies not installed: {', '.join(missing)}"],
            "errors": [],
        }

    FeaturizerClass = _get_matminer_structure_featurizer(matminer_key)
    if FeaturizerClass is None:
        return {
            "status": "failed",
            "feature_dataframe": pd.DataFrame(index=raw_dataframe.index),
            "feature_columns": [],
            "executed_featurizers": [{
                "name": featurizer_name,
                "display_name": display_name,
                "status": "failed",
                "n_features_generated": 0,
                "failed_sample_count": 0,
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "dependency_versions": dep_versions,
            }],
            "failed_samples": [],
            "failed_sample_count": 0,
            "warnings": [],
            "errors": [f"matminer structure featurizer class '{matminer_key}' could not be loaded."],
        }

    data_context = context.get("data_context") or {}
    input_columns = data_context.get("input_columns", [])
    structure_col = _find_structure_column(raw_dataframe, input_columns)

    if structure_col is None:
        return {
            "status": "failed",
            "feature_dataframe": pd.DataFrame(index=raw_dataframe.index),
            "feature_columns": [],
            "executed_featurizers": [{
                "name": featurizer_name,
                "display_name": display_name,
                "status": "failed",
                "n_features_generated": 0,
                "failed_sample_count": len(raw_dataframe),
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "dependency_versions": dep_versions,
            }],
            "failed_samples": list(raw_dataframe.index.astype(str)[:50]),
            "failed_sample_count": len(raw_dataframe),
            "warnings": [],
            "errors": ["No structure column found in input data."],
        }

    structures, failed = _parse_structures(raw_dataframe[structure_col], start_time)
    n_failed = len(failed)
    n_total = len(raw_dataframe)

    struct_series = pd.Series(structures, index=raw_dataframe.index, name=structure_col)
    df_with_structures = pd.DataFrame({structure_col: struct_series})

    kwargs = matminer_kwargs or {}
    try:
        featurizer = FeaturizerClass(**kwargs)
        feature_df = featurizer.featurize_dataframe(
            df_with_structures,
            structure_col,
            ignore_errors=True,
        )
    except Exception as e:
        logger.error("matminer structure featurizer '%s' failed: %s", matminer_key, e)
        return {
            "status": "failed",
            "feature_dataframe": pd.DataFrame(index=raw_dataframe.index),
            "feature_columns": [],
            "executed_featurizers": [{
                "name": featurizer_name,
                "display_name": display_name,
                "status": "failed",
                "n_features_generated": 0,
                "failed_sample_count": n_total,
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "dependency_versions": dep_versions,
            }],
            "failed_samples": list(raw_dataframe.index.astype(str)[:50]),
            "failed_sample_count": n_total,
            "warnings": [],
            "errors": [f"matminer structure featurizer raised exception: {e}"],
        }

    if structure_col in feature_df.columns:
        feature_df = feature_df.drop(columns=[structure_col])

    prefix = f"{featurizer_name}__"
    rename_map = {}
    for col in feature_df.columns:
        if not col.startswith(prefix):
            rename_map[col] = f"{prefix}{col}"
    if rename_map:
        feature_df = feature_df.rename(columns=rename_map)

    feature_columns = list(feature_df.columns)
    n_features = len(feature_columns)

    elapsed_ms = int((time.time() - start_time) * 1000)

    warnings = []
    if n_failed > 0:
        warnings.append(
            f"{n_failed}/{n_total} structure parsing failures "
            f"({n_failed / max(n_total, 1) * 100:.1f}%)."
        )

    failed_ratio = n_failed / max(n_total, 1)
    if failed_ratio > 0.2:
        status = "failed"
    elif n_features == 0:
        status = "failed"
    else:
        status = "success"

    return {
        "status": status,
        "feature_dataframe": feature_df,
        "feature_columns": feature_columns,
        "executed_featurizers": [{
            "name": featurizer_name,
            "display_name": display_name,
            "status": status,
            "n_features_generated": n_features,
            "failed_sample_count": n_failed,
            "execution_time_ms": elapsed_ms,
            "dependency_versions": dep_versions,
        }],
        "failed_samples": failed[:50],
        "failed_sample_count": n_failed,
        "warnings": warnings,
        "errors": [],
    }


class MatminerSiteStatsFeaturizer(BaseFeaturizer):

    def featurizer_name(self) -> str:
        return "matminer_site_stats"

    def featurize(self, raw_dataframe, context, resolved_strategy) -> dict:
        return _run_matminer_structure_featurizer(
            featurizer_name=self.featurizer_name(),
            display_name="Matminer SiteStats Features",
            raw_dataframe=raw_dataframe,
            context=context,
            matminer_key="site_stats",
            matminer_kwargs={"site_featurizer": _get_default_site_featurizer()},
        )
