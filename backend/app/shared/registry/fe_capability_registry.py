"""
Feature Engineering Capability Registry.

Defines the complete set of FE capabilities that Workflow Planning
can reference when building a capability-aware FeatureStrategy.

Each capability includes material-science-specific metadata,
input modality requirements, estimated cost, known limitations,
and fallback mappings.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class FECapabilitySpec(BaseModel):
    capability_id: str
    display_name: str
    status: str  # available | planned | disabled | experimental
    feature_family: str  # composition | structure | descriptor | hybrid | metadata
    input_modalities: List[str] = []
    supported_task_types: List[str] = ["regression", "classification"]
    required_input_columns: List[str] = []
    optional_input_columns: List[str] = []
    output_feature_groups: List[str] = []
    material_use_cases: List[str] = []
    dependencies: List[str] = []
    estimated_cost: str = "low"  # low | medium | high
    known_limitations: List[str] = []
    fallback_capability_ids: List[str] = []
    featurizer_ids: List[str] = []
    version: str = "1.0.0"


# ---- Full Capability Registry ----

FEATURE_ENGINEERING_CAPABILITIES: List[FECapabilitySpec] = [
    # ---- Composition Features ----
    FECapabilitySpec(
        capability_id="composition_elemental_statistics",
        display_name="Elemental Property Statistics (composition-based)",
        status="available",
        feature_family="composition",
        input_modalities=["composition"],
        supported_task_types=["regression", "classification"],
        required_input_columns=["formula"],
        optional_input_columns=[],
        output_feature_groups=["composition_elemental_statistics"],
        material_use_cases=["formation_energy", "band_gap", "elasticity", "stability"],
        dependencies=["pymatgen", "matminer"],
        estimated_cost="medium",
        known_limitations=["Requires valid chemical formulas", "Limited for multi-element compounds > 5 elements"],
        fallback_capability_ids=["descriptor_numeric_basic"],
        featurizer_ids=["basic_composition", "matminer_element_property"],
        version="1.0.0",
    ),
    FECapabilitySpec(
        capability_id="composition_stoichiometry",
        display_name="Stoichiometry Features (fractional compositions)",
        status="available",
        feature_family="composition",
        input_modalities=["composition"],
        supported_task_types=["regression", "classification"],
        required_input_columns=["formula"],
        optional_input_columns=[],
        output_feature_groups=["composition_stoichiometry"],
        material_use_cases=["formation_energy", "thermodynamic_stability", "phase_prediction"],
        dependencies=["pymatgen", "matminer"],
        estimated_cost="low",
        known_limitations=["Redundant for single-element systems"],
        fallback_capability_ids=["descriptor_numeric_basic"],
        featurizer_ids=["basic_composition", "matminer_stoichiometry"],
        version="1.0.0",
    ),
    FECapabilitySpec(
        capability_id="composition_oxidation_states",
        display_name="Oxidation State Features",
        status="available",
        feature_family="composition",
        input_modalities=["composition"],
        supported_task_types=["regression", "classification"],
        required_input_columns=["formula"],
        optional_input_columns=[],
        output_feature_groups=["composition_oxidation_states"],
        material_use_cases=["formation_energy", "stability", "redox_potential"],
        dependencies=["pymatgen", "matminer"],
        estimated_cost="medium",
        known_limitations=["Assumes common oxidation states", "May miss exotic valence states"],
        fallback_capability_ids=["composition_elemental_statistics"],
        featurizer_ids=["matminer_oxidation_states"],
        version="1.0.0",
    ),
    FECapabilitySpec(
        capability_id="composition_ionic_compound_features",
        display_name="Ionic Compound Features (electronegativity, ionic radii)",
        status="available",
        feature_family="composition",
        input_modalities=["composition"],
        supported_task_types=["regression", "classification"],
        required_input_columns=["formula"],
        optional_input_columns=[],
        output_feature_groups=["composition_ionic_compound"],
        material_use_cases=["formation_energy", "band_gap", "dielectric_constant"],
        dependencies=["pymatgen", "matminer"],
        estimated_cost="medium",
        known_limitations=["Assumes ionic bonding character", "Less relevant for metallic systems"],
        fallback_capability_ids=["composition_elemental_statistics"],
        featurizer_ids=["matminer_ion_property"],
        version="1.0.0",
    ),
    FECapabilitySpec(
        capability_id="composition_band_center",
        display_name="Band Center Features",
        status="available",
        feature_family="composition",
        input_modalities=["composition"],
        supported_task_types=["regression"],
        required_input_columns=["formula"],
        optional_input_columns=[],
        output_feature_groups=["composition_band_center"],
        material_use_cases=["band_gap", "catalytic_activity", "formation_energy"],
        dependencies=["pymatgen", "matminer"],
        estimated_cost="medium",
        known_limitations=["Requires orbital energy data", "Less accurate for heavy elements"],
        fallback_capability_ids=["composition_elemental_statistics"],
        featurizer_ids=["matminer_band_center"],
        version="1.0.0",
    ),

    # ---- Structure Features ----
    FECapabilitySpec(
        capability_id="structure_basic_features",
        display_name="Basic Structure Features (density, volume, lattice params)",
        status="available",
        feature_family="structure",
        input_modalities=["structure"],
        supported_task_types=["regression", "classification"],
        required_input_columns=["structure"],
        optional_input_columns=[],
        output_feature_groups=["structure_basic"],
        material_use_cases=["elasticity", "thermal_expansion", "formation_energy"],
        dependencies=["pymatgen", "matminer"],
        estimated_cost="medium",
        known_limitations=["Requires CIF or POSCAR structure input", "Cannot handle disordered structures well"],
        fallback_capability_ids=["descriptor_numeric_basic"],
        featurizer_ids=["pymatgen_structure_parser", "matminer_structure_basic"],
        version="1.0.0",
    ),
    FECapabilitySpec(
        capability_id="structure_site_features",
        display_name="Site Fingerprints (coordination, neighbor distances)",
        status="available",
        feature_family="structure",
        input_modalities=["structure"],
        supported_task_types=["regression", "classification"],
        required_input_columns=["structure"],
        optional_input_columns=[],
        output_feature_groups=["structure_site"],
        material_use_cases=["band_gap", "formation_energy", "ionic_conductivity"],
        dependencies=["pymatgen", "matminer"],
        estimated_cost="high",
        known_limitations=["Computationally heavy for large supercells", "Requires site-specific information"],
        fallback_capability_ids=["structure_basic_features"],
        featurizer_ids=["matminer_site_stats"],
        version="1.0.0",
    ),
    FECapabilitySpec(
        capability_id="structure_density_features",
        display_name="Density and Packing Features",
        status="available",
        feature_family="structure",
        input_modalities=["structure"],
        supported_task_types=["regression", "classification"],
        required_input_columns=["structure"],
        optional_input_columns=[],
        output_feature_groups=["structure_density"],
        material_use_cases=["elasticity", "hardness", "thermal_conductivity"],
        dependencies=["pymatgen", "matminer"],
        estimated_cost="low",
        known_limitations=["Only meaningful for periodic structures"],
        fallback_capability_ids=["descriptor_numeric_basic"],
        featurizer_ids=["matminer_structure_basic"],
        version="1.0.0",
    ),

    # ---- Descriptor Features ----
    FECapabilitySpec(
        capability_id="descriptor_numeric_basic",
        display_name="Pre-computed Numeric Descriptors (basic pass-through)",
        status="available",
        feature_family="descriptor",
        input_modalities=["descriptor", "descriptor_table"],
        supported_task_types=["regression", "classification"],
        required_input_columns=[],
        optional_input_columns=[],
        output_feature_groups=["descriptor_numeric"],
        material_use_cases=["formation_energy", "band_gap", "elasticity", "generic_material_property"],
        dependencies=[],
        estimated_cost="low",
        known_limitations=["No new feature generation", "Relies on pre-existing descriptor columns"],
        fallback_capability_ids=[],
        featurizer_ids=["descriptor_passthrough", "descriptor_cleaner"],
        version="1.0.0",
    ),
    FECapabilitySpec(
        capability_id="descriptor_statistical_features",
        display_name="Statistical Features from Descriptors (rolling stats, ratios)",
        status="available",
        feature_family="descriptor",
        input_modalities=["descriptor", "descriptor_table"],
        supported_task_types=["regression", "classification"],
        required_input_columns=[],
        optional_input_columns=[],
        output_feature_groups=["descriptor_statistical"],
        material_use_cases=["formation_energy", "thermal_conductivity", "elasticity"],
        dependencies=["pandas"],
        estimated_cost="low",
        known_limitations=["May generate correlated features", "Requires at least 2 numeric columns"],
        fallback_capability_ids=["descriptor_numeric_basic"],
        featurizer_ids=["descriptor_statistical"],
        version="1.0.0",
    ),

    # ---- Hybrid / Metadata ----
    FECapabilitySpec(
        capability_id="hybrid_composition_descriptor_fusion",
        display_name="Composition-Descriptor Fusion Features",
        status="planned",
        feature_family="hybrid",
        input_modalities=["composition", "descriptor_table"],
        supported_task_types=["regression", "classification"],
        required_input_columns=["formula"],
        optional_input_columns=[],
        output_feature_groups=["hybrid_fusion"],
        material_use_cases=["formation_energy", "band_gap", "elasticity", "all_properties"],
        dependencies=["pymatgen", "matminer"],
        estimated_cost="high",
        known_limitations=["High feature count", "May introduce redundancy with separate composition + descriptor runs"],
        fallback_capability_ids=["composition_elemental_statistics", "descriptor_numeric_basic"],
        featurizer_ids=[],
        version="1.0.0",
    ),
    FECapabilitySpec(
        capability_id="metadata_feature_extractor",
        display_name="Metadata Column Extractor (experimental parameters)",
        status="available",
        feature_family="metadata",
        input_modalities=["composition", "structure", "descriptor_table"],
        supported_task_types=["regression", "classification"],
        required_input_columns=[],
        optional_input_columns=[],
        output_feature_groups=["metadata"],
        material_use_cases=["any_property_with_experimental_metadata"],
        dependencies=[],
        estimated_cost="low",
        known_limitations=["Only extracts existing metadata columns", "No synthesis of new metadata features"],
        fallback_capability_ids=[],
        featurizer_ids=["metadata_feature_extractor"],
        version="1.0.0",
    ),

    # ---- Planned/Future Capabilities ----
    FECapabilitySpec(
        capability_id="composition_magpie_features",
        display_name="Magpie Composition Features (matminer-based)",
        status="available",
        feature_family="composition",
        input_modalities=["composition"],
        supported_task_types=["regression", "classification"],
        required_input_columns=["formula"],
        optional_input_columns=[],
        output_feature_groups=["composition_magpie"],
        material_use_cases=["formation_energy", "band_gap", "elasticity"],
        dependencies=["matminer"],
        estimated_cost="medium",
        known_limitations=["Requires matminer >= 0.7.0"],
        fallback_capability_ids=["composition_elemental_statistics"],
        featurizer_ids=["matminer_magpie"],
        version="1.0.0",
    ),
    FECapabilitySpec(
        capability_id="composition_valence_orbital",
        display_name="Valence Orbital Composition Features",
        status="available",
        feature_family="composition",
        input_modalities=["composition"],
        supported_task_types=["regression", "classification"],
        required_input_columns=["formula"],
        optional_input_columns=[],
        output_feature_groups=["composition_valence_orbital"],
        material_use_cases=["formation_energy", "band_gap", "elasticity"],
        dependencies=["matminer"],
        estimated_cost="medium",
        known_limitations=["Requires matminer >= 0.7.0"],
        fallback_capability_ids=["composition_elemental_statistics"],
        featurizer_ids=["matminer_valence_orbital"],
        version="1.0.0",
    ),
    FECapabilitySpec(
        capability_id="graph_neural_network_embeddings",
        display_name="Graph Neural Network Embeddings (Crystal Graph)",
        status="planned",
        feature_family="structure",
        input_modalities=["structure"],
        supported_task_types=["regression", "classification"],
        required_input_columns=["structure"],
        optional_input_columns=[],
        output_feature_groups=["gnn_embeddings"],
        material_use_cases=["formation_energy", "band_gap", "elasticity", "all_properties"],
        dependencies=["torch", "dgl"],
        estimated_cost="high",
        known_limitations=["Requires GPU for practical use", "Large model dependency footprint"],
        fallback_capability_ids=[],
        featurizer_ids=[],
        version="1.0.0",
    ),
]

# Fast lookup by capability_id
CAPABILITY_BY_ID: Dict[str, FECapabilitySpec] = {
    c.capability_id: c for c in FEATURE_ENGINEERING_CAPABILITIES
}


def get_available_fe_capabilities(
    input_modality: Optional[str] = None,
    task_type: Optional[str] = None,
    feature_family: Optional[str] = None,
) -> List[FECapabilitySpec]:
    """Return FE capabilities with status='available', optionally filtered."""
    result = [c for c in FEATURE_ENGINEERING_CAPABILITIES if c.status == "available"]
    if input_modality:
        result = [c for c in result if input_modality in c.input_modalities]
    if task_type:
        result = [c for c in result if task_type in c.supported_task_types]
    if feature_family:
        result = [c for c in result if c.feature_family == feature_family]
    return result


def get_all_fe_capabilities(
    input_modality: Optional[str] = None,
    task_type: Optional[str] = None,
    status: Optional[str] = None,
) -> List[FECapabilitySpec]:
    """Return all FE capabilities, with optional filters."""
    result = list(FEATURE_ENGINEERING_CAPABILITIES)
    if input_modality:
        result = [c for c in result if input_modality in c.input_modalities]
    if task_type:
        result = [c for c in result if task_type in c.supported_task_types]
    if status:
        result = [c for c in result if c.status == status]
    return result


def get_fe_capability_by_id(capability_id: str) -> Optional[FECapabilitySpec]:
    """Look up a single FE capability by its ID."""
    return CAPABILITY_BY_ID.get(capability_id)


def resolve_capability_to_featurizers(capability_id: str) -> List[str]:
    """Return the list of featurizer_ids that implement a given capability.

    Returns an empty list if the capability is not found or has no mapped featurizers.
    """
    cap = CAPABILITY_BY_ID.get(capability_id)
    if cap is None:
        return []
    return cap.featurizer_ids


def get_executable_fe_capabilities(
    input_modality: Optional[str] = None,
    task_type: Optional[str] = None,
    feature_family: Optional[str] = None,
) -> List[FECapabilitySpec]:
    """Return FE capabilities that have at least one available featurizer mapped.

    Stricter than get_available_fe_capabilities -- filters out capabilities
    marked 'available' that have no executable featurizer implementations.
    """
    from app.shared.registry.featurizer_registry import (
        get_featurizer_by_id,
        get_featurizer_effective_status,
    )

    result = []
    for c in FEATURE_ENGINEERING_CAPABILITIES:
        if c.status != "available":
            continue
        if not c.featurizer_ids:
            continue
        any_available = False
        for fid in c.featurizer_ids:
            spec = get_featurizer_by_id(fid)
            if spec and get_featurizer_effective_status(spec) == "available":
                if input_modality and input_modality not in spec.input_modalities:
                    continue
                if task_type and task_type not in c.supported_task_types:
                    continue
                if feature_family and c.feature_family != feature_family:
                    continue
                any_available = True
                break
        if not any_available:
            continue
        if input_modality and input_modality not in c.input_modalities:
            continue
        if task_type and task_type not in c.supported_task_types:
            continue
        if feature_family and c.feature_family != feature_family:
            continue
        result.append(c)
    return result


def get_registry_snapshot() -> Dict[str, Any]:
    """Return a lightweight snapshot for persistence in WorkflowPlan."""
    import datetime
    return {
        "snapshot_version": "1.0.0",
        "created_at": datetime.datetime.now().isoformat(),
        "total_capabilities": len(FEATURE_ENGINEERING_CAPABILITIES),
        "available_count": len([c for c in FEATURE_ENGINEERING_CAPABILITIES if c.status == "available"]),
        "planned_count": len([c for c in FEATURE_ENGINEERING_CAPABILITIES if c.status == "planned"]),
        "capabilities": [c.model_dump() for c in FEATURE_ENGINEERING_CAPABILITIES],
    }
