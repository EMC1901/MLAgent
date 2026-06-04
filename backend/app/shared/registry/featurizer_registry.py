"""
Featurizer Registry — shared contract between Workflow Planning and Feature Engineering.

This is the **single source of truth** for what featurizers the system supports.
Both Workflow Planning (prompt/validator) and Feature Engineering (strategy resolver)
must query this registry rather than maintaining their own hard-coded lists.
"""
import logging
from typing import List, Optional, Dict

from app.shared.registry.schemas import (
    FeaturizerSpec,
    FeaturizerResolveResult,
    FeaturizerFallbackResult,
    DependencyCheckResult,
)
from app.shared.registry.exceptions import (
    FeaturizerNotFoundException,
    FeaturizerNotAvailableException,
    NoAvailableFeaturizerException,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dependency detection (run at import time)
# ---------------------------------------------------------------------------

def _check_dependency(package_name: str) -> DependencyCheckResult:
    """Try importing a package and return its status and version."""
    import_map = {
        "pymatgen": "pymatgen",
        "matminer": "matminer",
        "sklearn": "sklearn",
        "scikit-learn": "sklearn",
        "pyarrow": "pyarrow",
        "scipy": "scipy",
    }
    module_name = import_map.get(package_name, package_name)
    try:
        mod = __import__(module_name)
        version = getattr(mod, "__version__", None)
        if version is None:
            try:
                from importlib.metadata import version as get_version
                version = get_version(module_name)
            except Exception:
                version = "unknown"
        return DependencyCheckResult(status="installed", version=str(version))
    except ImportError:
        return DependencyCheckResult(status="not_installed", version=None)


# Cache dependency results at module level
_DEPENDENCY_CACHE: Dict[str, DependencyCheckResult] = {}

for _dep_name in ["pymatgen", "matminer", "scikit-learn", "pyarrow", "scipy"]:
    _DEPENDENCY_CACHE[_dep_name] = _check_dependency(_dep_name)

_pymatgen_ok = _DEPENDENCY_CACHE["pymatgen"].status == "installed"
_matminer_ok = _DEPENDENCY_CACHE["matminer"].status == "installed"
_matminer_full_ok = _pymatgen_ok and _matminer_ok

logger.info(
    "Dependency check: pymatgen=%s, matminer=%s → matminer_featurizers=%s",
    _DEPENDENCY_CACHE["pymatgen"].status,
    _DEPENDENCY_CACHE["matminer"].status,
    "available" if _matminer_full_ok else "unavailable",
)


def check_all_dependencies() -> dict:
    """Return dependency status for all tracked packages."""
    return {name: result.model_dump() for name, result in _DEPENDENCY_CACHE.items()}


# ---------------------------------------------------------------------------
# Static featurizer definitions
# ---------------------------------------------------------------------------

_FEATURIZERS: List[FeaturizerSpec] = [
    # ---- Core composition featurizers ----
    FeaturizerSpec(
        id="basic_composition",
        display_name="Basic Composition Descriptors",
        description="Generate lightweight composition-based descriptors from chemical formulas "
                    "using a built-in 103-element property table. Always available as fallback.",
        input_modalities=["composition"],
        feature_type="composition_descriptors",
        supported_task_types=["regression", "classification"],
        aliases=[
            "basic_composition",
            "composition_descriptors",
            "basic_composition_descriptors",
            "elemental_property_statistics",
            "stoichiometric_features",
            "composition_statistics",
            "formula_statistics",
        ],
        status="available",
        mvp_supported=True,
        requires_dependencies=[],
        dependency_status={},
        output_feature_kind="numeric",
        estimated_feature_count="16",
        fallback_priority=100,
    ),

    # ---- Pymatgen composition parser ----
    FeaturizerSpec(
        id="pymatgen_composition_parser",
        display_name="Pymatgen Composition Parser",
        description="Parse chemical formulas using pymatgen.core.Composition for standardized "
                    "composition representation. Required by all matminer-based featurizers.",
        input_modalities=["composition"],
        feature_type="composition_descriptors",
        supported_task_types=["regression", "classification"],
        aliases=[
            "pymatgen_composition_parser",
            "pymatgen_composition",
            "pymatgen_parser",
        ],
        status="available" if _pymatgen_ok else "planned",
        mvp_supported=_pymatgen_ok,
        requires_dependencies=["pymatgen"],
        dependency_status=_DEPENDENCY_CACHE["pymatgen"].model_dump(),
        output_feature_kind="structural",
        estimated_feature_count="0",
        fallback_priority=90,
    ),

    # ---- Matminer-based composition featurizers ----
    FeaturizerSpec(
        id="matminer_stoichiometry",
        display_name="Matminer Stoichiometry Features",
        description="Generate stoichiometric composition features (num_atoms, atomic fractions, etc.) "
                    "using matminer.featurizers.composition.Stoichiometry.",
        input_modalities=["composition"],
        feature_type="composition_descriptors",
        supported_task_types=["regression", "classification"],
        aliases=[
            "matminer_stoichiometry",
            "stoichiometry_features",
            "stoichiometry",
        ],
        status="available" if _matminer_full_ok else "planned",
        mvp_supported=_matminer_full_ok,
        requires_dependencies=["pymatgen", "matminer"],
        dependency_status={
            "pymatgen": _DEPENDENCY_CACHE["pymatgen"].model_dump(),
            "matminer": _DEPENDENCY_CACHE["matminer"].model_dump(),
        },
        output_feature_kind="numeric",
        estimated_feature_count="8",
        fallback_priority=80,
    ),
    FeaturizerSpec(
        id="matminer_element_property",
        display_name="Matminer ElementProperty Features",
        description="Generate 132 element property statistics features (mean, range, max, min, etc.) "
                    "using matminer.featurizers.composition.ElementProperty with Magpie preset.",
        input_modalities=["composition"],
        feature_type="composition_descriptors",
        supported_task_types=["regression", "classification"],
        aliases=[
            "matminer_element_property",
            "matminer_elementproperty",
            "element_property",
            "elementproperty",
        ],
        status="available" if _matminer_full_ok else "planned",
        mvp_supported=_matminer_full_ok,
        requires_dependencies=["pymatgen", "matminer"],
        dependency_status={
            "pymatgen": _DEPENDENCY_CACHE["pymatgen"].model_dump(),
            "matminer": _DEPENDENCY_CACHE["matminer"].model_dump(),
        },
        output_feature_kind="numeric",
        estimated_feature_count="132",
        fallback_priority=70,
    ),
    FeaturizerSpec(
        id="matminer_magpie",
        display_name="Matminer Magpie Descriptors",
        description="Generate 132 Magpie composition descriptors using matminer. "
                    "Now available when pymatgen and matminer are installed.",
        input_modalities=["composition"],
        feature_type="composition_descriptors",
        supported_task_types=["regression", "classification"],
        aliases=[
            "magpie",
            "magpie_descriptors",
            "matminer_magpie",
            "matminer_composition_features",
            "element_property_magpie",
        ],
        status="available" if _matminer_full_ok else "planned",
        mvp_supported=_matminer_full_ok,
        requires_dependencies=["matminer", "pymatgen"],
        dependency_status={
            "pymatgen": _DEPENDENCY_CACHE["pymatgen"].model_dump(),
            "matminer": _DEPENDENCY_CACHE["matminer"].model_dump(),
        },
        output_feature_kind="numeric",
        estimated_feature_count="132",
        fallback_priority=60,
    ),
    FeaturizerSpec(
        id="matminer_valence_orbital",
        display_name="Matminer ValenceOrbital Features",
        description="Generate valence orbital composition features using "
                    "matminer.featurizers.composition.ValenceOrbital.",
        input_modalities=["composition"],
        feature_type="composition_descriptors",
        supported_task_types=["regression", "classification"],
        aliases=[
            "matminer_valence_orbital",
            "valence_orbital",
            "matminer_valenceorbital",
        ],
        status="available" if _matminer_full_ok else "planned",
        mvp_supported=_matminer_full_ok,
        requires_dependencies=["pymatgen", "matminer"],
        dependency_status={
            "pymatgen": _DEPENDENCY_CACHE["pymatgen"].model_dump(),
            "matminer": _DEPENDENCY_CACHE["matminer"].model_dump(),
        },
        output_feature_kind="numeric",
        estimated_feature_count="4",
        fallback_priority=50,
    ),

    # ---- Descriptor featurizers ----
    FeaturizerSpec(
        id="descriptor_passthrough",
        display_name="Existing Descriptor Passthrough",
        description="Use existing numeric descriptor columns directly as features.",
        input_modalities=["descriptor"],
        feature_type="existing_descriptors",
        supported_task_types=["regression", "classification"],
        aliases=[
            "descriptor_passthrough",
            "existing_descriptors",
            "descriptor_features",
            "numeric_descriptors",
            "precomputed_descriptors",
        ],
        status="available",
        mvp_supported=True,
        requires_dependencies=[],
        dependency_status={},
        output_feature_kind="numeric",
        estimated_feature_count="variable",
        fallback_priority=100,
    ),
    FeaturizerSpec(
        id="descriptor_cleaner",
        display_name="Descriptor Cleaner",
        description="Enhanced descriptor cleaning: identify numeric columns, exclude non-feature "
                    "columns, drop all-NaN/constant columns, mark high-missing-ratio columns, "
                    "output feature group metadata.",
        input_modalities=["descriptor"],
        feature_type="existing_descriptors",
        supported_task_types=["regression", "classification"],
        aliases=[
            "descriptor_cleaner",
            "clean_descriptors",
            "descriptor_normalizer",
        ],
        status="available",
        mvp_supported=True,
        requires_dependencies=[],
        dependency_status={},
        output_feature_kind="numeric",
        estimated_feature_count="variable",
        fallback_priority=90,
    ),

    # ---- Structure featurizers ----
    FeaturizerSpec(
        id="structure_placeholder",
        display_name="Structure Featurizer Placeholder",
        description="Placeholder for future structure-based featurizers. Not yet executable.",
        input_modalities=["structure"],
        feature_type="structure_descriptors",
        supported_task_types=["regression", "classification"],
        aliases=[
            "structure_descriptors",
            "structure_features",
            "crystal_structure_descriptors",
        ],
        status="available",
        mvp_supported=True,
        requires_dependencies=["pymatgen", "matminer"],
        dependency_status={
            "pymatgen": _DEPENDENCY_CACHE["pymatgen"].model_dump(),
            "matminer": _DEPENDENCY_CACHE["matminer"].model_dump(),
        },
        output_feature_kind="numeric",
        estimated_feature_count="variable",
        fallback_priority=10,
    ),
    FeaturizerSpec(
        id="pymatgen_structure_parser",
        display_name="Pymatgen Structure Parser",
        description="Parse CIF/POSCAR/structure data strings into pymatgen Structure objects for downstream featurizers.",
        input_modalities=["structure"],
        feature_type="structure_descriptors",
        supported_task_types=["regression", "classification"],
        aliases=[
            "pymatgen_structure_parser",
            "pymatgen_structure",
            "structure_parser",
        ],
        status="available" if _pymatgen_ok else "planned",
        mvp_supported=_pymatgen_ok,
        requires_dependencies=["pymatgen"],
        dependency_status=_DEPENDENCY_CACHE["pymatgen"].model_dump(),
        output_feature_kind="structural",
        estimated_feature_count="0",
        fallback_priority=10,
    ),
    FeaturizerSpec(
        id="matminer_structure_basic",
        display_name="Matminer Basic Structure Features",
        description="Generate basic structure features: density, volume, n_sites, "
                    "lattice parameters, space group, packing fraction.",
        input_modalities=["structure"],
        feature_type="structure_descriptors",
        supported_task_types=["regression", "classification"],
        aliases=[
            "matminer_structure_basic",
            "structure_basic",
            "basic_structure",
        ],
        status="available" if _matminer_full_ok else "planned",
        mvp_supported=_matminer_full_ok,
        requires_dependencies=["pymatgen", "matminer"],
        dependency_status={
            "pymatgen": _DEPENDENCY_CACHE["pymatgen"].model_dump(),
            "matminer": _DEPENDENCY_CACHE["matminer"].model_dump(),
        },
        output_feature_kind="numeric",
        estimated_feature_count="10",
        fallback_priority=9,
    ),

    # ---- Matminer composition featurizers (new) ----
    FeaturizerSpec(
        id="matminer_oxidation_states",
        display_name="Matminer OxidationStates Features",
        description="Generate oxidation state probabilities for each element "
                    "using matminer.featurizers.composition.ion.OxidationStates.",
        input_modalities=["composition"],
        feature_type="composition_descriptors",
        supported_task_types=["regression", "classification"],
        aliases=["matminer_oxidation_states", "oxidation_states"],
        status="available" if _matminer_full_ok else "planned",
        mvp_supported=_matminer_full_ok,
        requires_dependencies=["pymatgen", "matminer"],
        dependency_status={
            "pymatgen": _DEPENDENCY_CACHE["pymatgen"].model_dump(),
            "matminer": _DEPENDENCY_CACHE["matminer"].model_dump(),
        },
        output_feature_kind="numeric",
        estimated_feature_count="variable",
        fallback_priority=40,
    ),
    FeaturizerSpec(
        id="matminer_ion_property",
        display_name="Matminer Ionic Compound Features",
        description="Generate ionic compound features (electronegativity, ionic radii) "
                    "using matminer.featurizers.composition.ion.IonProperty.",
        input_modalities=["composition"],
        feature_type="composition_descriptors",
        supported_task_types=["regression", "classification"],
        aliases=["matminer_ion_property", "ion_property", "ionic_compound"],
        status="available" if _matminer_full_ok else "planned",
        mvp_supported=_matminer_full_ok,
        requires_dependencies=["pymatgen", "matminer"],
        dependency_status={
            "pymatgen": _DEPENDENCY_CACHE["pymatgen"].model_dump(),
            "matminer": _DEPENDENCY_CACHE["matminer"].model_dump(),
        },
        output_feature_kind="numeric",
        estimated_feature_count="4",
        fallback_priority=40,
    ),
    FeaturizerSpec(
        id="matminer_band_center",
        display_name="Matminer BandCenter Features",
        description="Generate band center composition features "
                    "using matminer.featurizers.composition.element.BandCenter.",
        input_modalities=["composition"],
        feature_type="composition_descriptors",
        supported_task_types=["regression"],
        aliases=["matminer_band_center", "band_center"],
        status="available" if _matminer_full_ok else "planned",
        mvp_supported=_matminer_full_ok,
        requires_dependencies=["pymatgen", "matminer"],
        dependency_status={
            "pymatgen": _DEPENDENCY_CACHE["pymatgen"].model_dump(),
            "matminer": _DEPENDENCY_CACHE["matminer"].model_dump(),
        },
        output_feature_kind="numeric",
        estimated_feature_count="1",
        fallback_priority=40,
    ),

    # ---- Matminer structure featurizers (new) ----
    FeaturizerSpec(
        id="matminer_site_stats",
        display_name="Matminer SiteStats Features",
        description="Generate site-level structure statistics (coordination, bond lengths, etc.) "
                    "using matminer.featurizers.structure.sites.SiteStatsFingerprint.",
        input_modalities=["structure"],
        feature_type="structure_descriptors",
        supported_task_types=["regression", "classification"],
        aliases=["matminer_site_stats", "site_stats", "site_fingerprint"],
        status="available" if _matminer_full_ok else "planned",
        mvp_supported=_matminer_full_ok,
        requires_dependencies=["pymatgen", "matminer"],
        dependency_status={
            "pymatgen": _DEPENDENCY_CACHE["pymatgen"].model_dump(),
            "matminer": _DEPENDENCY_CACHE["matminer"].model_dump(),
        },
        output_feature_kind="numeric",
        estimated_feature_count="variable",
        fallback_priority=30,
    ),

    # ---- Pure-Python descriptor featurizers (new) ----
    FeaturizerSpec(
        id="descriptor_statistical",
        display_name="Statistical Descriptor Features",
        description="Generate pairwise ratios, products, and per-row summary statistics "
                    "from existing numeric descriptor columns. No external dependencies.",
        input_modalities=["descriptor"],
        feature_type="existing_descriptors",
        supported_task_types=["regression", "classification"],
        aliases=["descriptor_statistical", "statistical_features", "descriptor_stats"],
        status="available",
        mvp_supported=True,
        requires_dependencies=[],
        dependency_status={},
        output_feature_kind="numeric",
        estimated_feature_count="variable",
        fallback_priority=70,
    ),

    # ---- Metadata featurizer (new) ----
    FeaturizerSpec(
        id="metadata_feature_extractor",
        display_name="Metadata Column Extractor",
        description="Identify and extract experimental metadata columns (temperature, pressure, "
                    "synthesis method, etc.) as features. Converts low-cardinality categorical "
                    "metadata to one-hot encoding.",
        input_modalities=["descriptor", "composition", "structure"],
        feature_type="existing_descriptors",
        supported_task_types=["regression", "classification"],
        aliases=["metadata_feature_extractor", "metadata", "experimental_metadata"],
        status="available",
        mvp_supported=True,
        requires_dependencies=[],
        dependency_status={},
        output_feature_kind="mixed",
        estimated_feature_count="variable",
        fallback_priority=20,
    ),
]

# ---------------------------------------------------------------------------
# Indexes built once at import time
# ---------------------------------------------------------------------------

_id_index: Dict[str, FeaturizerSpec] = {}
_alias_index: Dict[str, str] = {}  # alias → canonical id

for _spec in _FEATURIZERS:
    _id_index[_spec.id] = _spec
    for _alias in _spec.aliases:
        existing = _alias_index.get(_alias)
        if existing and existing != _spec.id:
            logger.warning(
                "Alias '%s' mapped to '%s', but already mapped to '%s'. Using first mapping.",
                _alias, _spec.id, existing,
            )
            continue
        _alias_index[_alias] = _spec.id


# ---------------------------------------------------------------------------
# Effective status helpers
# ---------------------------------------------------------------------------

def get_featurizer_effective_status(spec: FeaturizerSpec) -> str:
    """Return the effective status of a featurizer considering dependency availability."""
    if spec.status in ("planned", "disabled", "deprecated"):
        return spec.status
    if spec.status == "available":
        for dep in spec.requires_dependencies:
            dep_result = _DEPENDENCY_CACHE.get(dep)
            if dep_result and dep_result.status == "not_installed":
                return "unavailable"
    return spec.status


def update_dependency_status() -> None:
    """Re-check and update dependency_status on all featurizer specs."""
    for spec in _FEATURIZERS:
        if not spec.requires_dependencies:
            spec.dependency_status = {}
            continue
        deps = {}
        for dep_name in spec.requires_dependencies:
            if dep_name in _DEPENDENCY_CACHE:
                deps[dep_name] = _DEPENDENCY_CACHE[dep_name].model_dump()
            else:
                deps[dep_name] = DependencyCheckResult(status="unknown").model_dump()
        spec.dependency_status = deps


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_all_featurizers() -> List[FeaturizerSpec]:
    """Return all registered featurizers (any status)."""
    return list(_FEATURIZERS)


def get_featurizer_by_id(featurizer_id: str) -> Optional[FeaturizerSpec]:
    """Look up a featurizer by its canonical id."""
    return _id_index.get(featurizer_id)


def get_available_featurizers(
    input_modality: Optional[str] = None,
    task_type: Optional[str] = None,
    feature_type: Optional[str] = None,
) -> List[FeaturizerSpec]:
    """Return featurizers, optionally filtered. Only returns truly available ones."""
    results = []
    for spec in _FEATURIZERS:
        eff = get_featurizer_effective_status(spec)
        if eff != "available":
            continue
        if input_modality and input_modality not in spec.input_modalities:
            continue
        if task_type and task_type not in spec.supported_task_types:
            continue
        if feature_type and spec.feature_type != feature_type:
            continue
        results.append(spec)
    return sorted(results, key=lambda s: -s.fallback_priority)


def get_featurizers_for_modality(input_modality: str) -> List[FeaturizerSpec]:
    """Return all featurizers (any status) that support a given input modality."""
    return [s for s in _FEATURIZERS if input_modality in s.input_modalities]


def resolve(name: str) -> FeaturizerResolveResult:
    """Resolve a featurizer name (id or alias) and return its resolution result."""
    spec = _id_index.get(name)
    if spec:
        return FeaturizerResolveResult(
            input_name=name,
            resolved_id=spec.id,
            matched_by="id",
            status=get_featurizer_effective_status(spec),
        )

    canonical_id = _alias_index.get(name)
    if canonical_id:
        spec = _id_index.get(canonical_id)
        if spec:
            return FeaturizerResolveResult(
                input_name=name,
                resolved_id=spec.id,
                matched_by="alias",
                status=get_featurizer_effective_status(spec),
            )

    return FeaturizerResolveResult(
        input_name=name,
        resolved_id=None,
        matched_by=None,
        status=None,
    )


def resolve_to_available(name: str, input_modality: str) -> FeaturizerResolveResult:
    """Resolve a name AND check it is available for the given modality."""
    result = resolve(name)

    if result.resolved_id is None:
        return result

    spec = _id_index.get(result.resolved_id)
    if spec is None:
        return result

    eff_status = get_featurizer_effective_status(spec)
    if eff_status != "available":
        return FeaturizerResolveResult(
            input_name=name,
            resolved_id=spec.id,
            matched_by=result.matched_by,
            status=eff_status,
        )

    if input_modality not in spec.input_modalities:
        return FeaturizerResolveResult(
            input_name=name,
            resolved_id=spec.id,
            matched_by=result.matched_by,
            status="modality_mismatch",
        )

    return result


def get_default_fallback(input_modality: str, task_type: Optional[str] = None) -> FeaturizerFallbackResult:
    """Return the highest-priority available featurizer for a modality."""
    candidates = get_available_featurizers(
        input_modality=input_modality,
        task_type=task_type,
    )
    if not candidates:
        return FeaturizerFallbackResult(
            fallback_featurizer_id=None,
            reason=f"No available featurizer for modality '{input_modality}'.",
        )

    best = candidates[0]
    return FeaturizerFallbackResult(
        fallback_featurizer_id=best.id,
        reason=f"Highest priority available {input_modality} featurizer (priority={best.fallback_priority}).",
    )


def get_planned_featurizers(input_modality: Optional[str] = None) -> List[FeaturizerSpec]:
    """Return featurizers with status='planned', optionally filtered."""
    results = []
    for spec in _FEATURIZERS:
        if spec.status != "planned":
            continue
        if input_modality and input_modality not in spec.input_modalities:
            continue
        results.append(spec)
    return results


def get_featurizers_requiring_dependency(dep_name: str) -> List[FeaturizerSpec]:
    """Return featurizers that require a specific dependency."""
    return [s for s in _FEATURIZERS if dep_name in s.requires_dependencies]


# ---------------------------------------------------------------------------
# Capability-to-featurizer resolution
# ---------------------------------------------------------------------------

def resolve_featurizers_from_capability_actions(
    selected_actions: list,
    input_modality: str,
) -> list:
    """Resolve selected_feature_actions (from LLM) to executable featurizer IDs.

    Each action should have 'action_id' and 'capability_id' keys.
    Uses the FE Capability Registry's featurizer_ids mapping to bridge the two registries.

    Returns a list of dicts with keys:
        action_id, capability_id, featurizer_id, status
    where status is one of: "resolved", "unavailable", "no_implementation"
    """
    from app.shared.registry.fe_capability_registry import resolve_capability_to_featurizers

    results = []
    for action in selected_actions:
        capability_id = action.get("capability_id", "")
        action_id = action.get("action_id", "")

        featurizer_ids = resolve_capability_to_featurizers(capability_id)

        if not featurizer_ids:
            results.append({
                "action_id": action_id,
                "capability_id": capability_id,
                "featurizer_id": None,
                "status": "no_implementation",
            })
            continue

        found = False
        for fid in featurizer_ids:
            spec = get_featurizer_by_id(fid)
            if spec is None:
                continue
            eff = get_featurizer_effective_status(spec)
            if eff == "available" and input_modality in spec.input_modalities:
                results.append({
                    "action_id": action_id,
                    "capability_id": capability_id,
                    "featurizer_id": fid,
                    "status": "resolved",
                })
                found = True
                break

        if not found:
            results.append({
                "action_id": action_id,
                "capability_id": capability_id,
                "featurizer_id": featurizer_ids[0] if featurizer_ids else None,
                "status": "unavailable",
            })

    return results


# ---------------------------------------------------------------------------
# Self-check (called at startup or in tests)
# ---------------------------------------------------------------------------

def validate_registry() -> List[str]:
    """Run self-consistency checks on the registry. Returns a list of issues."""
    issues = []

    seen_ids = set()
    for spec in _FEATURIZERS:
        if spec.id in seen_ids:
            issues.append(f"Duplicate featurizer id: '{spec.id}'")
        seen_ids.add(spec.id)

    alias_to_ids: Dict[str, list] = {}
    for spec in _FEATURIZERS:
        for alias in spec.aliases:
            if alias not in alias_to_ids:
                alias_to_ids[alias] = []
            alias_to_ids[alias].append(spec.id)

    for alias, ids in alias_to_ids.items():
        if len(ids) > 1:
            issues.append(f"Alias '{alias}' maps to multiple IDs: {ids}")

    valid_statuses = {"available", "planned", "disabled", "deprecated", "unavailable"}
    for spec in _FEATURIZERS:
        if spec.status not in valid_statuses:
            issues.append(f"Featurizer '{spec.id}' has invalid status '{spec.status}'")

    valid_modalities = {"composition", "descriptor", "structure", "text", "mixed"}
    for spec in _FEATURIZERS:
        for mod in spec.input_modalities:
            if mod not in valid_modalities:
                issues.append(f"Featurizer '{spec.id}' has invalid input_modality '{mod}'")

    for mod in ("composition", "descriptor"):
        avail = get_available_featurizers(input_modality=mod)
        if not avail:
            issues.append(f"No available featurizer for modality '{mod}'")

    return issues
