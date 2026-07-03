"""Phase 4: Material Semantics Registry.

Maps feature/descriptor names to material science concepts, mechanism families,
and physical interpretations.  Used by the mechanism mapper to ground descriptor
patterns in domain knowledge rather than keyword heuristics alone.

Priority chain (as defined in Phase4.md):
  feature_lineage.description
  > feature_lineage.category
  > material_semantics_registry
  > physics_rule_registry
  > keyword fallback
  > opaque descriptor
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MaterialSemanticRule:
    """A rule that maps feature name patterns to material science concepts."""
    feature_patterns: List[str]
    material_concept: str
    mechanism_family: str
    expected_role: str
    physical_interpretation: str
    typical_units: Optional[str] = None
    caveats: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Built-in rules covering common materials ML descriptors
# ---------------------------------------------------------------------------

_BUILTIN_RULES: List[MaterialSemanticRule] = [
    # -- composition --
    MaterialSemanticRule(
        feature_patterns=["mean_atomic_number", "avg_atomic_number"],
        material_concept="mean atomic number",
        mechanism_family="electronic_structure",
        expected_role="modulates electron count per atom",
        physical_interpretation="Higher mean atomic number implies heavier elements with more electrons, which can affect bonding character and electronic properties.",
        typical_units="dimensionless",
    ),
    MaterialSemanticRule(
        feature_patterns=["avg_electronegativity", "mean_electronegativity", "electronegativity_mean"],
        material_concept="average electronegativity",
        mechanism_family="bonding_strength",
        expected_role="captures overall bond polarity tendency",
        physical_interpretation="Average electronegativity reflects the overall tendency of constituent atoms to attract electrons, influencing bond ionicity and stability.",
        typical_units="Pauling scale",
    ),
    MaterialSemanticRule(
        feature_patterns=["electronegativity_diff", "electronegativity_difference", "chi_diff"],
        material_concept="electronegativity contrast",
        mechanism_family="bonding_strength",
        expected_role="quantifies bond polarity / charge transfer driving force",
        physical_interpretation="Larger electronegativity differences drive charge transfer and ionic character. Moderate contrasts may balance ionic and covalent contributions.",
        typical_units="Pauling scale",
        caveats=["Electronegativity contrast alone does not determine bond type; atomic radii and valence also matter."],
    ),
    MaterialSemanticRule(
        feature_patterns=["atomic_radius", "avg_atomic_radius", "mean_atomic_radius"],
        material_concept="atomic size",
        mechanism_family="lattice_distortion",
        expected_role="determines atomic packing and lattice parameter scaling",
        physical_interpretation="Atomic radius controls interatomic distances and packing efficiency. Mismatched radii cause lattice strain.",
        typical_units="pm or Å",
    ),
    MaterialSemanticRule(
        feature_patterns=["atomic_volume", "molar_volume"],
        material_concept="atomic / molar volume",
        mechanism_family="lattice_distortion",
        expected_role="proxies for packing density and free volume",
        physical_interpretation="Larger atomic volumes reduce packing density and may indicate softer lattice or higher compressibility.",
        typical_units="Å³ or cm³/mol",
    ),
    MaterialSemanticRule(
        feature_patterns=["valence_electron", "valence_electron_count", "vec"],
        material_concept="valence electron concentration",
        mechanism_family="electronic_structure",
        expected_role="governs bonding electron count and band filling",
        physical_interpretation="VEC influences the Fermi level position and bonding/antibonding orbital occupation, affecting phase stability and mechanical properties.",
        typical_units="electrons/atom",
    ),
    MaterialSemanticRule(
        feature_patterns=["fraction_"],
        material_concept="compositional fraction",
        mechanism_family="composition_complexity",
        expected_role="controls stoichiometry and multi-element effects",
        physical_interpretation="Elemental fractions define the composition space. Near-equimolar fractions may indicate high-entropy effects; dominant fractions approach binary/ternary limits.",
    ),

    # -- structure --
    MaterialSemanticRule(
        feature_patterns=["density", "mass_density"],
        material_concept="mass density",
        mechanism_family="lattice_distortion",
        expected_role="integrates atomic mass and packing",
        physical_interpretation="Density combines atomic mass and structural compactness. Higher density often correlates with closer packing and higher coordination.",
        typical_units="g/cm³",
    ),
    MaterialSemanticRule(
        feature_patterns=["volume", "cell_volume", "unit_cell_volume"],
        material_concept="unit cell volume",
        mechanism_family="lattice_distortion",
        expected_role="reflects lattice expansion/contraction",
        physical_interpretation="Cell volume integrates atomic sizes, bonding, and temperature effects. Volume changes can signal phase transitions or compositional expansion.",
        typical_units="Å³",
    ),
    MaterialSemanticRule(
        feature_patterns=["lattice_parameter", "lattice_constant"],
        material_concept="lattice parameter",
        mechanism_family="lattice_distortion",
        expected_role="fundamental structural length scale",
        physical_interpretation="Lattice parameters encode the periodic repeat distance. Variations track composition, temperature, and pressure effects.",
        typical_units="Å",
    ),
    MaterialSemanticRule(
        feature_patterns=["packing", "packing_fraction", "atomic_packing_factor"],
        material_concept="packing efficiency",
        mechanism_family="lattice_distortion",
        expected_role="quantifies space-filling",
        physical_interpretation="Packing fraction measures how efficiently atoms fill space. Close-packed structures maximize packing; open structures leave free volume.",
    ),
    MaterialSemanticRule(
        feature_patterns=["coordination", "coordination_number", "cn"],
        material_concept="coordination number",
        mechanism_family="lattice_distortion",
        expected_role="local bonding topology",
        physical_interpretation="Coordination number reflects the local atomic environment. Higher CN generally implies denser, more bonded environments.",
    ),

    # -- electronic --
    MaterialSemanticRule(
        feature_patterns=["band_gap", "bandgap", "gap", "bg"],
        material_concept="electronic band gap",
        mechanism_family="electronic_structure",
        expected_role="determines electronic transport and optical behavior",
        physical_interpretation="The band gap separates valence and conduction bands. It controls conductivity, optical absorption edge, and photovoltaic potential.",
        typical_units="eV",
    ),
    MaterialSemanticRule(
        feature_patterns=["dos", "density_of_states"],
        material_concept="electronic density of states",
        mechanism_family="electronic_structure",
        expected_role="electronic availability near Fermi level",
        physical_interpretation="DOS at the Fermi level correlates with conductivity, superconductivity, and catalytic activity.",
    ),
    MaterialSemanticRule(
        feature_patterns=["fermi", "fermi_energy", "fermi_level"],
        material_concept="Fermi energy",
        mechanism_family="electronic_structure",
        expected_role="electrochemical potential of electrons",
        physical_interpretation="Fermi energy sets the electron chemical potential and influences work function, contact behavior, and redox stability.",
        typical_units="eV",
    ),
    MaterialSemanticRule(
        feature_patterns=["homo", "lumo", "homo_lumo"],
        material_concept="frontier orbital energies",
        mechanism_family="electronic_structure",
        expected_role="molecular reactivity and charge transfer",
        physical_interpretation="HOMO-LUMO gap approximates chemical hardness and optical excitation energy in molecular systems.",
        typical_units="eV",
    ),

    # -- thermodynamic --
    MaterialSemanticRule(
        feature_patterns=["formation_energy", "e_form", "formation_enthalpy"],
        material_concept="formation energy",
        mechanism_family="thermodynamic_stability",
        expected_role="thermodynamic stability indicator",
        physical_interpretation="Formation energy quantifies stability relative to constituent elements. More negative values indicate stronger compound stability.",
        typical_units="eV/atom",
    ),
    MaterialSemanticRule(
        feature_patterns=["cohesive_energy", "e_coh"],
        material_concept="cohesive energy",
        mechanism_family="bonding_strength",
        expected_role="measures bond strength",
        physical_interpretation="Cohesive energy is the energy gain when free atoms condense into a solid. It correlates with melting point, hardness, and stability.",
        typical_units="eV/atom",
    ),
    MaterialSemanticRule(
        feature_patterns=["mixing_enthalpy", "delta_h_mix"],
        material_concept="mixing enthalpy",
        mechanism_family="thermodynamic_stability",
        expected_role="drives phase separation or solid-solution formation",
        physical_interpretation="Negative mixing enthalpy favors mixing; positive values favor phase separation. Near-zero values can indicate high-entropy stabilization.",
        typical_units="kJ/mol",
    ),
    MaterialSemanticRule(
        feature_patterns=["decomposition_energy", "e_decomp"],
        material_concept="decomposition energy",
        mechanism_family="thermodynamic_stability",
        expected_role="metastability indicator",
        physical_interpretation="Decomposition energy measures the thermodynamic driving force toward competing phases. Small positive values indicate metastable compounds.",
        typical_units="eV/atom",
    ),

    # -- processing / microstructure --
    MaterialSemanticRule(
        feature_patterns=["temperature", "temp", "t_"],
        material_concept="temperature",
        mechanism_family="processing_structure",
        expected_role="thermal driving force for kinetics and phase stability",
        physical_interpretation="Temperature controls diffusion, phase transitions, and equilibrium. It is a primary processing parameter.",
        typical_units="K or °C",
        caveats=["Temperature is a processing condition, not an intrinsic material descriptor."],
    ),
    MaterialSemanticRule(
        feature_patterns=["anneal", "annealing"],
        material_concept="annealing condition",
        mechanism_family="processing_structure",
        expected_role="post-synthesis thermal history",
        physical_interpretation="Annealing can relieve strain, grow grains, or induce phase transformations depending on temperature and duration.",
        caveats=["Annealing effect depends on time-temperature profile, not captured by a single value."],
    ),
    MaterialSemanticRule(
        feature_patterns=["grain", "grain_size", "crystallite"],
        material_concept="grain / crystallite size",
        mechanism_family="processing_structure",
        expected_role="microstructural length scale",
        physical_interpretation="Grain size affects mechanical strength (Hall-Petch), conductivity, and diffusion. Smaller grains increase grain-boundary area.",
        typical_units="nm or µm",
    ),
    MaterialSemanticRule(
        feature_patterns=["phase_fraction", "phase_"],
        material_concept="phase fraction",
        mechanism_family="processing_structure",
        expected_role="multi-phase microstructure composition",
        physical_interpretation="Phase fractions control composite properties through rule-of-mixtures effects and interface-mediated behavior.",
    ),
]


class MaterialSemanticsRegistry:
    """Registry that maps feature names to material science concepts.

    Looks up features against built-in pattern rules and can be extended
    with custom rules at runtime.
    """

    def __init__(self):
        self._rules: List[MaterialSemanticRule] = list(_BUILTIN_RULES)
        # Pre-built fast-lookup index: lowercase pattern -> rule
        self._index: Dict[str, MaterialSemanticRule] = {}
        self._build_index()

    def _build_index(self) -> None:
        self._index.clear()
        for rule in self._rules:
            for pat in rule.feature_patterns:
                self._index[pat.lower()] = rule

    def register_rule(self, rule: MaterialSemanticRule) -> None:
        """Register a custom semantic rule at runtime."""
        self._rules.append(rule)
        for pat in rule.feature_patterns:
            self._index[pat.lower()] = rule
        logger.info("Registered material semantic rule: %s", rule.material_concept)

    def lookup(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """Look up material semantics for a feature name.

        Returns a dict with concept, mechanism_family, expected_role,
        physical_interpretation, typical_units, and caveats,
        or None if no rule matches.
        """
        if not feature_name:
            return None

        feat_lower = feature_name.lower()

        # 1. Exact pattern match
        if feat_lower in self._index:
            rule = self._index[feat_lower]
            return _rule_to_dict(rule)

        # 2. Substring match (for patterns like "fraction_" prefix)
        for pat, rule in self._index.items():
            if pat in feat_lower:
                return _rule_to_dict(rule)

        return None

    def get_all_rules(self) -> List[Dict[str, Any]]:
        """Return all registered rules as dicts (for inspection)."""
        return [_rule_to_dict(r) for r in self._rules]


def _rule_to_dict(rule: MaterialSemanticRule) -> Dict[str, Any]:
    return {
        "material_concept": rule.material_concept,
        "mechanism_family": rule.mechanism_family,
        "expected_role": rule.expected_role,
        "physical_interpretation": rule.physical_interpretation,
        "typical_units": rule.typical_units,
        "caveats": rule.caveats,
    }


# Module-level singleton
_semantics_registry: Optional[MaterialSemanticsRegistry] = None


def get_semantics_registry() -> MaterialSemanticsRegistry:
    """Get or create the global MaterialSemanticsRegistry singleton."""
    global _semantics_registry
    if _semantics_registry is None:
        _semantics_registry = MaterialSemanticsRegistry()
    return _semantics_registry
