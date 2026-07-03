"""Tests for PhysicsRuleRegistry and check_physics_constraints wrapper."""

import numpy as np
import pytest

from app.modules.interpretability_analysis.physics_rule_registry import (
    PhysicsRuleRegistry,
    PhysicsConstraintRule,
    get_registry,
    check_physics_constraints,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_registry() -> PhysicsRuleRegistry:
    """Return a brand-new registry instance (NOT the module-level singleton)."""
    return PhysicsRuleRegistry()


# ---------------------------------------------------------------------------
# 1. Singleton
# ---------------------------------------------------------------------------

def test_registry_singleton_returns_same_instance():
    """Calling get_registry() multiple times yields the same object."""
    a = get_registry()
    b = get_registry()
    assert a is b


# ---------------------------------------------------------------------------
# 2-4. Default constraint checks
# ---------------------------------------------------------------------------

class TestDefaultConstraints:
    """Verify built-in constraints behave correctly."""

    def test_band_gap_passes(self):
        """Non-negative band gap values should all satisfy the constraint."""
        reg = _fresh_registry()
        rule = reg.get_all_constraints()["band_gap"]
        values = np.array([0.0, 0.5, 1.0, 2.5, 3.2])
        result = rule.check_fn(values)
        assert np.all(result)

    def test_band_gap_violation(self):
        """Negative band gap values should be flagged as violations."""
        reg = _fresh_registry()
        rule = reg.get_all_constraints()["band_gap"]
        values = np.array([-0.1, 0.5, -1.2, 2.5])
        result = rule.check_fn(values)
        assert not np.all(result)
        assert list(result) == [False, True, False, True]

    def test_density_positive(self):
        """Density must be strictly positive; zeros fail."""
        reg = _fresh_registry()
        rule = reg.get_all_constraints()["density"]
        values = np.array([0.0, 1.0, 3.5, 0.0])
        result = rule.check_fn(values)
        assert list(result) == [False, True, True, False]


# ---------------------------------------------------------------------------
# 5-6. match_constraints
# ---------------------------------------------------------------------------

class TestMatchConstraints:
    """Tests for matching constraints by target name."""

    def test_match_by_target_name(self):
        """Matching 'band_gap' should return at least the band_gap constraint."""
        reg = _fresh_registry()
        matched = reg.match_constraints("band_gap")
        assert len(matched) >= 1
        assert "band_gap" in matched

    def test_match_no_result(self):
        """An unknown target property returns an empty dict."""
        reg = _fresh_registry()
        matched = reg.match_constraints("nonexistent_target_xyz")
        assert matched == {}

    def test_match_case_insensitive(self):
        """Matching is case-insensitive."""
        reg = _fresh_registry()
        matched = reg.match_constraints("BAND_GAP")
        assert "band_gap" in matched


# ---------------------------------------------------------------------------
# 7. register_custom_constraint
# ---------------------------------------------------------------------------

class TestRegisterCustomConstraint:
    """Register individual PhysicsConstraintRule instances."""

    def test_register_and_retrieve(self):
        reg = _fresh_registry()
        rule = PhysicsConstraintRule(
            constraint_name="test_positivity",
            description="Values must be > 0",
            check_fn=lambda v: v > 0,
            severity="warning",
            target_patterns=["custom_target"],
        )
        reg.register_constraint(rule)
        all_c = reg.get_all_constraints()
        assert "test_positivity" in all_c
        assert all_c["test_positivity"] is rule

    def test_register_empty_name_raises(self):
        reg = _fresh_registry()
        rule = PhysicsConstraintRule(
            constraint_name="",
            description="bad",
            check_fn=lambda v: v > 0,
            severity="warning",
        )
        with pytest.raises(ValueError, match="Constraint name cannot be empty"):
            reg.register_constraint(rule)

    def test_register_non_callable_raises(self):
        reg = _fresh_registry()
        rule = PhysicsConstraintRule(
            constraint_name="bad_check",
            description="non-callable",
            check_fn="not_callable",  # type: ignore
            severity="warning",
        )
        with pytest.raises(ValueError, match="check_fn must be callable"):
            reg.register_constraint(rule)

    def test_invalid_severity_defaults_to_warning(self):
        reg = _fresh_registry()
        rule = PhysicsConstraintRule(
            constraint_name="soft_check",
            description="something",
            check_fn=lambda v: v > 0,
            severity="invalid",
        )
        reg.register_constraint(rule)
        stored = reg.get_all_constraints()["soft_check"]
        assert stored.severity == "warning"


# ---------------------------------------------------------------------------
# 8. register_custom_constraints_from_dict
# ---------------------------------------------------------------------------

class TestRegisterCustomConstraintsFromDict:
    """Batch registration via register_custom_constraints."""

    def test_batch_register(self):
        reg = _fresh_registry()
        custom = {
            "positive": {
                "check": lambda v: v > 0,
                "description": "Must be positive",
                "severity": "critical",
                "target_patterns": ["target_a"],
            },
            "less_than_one": {
                "check": lambda v: v < 1.0,
                "description": "Must be < 1",
                "severity": "info",
                "target_patterns": ["target_b"],
            },
        }
        reg.register_custom_constraints(custom)
        all_c = reg.get_all_constraints()
        assert "positive" in all_c
        assert "less_than_one" in all_c
        assert all_c["positive"].severity == "critical"
        assert all_c["less_than_one"].severity == "info"

    def test_skip_non_dict_specs(self):
        reg = _fresh_registry()
        custom = {
            "bad_one": "not_a_dict",
        }
        # Should not raise; should just skip
        reg.register_custom_constraints(custom)
        assert "bad_one" not in reg.get_all_constraints()

    def test_skip_non_callable_check(self):
        reg = _fresh_registry()
        custom = {
            "no_check": {
                "check": "unusable",
                "description": "bad",
            },
        }
        reg.register_custom_constraints(custom)
        assert "no_check" not in reg.get_all_constraints()

    def test_empty_custom_does_nothing(self):
        reg = _fresh_registry()
        before = set(reg.get_all_constraints().keys())
        reg.register_custom_constraints({})
        after = set(reg.get_all_constraints().keys())
        assert before == after


# ---------------------------------------------------------------------------
# 9-10. compute_physics_consistency_score
# ---------------------------------------------------------------------------

class TestComputePhysicsConsistencyScore:
    """Score computation from constraint check results."""

    def test_all_passed_gives_one(self):
        reg = _fresh_registry()
        results = {
            "constraints": [
                {"passed": True, "severity": "critical"},
                {"passed": True, "severity": "warning"},
            ],
            "passed": True,
        }
        score = reg.compute_physics_consistency_score(results)
        assert score == 1.0

    def test_critical_violation_capped_at_point_five(self):
        reg = _fresh_registry()
        results = {
            "constraints": [
                {"passed": False, "severity": "critical"},
            ],
            "passed": False,
        }
        score = reg.compute_physics_consistency_score(results)
        assert score == 0.5

    def test_warning_violation_reduces_score(self):
        reg = _fresh_registry()
        results = {
            "constraints": [
                {"passed": False, "severity": "warning"},
            ],
            "passed": False,
        }
        score = reg.compute_physics_consistency_score(results)
        assert score == 0.9

    def test_info_violation_reduces_score(self):
        reg = _fresh_registry()
        results = {
            "constraints": [
                {"passed": False, "severity": "info"},
            ],
            "passed": False,
        }
        score = reg.compute_physics_consistency_score(results)
        assert score == 0.95

    def test_mixed_violations_with_critical_cap(self):
        """Score cannot exceed 0.5 when any critical violation is present.
        Here: 1 critical + 1 warning => raw 1.0 - 0.3 - 0.1 = 0.6, capped to 0.5."""
        reg = _fresh_registry()
        results = {
            "constraints": [
                {"passed": False, "severity": "critical"},
                {"passed": False, "severity": "warning"},
            ],
            "passed": False,
        }
        score = reg.compute_physics_consistency_score(results)
        assert score == 0.5

    def test_score_never_below_zero(self):
        reg = _fresh_registry()
        results = {
            "constraints": [
                {"passed": False, "severity": "warning"}
                for _ in range(20)
            ],
            "passed": False,
        }
        score = reg.compute_physics_consistency_score(results)
        assert score == 0.0

    def test_empty_constraints_returns_one(self):
        reg = _fresh_registry()
        results: dict = {"constraints": [], "passed": True}
        score = reg.compute_physics_consistency_score(results)
        assert score == 1.0


# ---------------------------------------------------------------------------
# 11-12. check_all
# ---------------------------------------------------------------------------

class TestCheckAll:
    """Integration-level checks via check_all / check_physics_constraints."""

    def test_empty_y_pred(self):
        """Empty array returns passed=True with no constraint results."""
        reg = _fresh_registry()
        result = reg.check_all(np.array([], dtype=float), target_property="band_gap")
        assert result["passed"] is True
        assert result["constraints"] == []

    def test_none_y_pred(self):
        """None input returns passed=True with no constraint results."""
        reg = _fresh_registry()
        result = reg.check_all(None, target_property="band_gap")  # type: ignore[arg-type]
        assert result["passed"] is True
        assert result["constraints"] == []

    def test_with_custom_constraints_temp(self):
        """Custom constraints passed to check_all are registered temporarily
        and cleaned up afterward."""
        reg = _fresh_registry()
        before = set(reg.get_all_constraints().keys())

        y_pred = np.array([0.3, 0.5, 0.7])
        result = reg.check_all(
            y_pred,
            target_property="custom_target",
            custom_constraints={
                "under_one": {
                    "check": lambda v: v < 1.0,
                    "description": "All values < 1",
                    "severity": "warning",
                }
            },
        )
        # Temporary constraint was used and then removed
        after = set(reg.get_all_constraints().keys())
        assert before == after
        assert len(result["constraints"]) >= 1
        # All values < 1, so should pass
        assert result["passed"] is True

    def test_with_custom_constraints_violation(self):
        """Custom constraints that are violated produce a failing result."""
        reg = _fresh_registry()
        y_pred = np.array([1.5, 0.3, 2.0])
        result = reg.check_all(
            y_pred,
            target_property="custom_target",
            custom_constraints={
                "under_one": {
                    "check": lambda v: v < 1.0,
                    "description": "All values < 1",
                    "severity": "critical",
                }
            },
        )
        assert result["passed"] is False
        violation_entry = result["constraints"][0]
        assert violation_entry["passed"] is False
        assert violation_entry["n_violations"] == 2

    def test_check_all_via_wrapper(self):
        """check_physics_constraints wrapper works correctly."""
        y_pred = np.array([1.0, 2.0, 3.0])
        result = check_physics_constraints(y_pred, target_property="band_gap")
        assert "constraints" in result
        assert "passed" in result

    def test_check_all_no_matching_constraints(self):
        """When no constraints match the target, passed=True with empty results."""
        reg = _fresh_registry()
        y_pred = np.array([1.0, 2.0])
        result = reg.check_all(y_pred, target_property="does_not_match_any_pattern")
        assert result["passed"] is True
        assert result["constraints"] == []


# ---------------------------------------------------------------------------
# 13-14. Feature semantics
# ---------------------------------------------------------------------------

class TestFeatureSemantics:
    """Registering and retrieving feature-level semantics."""

    def test_register_feature_semantics(self):
        reg = _fresh_registry()
        reg.register_feature_semantics(
            "my_custom_feature",
            {"category": "optical", "unit": "eV"},
        )
        semantics = reg.get_feature_semantics("my_custom_feature")
        assert semantics == {"category": "optical", "unit": "eV"}

    def test_get_feature_semantics_match(self):
        """Pattern matching is case-insensitive and substring-based."""
        reg = _fresh_registry()
        # Default semantics include "electronegativity"
        semantics = reg.get_feature_semantics("ELECTRONEGATIVITY")
        assert "category" in semantics
        assert semantics["category"] == "elemental"

    def test_get_feature_semantics_no_match(self):
        reg = _fresh_registry()
        semantics = reg.get_feature_semantics("completely_unknown_feature_xyz")
        assert semantics == {}

    def test_register_feature_semantics_empty_pattern_raises(self):
        reg = _fresh_registry()
        with pytest.raises(ValueError, match="feature_pattern cannot be empty"):
            reg.register_feature_semantics("", {"category": "test"})

    def test_get_feature_semantics_partial_substring(self):
        """Substring matching: 'electronegativity_difference' should match
        the 'electronegativity' pattern."""
        reg = _fresh_registry()
        semantics = reg.get_feature_semantics("electronegativity_difference")
        assert "category" in semantics
        assert semantics["category"] == "elemental"


# ---------------------------------------------------------------------------
# 15. Unregister
# ---------------------------------------------------------------------------

class TestUnregisterConstraint:
    def test_unregister_existing(self):
        reg = _fresh_registry()
        before = "band_gap" in reg.get_all_constraints()
        assert before is True
        removed = reg.unregister_constraint("band_gap")
        assert removed is True
        assert "band_gap" not in reg.get_all_constraints()

    def test_unregister_nonexistent(self):
        reg = _fresh_registry()
        removed = reg.unregister_constraint("never_registered")
        assert removed is False
