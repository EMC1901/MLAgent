"""Matminer-based composition featurizers.

Each featurizer wraps a matminer featurizer class and handles:
  - Dependency detection (pymatgen + matminer)
  - Composition column discovery and parsing
  - Column prefixing: {featurizer_id}__{original_name}
  - Per-sample failure tracking
  - Execution time measurement

When dependencies are missing, featurizers return 'unavailable' status.
"""
import logging
import time
import pandas as pd
import numpy as np
from app.modules.feature_engineering.featurizers.base_featurizer import BaseFeaturizer

logger = logging.getLogger(__name__)

try:
    from pymatgen.core import Composition
    _PYMATGEN_AVAILABLE = True
except ImportError:
    _PYMATGEN_AVAILABLE = False
    Composition = None

try:
    import matminer
    _MATMINER_AVAILABLE = True
    _MATMINER_VERSION = getattr(matminer, "__version__", "unknown")
except ImportError:
    _MATMINER_AVAILABLE = False
    _MATMINER_VERSION = None

_DEPS_OK = _PYMATGEN_AVAILABLE and _MATMINER_AVAILABLE

# Lazy-loaded matminer featurizer classes
_MATMINER_FEATURIZERS = {}


def _get_matminer_featurizer(key):
    """Lazy-load a matminer featurizer class."""
    if key in _MATMINER_FEATURIZERS:
        return _MATMINER_FEATURIZERS[key]

    try:
        if key == "stoichiometry":
            from matminer.featurizers.composition import Stoichiometry
            cls = Stoichiometry
        elif key == "element_property":
            from matminer.featurizers.composition import ElementProperty
            cls = ElementProperty
        elif key == "magpie":
            from matminer.featurizers.composition import ElementProperty
            cls = ElementProperty
        elif key == "valence_orbital":
            from matminer.featurizers.composition import ValenceOrbital
            cls = ValenceOrbital
        else:
            return None
        _MATMINER_FEATURIZERS[key] = cls
        return cls
    except ImportError as e:
        logger.warning("Cannot import matminer featurizer '%s': %s", key, e)
        return None


def _find_composition_column(df, input_columns):
    """Find the composition column in the dataframe."""
    candidates = ["composition", "formula", "chemical_formula",
                  "material_formula", "pretty_formula"]
    for col in candidates:
        if col in df.columns:
            return col
    for col in (input_columns or []):
        if col in df.columns:
            return col
    return None


def _get_dependency_versions():
    versions = {}
    if _PYMATGEN_AVAILABLE:
        try:
            import pymatgen
            versions["pymatgen"] = getattr(pymatgen, "__version__", "unknown")
        except Exception:
            versions["pymatgen"] = "unknown"
    else:
        versions["pymatgen"] = "not_installed"
    if _MATMINER_AVAILABLE:
        versions["matminer"] = _MATMINER_VERSION or "unknown"
    else:
        versions["matminer"] = "not_installed"
    return versions


def _run_matminer_featurizer(
    featurizer_name,
    display_name,
    raw_dataframe,
    context,
    matminer_key,
    matminer_kwargs=None,
) -> dict:
    """Shared execution logic for all matminer composition featurizers."""
    start_time = time.time()
    dep_versions = _get_dependency_versions()

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

    FeaturizerClass = _get_matminer_featurizer(matminer_key)
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
            "errors": [f"matminer featurizer class '{matminer_key}' could not be loaded."],
        }

    data_context = context.get("data_context") or {}
    input_columns = data_context.get("input_columns", [])
    composition_col = _find_composition_column(raw_dataframe, input_columns)

    if composition_col is None:
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
            "errors": ["No composition column found in input data."],
        }

    # Parse compositions
    compositions = []
    failed = []
    for idx, val in raw_dataframe[composition_col].items():
        try:
            comp = Composition(str(val))
            compositions.append(comp)
        except Exception:
            compositions.append(None)
            failed.append(str(idx))

    n_failed = len(failed)
    n_total = len(raw_dataframe)

    # Build a DataFrame with the Composition objects (not raw strings)
    # This is critical: matminer expects Composition objects, not strings
    comp_series = pd.Series(compositions, index=raw_dataframe.index, name=composition_col)
    df_with_compositions = pd.DataFrame({composition_col: comp_series})

    # Instantiate and run the matminer featurizer
    kwargs = matminer_kwargs or {}
    try:
        featurizer = FeaturizerClass(**kwargs)
        feature_df = featurizer.featurize_dataframe(
            df_with_compositions,
            composition_col,
            ignore_errors=True,
        )
    except Exception as e:
        logger.error("matminer featurizer '%s' failed: %s", matminer_key, e)
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
            "errors": [f"matminer featurizer raised exception: {e}"],
        }

    # matminer returns a DataFrame with new feature columns (and possibly keeps the composition col)
    # Drop the composition column if it was kept
    if composition_col in feature_df.columns:
        feature_df = feature_df.drop(columns=[composition_col])

    # Prefix columns with featurizer_id to avoid conflicts
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
            f"{n_failed}/{n_total} composition parsing failures "
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


# ---------------------------------------------------------------------------
# Individual featurizer classes
# ---------------------------------------------------------------------------

class MatminerStoichiometryFeaturizer(BaseFeaturizer):

    def featurizer_name(self) -> str:
        return "matminer_stoichiometry"

    def featurize(self, raw_dataframe, context, resolved_strategy) -> dict:
        return _run_matminer_featurizer(
            featurizer_name=self.featurizer_name(),
            display_name="Matminer Stoichiometry Features",
            raw_dataframe=raw_dataframe,
            context=context,
            matminer_key="stoichiometry",
        )


class MatminerElementPropertyFeaturizer(BaseFeaturizer):

    def featurizer_name(self) -> str:
        return "matminer_element_property"

    def featurize(self, raw_dataframe, context, resolved_strategy) -> dict:
        return _run_matminer_featurizer(
            featurizer_name=self.featurizer_name(),
            display_name="Matminer ElementProperty Features",
            raw_dataframe=raw_dataframe,
            context=context,
            matminer_key="element_property",
            matminer_kwargs={
                "features": ["number", "mass", "density", "melting point",
                            "boiling point", "column", "row", "covalent radius",
                            "atomic radius", "atomic volume", "electronegativity",
                            "electron affinity", "first ionization", "heat of fusion",
                            "heat of vaporization", "polarizability"],
                "stats": ["mean", "std_dev", "minimum", "maximum", "range"],
                "data_source": "magpie",
            },
        )


class MatminerMagpieFeaturizer(BaseFeaturizer):

    def featurizer_name(self) -> str:
        return "matminer_magpie"

    def featurize(self, raw_dataframe, context, resolved_strategy) -> dict:
        return _run_matminer_featurizer(
            featurizer_name=self.featurizer_name(),
            display_name="Matminer Magpie Descriptors",
            raw_dataframe=raw_dataframe,
            context=context,
            matminer_key="magpie",
            matminer_kwargs={
                "features": ["number", "mass", "density", "melting point",
                            "boiling point", "column", "row", "covalent radius",
                            "atomic radius", "atomic volume", "electronegativity",
                            "electron affinity", "first ionization", "heat of fusion",
                            "heat of vaporization", "polarizability"],
                "stats": ["mean", "std_dev", "minimum", "maximum", "range"],
                "data_source": "magpie",
            },
        )


class MatminerValenceOrbitalFeaturizer(BaseFeaturizer):

    def featurizer_name(self) -> str:
        return "matminer_valence_orbital"

    def featurize(self, raw_dataframe, context, resolved_strategy) -> dict:
        return _run_matminer_featurizer(
            featurizer_name=self.featurizer_name(),
            display_name="Matminer ValenceOrbital Features",
            raw_dataframe=raw_dataframe,
            context=context,
            matminer_key="valence_orbital",
        )
