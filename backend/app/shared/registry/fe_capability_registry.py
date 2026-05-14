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
        known_limitations=["May generate correlated features", "Requires at least 3 numeric columns"],
        fallback_capability_ids=["descriptor_numeric_basic"],
        version="1.0.0",
    ),

    # ---- Hybrid / Metadata ----
    FECapabilitySpec(
        capability_id="hybrid_composition_descriptor_fusion",
        display_name="Composition-Descriptor Fusion Features",
        status="available",
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
        version="1.0.0",
    ),

    # ---- Planned/Future Capabilities ----
    FECapabilitySpec(
        capability_id="composition_magpie_features",
        display_name="Magpie Composition Features (matminer-based)",
        status="planned",
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
