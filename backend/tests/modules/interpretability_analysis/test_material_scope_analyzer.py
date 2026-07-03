"""Tests for the Phase 4 material_scope_analyzer module.

Covers:
- Family column detection from metadata, lineage, and heuristics
- Quantile-based scope correctly separates high-value from low-value families
- value_range-based scope with min/max overlap
- Threshold-based scope
- Missing metadata produces explicit scope_note
- apply_scope_to_mechanisms integration
"""

import pytest
import numpy as np
import pandas as pd
from app.modules.interpretability_analysis.schemas import (
    MaterialPatternCandidate,
    PatternCondition,
    PatternEffect,
    MaterialMechanismCandidate,
)
from app.modules.interpretability_analysis.material_scope_analyzer import (
    analyze_material_scope,
    apply_scope_to_mechanisms,
    _detect_material_family_columns,
    _feature_in_range,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pattern(pattern_id="mp_test", conditions=None):
    return MaterialPatternCandidate(
        pattern_id=pattern_id,
        pattern_type="monotonic",
        statement="Test pattern.",
        conditions=conditions or [
            PatternCondition(
                feature_name="feat_x",
                material_concept="test",
                operator="between",
                value_range={"min": 0.0, "max": 1.0},
                source="pdp",
            )
        ],
        predicted_effect=PatternEffect(
            target_direction="increases", effect_size=0.3,
            effect_unit="pdp_delta", evidence_basis="pdp_delta",
        ),
    )


# ---------------------------------------------------------------------------
# Test: Family column detection
# ---------------------------------------------------------------------------

class TestFamilyColumnDetection:
    """Detection of material-family columns from metadata / lineage / heuristics."""

    def test_detect_from_metadata(self):
        X = pd.DataFrame({"a": [1, 2], "formula_col": ["AB", "CD"], "b": [3, 4]})
        meta = {"formula_column": "formula_col"}
        cols = _detect_material_family_columns(X, meta, None)
        assert "formula_col" in cols
        assert cols["formula_col"] == "formula"

    def test_detect_from_lineage(self):
        X = pd.DataFrame({"a": [1, 2], "crystal_fam": ["cubic", "hex"]})
        lineage = {"crystal_fam": {"category": "crystal_family"}}
        cols = _detect_material_family_columns(X, None, lineage)
        assert "crystal_fam" in cols

    def test_detect_from_heuristic(self):
        X = pd.DataFrame({
            "feat": [1, 2, 3, 4, 5],
            "space_group": [225, 225, 221, 221, 194],
        })
        cols = _detect_material_family_columns(X, None, None)
        assert "space_group" in cols  # contains "group"

    def test_heuristic_skips_high_cardinality(self):
        X = pd.DataFrame({"family_name": list(range(100))})  # 100 unique values
        cols = _detect_material_family_columns(X, None, None)
        assert "family_name" not in cols  # n_unique > 50

    def test_no_families_detected(self):
        X = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        cols = _detect_material_family_columns(X, None, None)
        assert cols == {}


# ---------------------------------------------------------------------------
# Test: Quantile-based scope (P2 fix)
# ---------------------------------------------------------------------------

class TestQuantileScope:
    """Quantile conditions must use global thresholds, not always-True."""

    def test_high_quantile_excludes_low_family(self):
        np.random.seed(42)
        X = pd.DataFrame({
            "feat_x": np.concatenate([
                np.random.uniform(0.0, 0.3, 40),   # family A: low
                np.random.uniform(0.7, 1.0, 40),   # family B: high
            ]),
            "family": ["A"] * 40 + ["B"] * 40,
        })
        p = _make_pattern(conditions=[
            PatternCondition(feature_name="feat_x", material_concept="test",
                           operator="high", value_range={},
                           quantile_range=[0.7, 0.9], source="pdp"),
        ])
        results = analyze_material_scope([p], X, {}, {})
        assert len(results) == 1
        scope = results[0]
        assert "B" in scope["stable_families"], f"High-quantile family B should be stable, got {scope}"
        assert "A" not in scope["stable_families"], f"Low-value A must not be stable for high-quantile pattern"

    def test_low_quantile_excludes_high_family(self):
        np.random.seed(42)
        X = pd.DataFrame({
            "feat_x": np.concatenate([
                np.random.uniform(0.0, 0.3, 40),   # family A: low
                np.random.uniform(0.7, 1.0, 40),   # family B: high
            ]),
            "family": ["A"] * 40 + ["B"] * 40,
        })
        p = _make_pattern(conditions=[
            PatternCondition(feature_name="feat_x", material_concept="test",
                           operator="low", value_range={},
                           quantile_range=[0.1, 0.3], source="pdp"),
        ])
        results = analyze_material_scope([p], X, {}, {})
        scope = results[0]
        assert "A" in scope["stable_families"], f"Low-quantile family A should be stable, got {scope}"
        assert "B" not in scope["stable_families"], f"High-value B must not be stable for low-quantile pattern"


# ---------------------------------------------------------------------------
# Test: value_range-based scope
# ---------------------------------------------------------------------------

class TestValueRangeScope:
    """Explicit value_range min/max conditions."""

    def test_overlapping_range_is_stable(self):
        np.random.seed(42)
        X = pd.DataFrame({
            "feat_x": np.concatenate([
                np.random.uniform(0.2, 0.8, 40),   # A: overlaps [0.0, 1.0]
                np.random.uniform(2.0, 3.0, 40),   # B: outside
            ]),
            "family": ["A"] * 40 + ["B"] * 40,
        })
        p = _make_pattern(conditions=[
            PatternCondition(feature_name="feat_x", material_concept="test",
                           operator="between", value_range={"min": 0.0, "max": 1.0},
                           source="pdp"),
        ])
        results = analyze_material_scope([p], X, {}, {})
        scope = results[0]
        assert "A" in scope["stable_families"]
        # B has values 2.0-3.0, which do NOT overlap [0.0, 1.0]
        assert "B" not in scope["stable_families"], f"B should not be stable (range 2-3 vs [0,1]); got {scope}"

    def test_threshold_straddling(self):
        np.random.seed(42)
        X = pd.DataFrame({
            "feat_x": np.concatenate([
                np.random.uniform(0.0, 0.4, 40),   # A: below threshold
                np.random.uniform(0.3, 0.7, 40),   # B: straddles threshold 0.5
            ]),
            "family": ["A"] * 40 + ["B"] * 40,
        })
        p = _make_pattern(conditions=[
            PatternCondition(feature_name="feat_x", material_concept="test",
                           operator="between", value_range={"threshold": 0.5},
                           source="pdp"),
        ])
        results = analyze_material_scope([p], X, {}, {})
        scope = results[0]
        # B straddles 0.5 (range 0.3-0.7)
        assert "B" in scope["stable_families"]
        # A is entirely below 0.5 (max=0.4)
        assert "A" not in scope["stable_families"], f"A should not be stable (0-0.4 vs threshold 0.5); got {scope}"


# ---------------------------------------------------------------------------
# Test: Missing metadata note
# ---------------------------------------------------------------------------

class TestMissingMetadata:
    """When no family columns exist, scope_note must be explicit."""

    def test_no_family_columns_produces_note(self):
        X = pd.DataFrame({"feat_x": [1.0, 2.0, 3.0, 4.0, 5.0]})
        p = _make_pattern()
        results = analyze_material_scope([p], X, {}, {})
        assert len(results) == 1
        assert "No material-family metadata available" in results[0]["scope_note"]
        assert results[0]["stable_families"] == []
        assert results[0]["weak_families"] == []

    def test_too_few_samples_excluded(self):
        X = pd.DataFrame({
            "feat_x": np.random.uniform(0, 1, 100),
            "family": ["tiny"] * 3 + ["big"] * 97,
        })
        p = _make_pattern()
        results = analyze_material_scope([p], X, {}, {})
        scope = results[0]
        # "tiny" has only 3 samples
        assert any("too few samples" in fam for fam in scope["excluded_families"]), \
            f"tiny family with 3 samples should be excluded, got {scope}"


# ---------------------------------------------------------------------------
# Test: apply_scope_to_mechanisms
# ---------------------------------------------------------------------------

class TestApplyScopeToMechanisms:
    """Scope results must be applied to mechanism candidates."""

    def test_applies_scope(self):
        mechanisms = [
            MaterialMechanismCandidate(
                mechanism_id="mm_1",
                source_pattern_ids=["mp_a"],
                mechanism_family="bonding_strength",
            ),
        ]
        scope_results = [{
            "pattern_id": "mp_a",
            "stable_families": ["oxide", "perovskite"],
            "weak_families": ["alloy"],
            "excluded_families": [],
            "family_support_counts": {},
            "scope_note": "",
        }]
        mechanisms = apply_scope_to_mechanisms(mechanisms, scope_results)
        assert len(mechanisms) == 1
        assert "oxide" in mechanisms[0].applicable_material_scope
        assert "perovskite" in mechanisms[0].applicable_material_scope
        assert "alloy" in mechanisms[0].excluded_or_weak_scope

    def test_empty_scope_no_change(self):
        mechanisms = [MaterialMechanismCandidate(mechanism_id="mm_1", source_pattern_ids=["mp_x"])]
        result = apply_scope_to_mechanisms(mechanisms, [])
        assert result == mechanisms


# ---------------------------------------------------------------------------
# Test: _feature_in_range edge cases
# ---------------------------------------------------------------------------

class TestFeatureInRangeEdgeCases:
    """Edge cases for the _feature_in_range helper."""

    def test_none_values(self):
        assert _feature_in_range(None, PatternCondition(feature_name="x", source="pdp")) is False

    def test_empty_series(self):
        s = pd.Series([], dtype=float)
        assert _feature_in_range(s, PatternCondition(feature_name="x", source="pdp")) is False

    def test_no_constraints(self):
        s = pd.Series([1.0, 2.0, 3.0])
        assert _feature_in_range(s, PatternCondition(
            feature_name="x", value_range={}, source="pdp")) is True
