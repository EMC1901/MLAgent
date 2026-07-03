"""Tests for the Phase 4 material_semantics_registry module.

Covers:
- Built-in rule coverage across composition/structure/electronic/thermodynamic/processing
- Exact match and substring match lookups
- Missing feature returns None
- Custom rule registration
- Rule-to-dict serialization
"""

import pytest
from app.modules.interpretability_analysis.material_semantics_registry import (
    MaterialSemanticsRegistry,
    MaterialSemanticRule,
    get_semantics_registry,
)


class TestMaterialSemanticsRegistry:
    """Tests for the MaterialSemanticsRegistry singleton and lookups."""

    def test_composition_descriptors(self):
        reg = get_semantics_registry()
        # electronegativity
        r = reg.lookup("electronegativity_diff")
        assert r is not None
        assert "electronegativity" in r["material_concept"].lower()
        assert r["mechanism_family"] == "bonding_strength"

        # atomic radius
        r = reg.lookup("mean_atomic_radius")
        assert r is not None
        assert r["mechanism_family"] == "lattice_distortion"

        # valence
        r = reg.lookup("valence_electron_count")
        assert r is not None
        assert r["mechanism_family"] == "electronic_structure"

        # fraction prefix (substring match)
        r = reg.lookup("fraction_fe")
        assert r is not None
        assert r["mechanism_family"] == "composition_complexity"

    def test_structure_descriptors(self):
        reg = get_semantics_registry()
        r = reg.lookup("density")
        assert r is not None
        assert r["mechanism_family"] == "lattice_distortion"

        r = reg.lookup("unit_cell_volume")
        assert r is not None
        assert r["mechanism_family"] == "lattice_distortion"

        r = reg.lookup("lattice_parameter")
        assert r is not None

        r = reg.lookup("coordination_number")
        assert r is not None

    def test_electronic_descriptors(self):
        reg = get_semantics_registry()
        r = reg.lookup("band_gap")
        assert r is not None
        assert r["mechanism_family"] == "electronic_structure"
        assert r["typical_units"] == "eV"

        r = reg.lookup("fermi_energy")
        assert r is not None
        assert r["mechanism_family"] == "electronic_structure"

    def test_thermodynamic_descriptors(self):
        reg = get_semantics_registry()
        r = reg.lookup("formation_energy")
        assert r is not None
        assert r["mechanism_family"] == "thermodynamic_stability"

        r = reg.lookup("mixing_enthalpy")
        assert r is not None
        assert r["mechanism_family"] == "thermodynamic_stability"

        r = reg.lookup("decomposition_energy")
        assert r is not None
        assert r["mechanism_family"] == "thermodynamic_stability"

        r = reg.lookup("cohesive_energy")
        assert r is not None
        assert r["mechanism_family"] == "bonding_strength"

    def test_processing_descriptors(self):
        reg = get_semantics_registry()
        r = reg.lookup("grain_size")
        assert r is not None
        assert r["mechanism_family"] == "processing_structure"

        r = reg.lookup("phase_fraction")
        assert r is not None
        assert r["mechanism_family"] == "processing_structure"

    def test_missing_feature_returns_none(self):
        reg = get_semantics_registry()
        assert reg.lookup("completely_unknown_xyz_123") is None
        assert reg.lookup("") is None

    def test_custom_rule_registration(self):
        reg = get_semantics_registry()
        rule = MaterialSemanticRule(
            feature_patterns=["custom_descriptor_xyz"],
            material_concept="custom test concept",
            mechanism_family="electronic_structure",
            expected_role="test only",
            physical_interpretation="Test interpretation.",
            typical_units="test_units",
            caveats=["Not real."],
        )
        reg.register_rule(rule)

        r = reg.lookup("custom_descriptor_xyz")
        assert r is not None
        assert r["material_concept"] == "custom test concept"
        assert r["typical_units"] == "test_units"
        assert "Not real." in r["caveats"]

    def test_get_all_rules(self):
        reg = get_semantics_registry()
        all_rules = reg.get_all_rules()
        assert len(all_rules) > 20  # built-in coverage
        for r in all_rules:
            assert "material_concept" in r
            assert "mechanism_family" in r

    def test_empty_feature_returns_none(self):
        reg = get_semantics_registry()
        assert reg.lookup(None) is None
        assert reg.lookup("") is None


class TestGroundingPriorityChain:
    """Verify the priority chain: lineage.description > lineage.category
    > semantics_registry > keyword fallback > opaque descriptor."""

    def test_lineage_description_wins(self):
        from app.modules.interpretability_analysis.material_mechanism_mapper import _ground_feature
        reg = get_semantics_registry()
        lineage = {"band_gap": {"description": "Custom electronic descriptor", "category": "structure"}}
        concept, level = _ground_feature("band_gap", lineage, reg)
        assert concept == "Custom electronic descriptor"
        assert level == "lineage_grounded"

    def test_lineage_category_second(self):
        from app.modules.interpretability_analysis.material_mechanism_mapper import _ground_feature
        reg = get_semantics_registry()
        lineage = {"my_feat": {"category": "thermodynamic"}}
        concept, level = _ground_feature("my_feat", lineage, reg)
        assert "thermodynamic" in concept.lower()
        assert level == "lineage_grounded"

    def test_registry_fallback(self):
        from app.modules.interpretability_analysis.material_mechanism_mapper import _ground_feature
        reg = get_semantics_registry()
        concept, level = _ground_feature("electronegativity_diff", {}, reg)
        assert level == "physics_prior_grounded"
        assert "electronegativity" in concept.lower()

    def test_keyword_fallback(self):
        from app.modules.interpretability_analysis.material_mechanism_mapper import _ground_feature
        reg = get_semantics_registry()
        # "bulk_modulus" is in the physics registry's keyword map but not the semantics registry
        concept, level = _ground_feature("bulk_modulus_123", {}, reg)
        assert level == "descriptor_grounded"

    def test_opaque_descriptor(self):
        from app.modules.interpretability_analysis.material_mechanism_mapper import _ground_feature
        reg = get_semantics_registry()
        concept, level = _ground_feature("xyz_unknown_abc", {}, reg)
        assert "opaque" in concept.lower()
        assert level == "descriptor_grounded"
