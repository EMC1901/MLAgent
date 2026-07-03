"""Tests for Phase 3a: material_pattern_validator module.

Covers: build_condition_mask, subgroup_contrast, bootstrap_effect_ci,
ice_consistency, boundary_error_check, and validate_material_patterns.
"""

import pytest
import numpy as np
import pandas as pd
from types import SimpleNamespace

from app.modules.interpretability_analysis.material_pattern_validator import (
    validate_material_patterns,
    build_condition_mask,
)
from app.modules.interpretability_analysis.schemas import (
    MaterialPatternCandidate,
    PatternCondition,
    PatternEffect,
    PatternSampleSupport,
    PatternValidationResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_X(n_samples=200, seed=42):
    rng = np.random.RandomState(seed)
    return pd.DataFrame({
        "feat_0": rng.uniform(0, 1, n_samples),
        "feat_1": rng.uniform(0, 1, n_samples),
        "feat_2": rng.uniform(0, 1, n_samples),
    })


def _make_y_pred(X):
    return 2.0 * X["feat_0"] + 0.5 * X["feat_1"] + np.random.RandomState(99).normal(0, 0.1, len(X))


def _make_y_true(X):
    return 2.0 * X["feat_0"] + 0.5 * X["feat_1"]


def _make_monotonic_pattern(effect_dir="increases"):
    cond = PatternCondition(
        feature_name="feat_0",
        material_concept="test concept",
        operator="high",
        quantile_range=[0.75, 1.0],
        source="pdp",
    )
    effect = PatternEffect(
        target_direction=effect_dir,
        effect_size=0.5,
        evidence_basis="pdp_delta",
    )
    return MaterialPatternCandidate(
        pattern_id="test_mono_inc",
        pattern_type="monotonic",
        statement="feat_0 shows monotonic increase on target",
        material_concepts=["test concept"],
        conditions=[cond],
        predicted_effect=effect,
        confidence_score=0.8,
        confidence_label="high",
    )


def _make_threshold_pattern():
    cond = PatternCondition(
        feature_name="feat_0",
        material_concept="test concept",
        operator="high",
        quantile_range=[0.75, 1.0],
        value_range={"min": 0.75, "max": 1.0},
        source="pdp",
    )
    effect = PatternEffect(
        target_direction="increases",
        effect_size=0.3,
        evidence_basis="pdp_delta",
    )
    return MaterialPatternCandidate(
        pattern_id="test_thresh",
        pattern_type="threshold",
        statement="feat_0 above 0.75 shows threshold increase",
        material_concepts=["test concept"],
        conditions=[cond],
        predicted_effect=effect,
        confidence_score=0.7,
        confidence_label="medium",
    )


def _make_boundary_pattern():
    return MaterialPatternCandidate(
        pattern_id="test_boundary",
        pattern_type="boundary",
        statement="Boundary: high error when feat_1 is low",
        material_concepts=["error region"],
        conditions=[
            PatternCondition(
                feature_name="feat_1",
                material_concept="test",
                operator="low",
                quantile_range=[0.0, 0.25],
                source="subgroup_contrast",
            ),
        ],
        predicted_effect=PatternEffect(
            target_direction="uncertain",
            effect_size=0.0,
            evidence_basis="predicted_target",
        ),
        confidence_score=0.4,
        confidence_label="low",
    )


def _make_reverse_direction_pattern():
    cond = PatternCondition(
        feature_name="feat_0",
        material_concept="test",
        operator="high",
        quantile_range=[0.75, 1.0],
        source="pdp",
    )
    effect = PatternEffect(
        target_direction="decreases",  # Wrong direction for feat_0 which actually increases
        effect_size=0.5,
        evidence_basis="pdp_delta",
    )
    return MaterialPatternCandidate(
        pattern_id="test_rev",
        pattern_type="monotonic",
        statement="feat_0 decreases target (reverse direction)",
        material_concepts=["test"],
        conditions=[cond],
        predicted_effect=effect,
        confidence_score=0.6,
        confidence_label="medium",
    )


def _make_small_sample_pattern():
    cond = PatternCondition(
        feature_name="feat_0",
        material_concept="test",
        operator="between",
        value_range={"min": 0.99, "max": 1.0},  # very narrow range
        source="pdp",
    )
    effect = PatternEffect(
        target_direction="increases",
        effect_size=0.1,
        evidence_basis="pdp_delta",
    )
    return MaterialPatternCandidate(
        pattern_id="test_small",
        pattern_type="window",
        statement="feat_0 narrow window",
        material_concepts=["test"],
        conditions=[cond],
        predicted_effect=effect,
        confidence_score=0.5,
        confidence_label="low",
    )


class MockModel:
    """Mock model that predicts based on feat_0."""
    def predict(self, X):
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        # feat_0 is column 0
        return X[:, 0] * 2.0 + X[:, 1] * 0.5


# ---------------------------------------------------------------------------
# build_condition_mask
# ---------------------------------------------------------------------------


class TestBuildConditionMask:

    def test_low_operator_uses_default_quantile(self):
        X = _make_X()
        cond = PatternCondition(
            feature_name="feat_0", material_concept="test",
            operator="low", source="pdp",
        )
        mask, stats = build_condition_mask(X, [cond])
        n_in = mask.sum()
        expected_low = int(len(X) * 0.25)
        assert n_in <= expected_low + 5
        assert n_in >= expected_low - 5

    def test_high_operator_uses_default_quantile(self):
        X = _make_X()
        cond = PatternCondition(
            feature_name="feat_0", material_concept="test",
            operator="high", source="pdp",
        )
        mask, stats = build_condition_mask(X, [cond])
        n_in = mask.sum()
        expected_high = int(len(X) * 0.25)
        assert n_in <= expected_high + 5
        assert n_in >= expected_high - 5

    def test_high_operator_with_explicit_quantile_range(self):
        X = _make_X()
        cond = PatternCondition(
            feature_name="feat_0", material_concept="test",
            operator="high", quantile_range=[0.75, 1.0], source="pdp",
        )
        mask, stats = build_condition_mask(X, [cond])
        assert mask.sum() > 0

    def test_between_operator_with_value_range(self):
        X = _make_X()
        cond = PatternCondition(
            feature_name="feat_0", material_concept="test",
            operator="between", value_range={"min": 0.2, "max": 0.4}, source="pdp",
        )
        mask, stats = build_condition_mask(X, [cond])
        assert mask.sum() > 0
        in_vals = X.loc[mask, "feat_0"]
        assert in_vals.min() >= 0.2
        assert in_vals.max() <= 0.4

    def test_between_operator_falls_back_to_quantile(self):
        X = _make_X()
        cond = PatternCondition(
            feature_name="feat_0", material_concept="test",
            operator="between", source="pdp",
        )
        mask, stats = build_condition_mask(X, [cond])
        assert mask.sum() > 0

    def test_outside_operator(self):
        X = _make_X()
        cond = PatternCondition(
            feature_name="feat_0", material_concept="test",
            operator="outside", value_range={"min": 0.3, "max": 0.7}, source="pdp",
        )
        mask, stats = build_condition_mask(X, [cond])
        assert mask.sum() > 0
        in_vals = X.loc[mask, "feat_0"]
        # All values should be outside [0.3, 0.7]
        assert ((in_vals < 0.3) | (in_vals > 0.7)).all()

    def test_increasing_operator_splits_at_median(self):
        X = _make_X()
        cond = PatternCondition(
            feature_name="feat_0", material_concept="test",
            operator="increasing", source="pdp",
        )
        mask, stats = build_condition_mask(X, [cond])
        assert mask.sum() > 0
        median = X["feat_0"].median()
        assert (X.loc[mask, "feat_0"] >= median).all()

    def test_decreasing_operator_selects_above_median(self):
        X = _make_X()
        cond = PatternCondition(
            feature_name="feat_0", material_concept="test",
            operator="decreasing", source="pdp",
        )
        mask, stats = build_condition_mask(X, [cond])
        assert mask.sum() > 0
        median = X["feat_0"].median()
        # Decreasing uses high-value group as in-scope (>= median),
        # because high values → lower target → negative delta → matches "decreases".
        assert (X.loc[mask, "feat_0"] >= median).all()

    def test_multiple_conditions_and_logic(self):
        X = _make_X()
        cond1 = PatternCondition(
            feature_name="feat_0", material_concept="test",
            operator="high", quantile_range=[0.5, 1.0], source="pdp",
        )
        cond2 = PatternCondition(
            feature_name="feat_1", material_concept="test",
            operator="high", quantile_range=[0.5, 1.0], source="pdp",
        )
        mask, stats = build_condition_mask(X, [cond1, cond2])
        n_both = mask.sum()
        n_single = int(len(X) * 0.25)
        # Both high means intersection should be <= either single
        assert n_both <= n_single + 10

    def test_empty_conditions_returns_zero_mask(self):
        X = _make_X()
        mask, stats = build_condition_mask(X, [])
        # Empty conditions → no actionable subgroup → returns zero mask
        assert mask.sum() == 0
        assert "_warning" in stats

    def test_missing_feature_raises(self):
        X = _make_X()
        cond = PatternCondition(
            feature_name="nonexistent", material_concept="test",
            operator="high", source="pdp",
        )
        with pytest.raises(ValueError):
            build_condition_mask(X, [cond])

    def test_empty_X_returns_empty_mask(self):
        X = pd.DataFrame()
        mask, stats = build_condition_mask(X, [])
        assert len(mask) == 0


# ---------------------------------------------------------------------------
# validate_material_patterns — integration
# ---------------------------------------------------------------------------


class TestValidateMaterialPatterns:

    def test_monotonic_positive_direction_passes(self):
        X = _make_X()
        y_pred = _make_y_pred(X)
        y_true = _make_y_true(X)
        patterns = [_make_monotonic_pattern("increases")]
        result = validate_material_patterns(patterns, X, y_true, y_pred)
        p = result[0]
        assert p.validation_status in ("pass", "weak")
        assert p.sample_support is not None
        assert p.sample_support.in_scope_count > 0
        assert len(p.validation_results) >= 2  # subgroup + bootstrap

    def test_reverse_direction_fails(self):
        X = _make_X()
        y_pred = _make_y_pred(X)
        y_true = _make_y_true(X)
        patterns = [_make_reverse_direction_pattern()]
        result = validate_material_patterns(patterns, X, y_true, y_pred)
        p = result[0]
        # Should have at least one fail result
        statuses = {vr.status for vr in p.validation_results}
        assert "fail" in statuses or p.validation_status == "fail"

    def test_threshold_pattern_passes(self):
        X = _make_X()
        y_pred = _make_y_pred(X)
        y_true = _make_y_true(X)
        patterns = [_make_threshold_pattern()]
        result = validate_material_patterns(patterns, X, y_true, y_pred)
        p = result[0]
        assert p.validation_status in ("pass", "weak")
        assert len(p.validation_results) >= 2

    def test_boundary_error_check_applied(self):
        X = _make_X(100)
        y_pred = _make_y_pred(X)
        y_true = _make_y_true(X)
        patterns = [_make_boundary_pattern()]
        result = validate_material_patterns(patterns, X, y_true, y_pred)
        p = result[0]
        boundary_validations = [
            vr for vr in p.validation_results
            if vr.validation_type == "boundary_error_check"
        ]
        assert len(boundary_validations) == 1

    def test_small_sample_gets_weak(self):
        X = _make_X(50)
        y_pred = _make_y_pred(X)
        y_true = _make_y_true(X)
        patterns = [_make_small_sample_pattern()]
        result = validate_material_patterns(patterns, X, y_true, y_pred)
        p = result[0]
        # Very narrow range should have few in-scope samples
        assert p.sample_support is not None
        if p.sample_support.in_scope_count < 5:
            assert p.validation_status in ("weak", "fail")

    def test_no_y_true_still_validates_model_only(self):
        X = _make_X()
        y_pred = _make_y_pred(X)
        patterns = [_make_monotonic_pattern()]
        result = validate_material_patterns(patterns, X, None, y_pred)
        p = result[0]
        # Subgroup contrast still runs but observed_delta won't be present
        assert p.validation_status != "unvalidated"

    def test_no_X_or_y_pred_skips(self):
        patterns = [_make_monotonic_pattern()]
        result = validate_material_patterns(patterns, None, None, None)
        assert result[0].validation_status == "unvalidated"

    def test_mismatched_prediction_length_skips_without_exception(self):
        X = _make_X(20)
        y_pred = _make_y_pred(X).iloc[:10]
        y_true = _make_y_true(X).iloc[:10]
        patterns = [_make_monotonic_pattern()]

        result = validate_material_patterns(patterns, X, y_true, y_pred)

        assert result[0].validation_status == "unvalidated"
        assert any("not row-aligned" in item for item in result[0].limitations)

    def test_empty_patterns_returns_empty(self):
        result = validate_material_patterns([], _make_X(), None, _make_y_pred(_make_X()))
        assert result == []

    def test_ice_consistency_not_applied_to_boundary(self):
        X = _make_X()
        y_pred = _make_y_pred(X)
        y_true = _make_y_true(X)
        patterns = [_make_boundary_pattern()]
        result = validate_material_patterns(
            patterns, X, y_true, y_pred, model=MockModel(),
            max_patterns_for_ice=5,
        )
        p = result[0]
        ice_validations = [
            vr for vr in p.validation_results
            if vr.validation_type == "ice_consistency"
        ]
        # Boundary patterns should get 'not_applicable' for ICE
        assert len(ice_validations) == 0

    def test_ice_consistency_applied_with_model(self):
        X = _make_X(100)
        y_pred = _make_y_pred(X)
        y_true = _make_y_true(X)
        patterns = [_make_monotonic_pattern("increases")]
        result = validate_material_patterns(
            patterns, X, y_true, y_pred, model=MockModel(),
            max_patterns_for_ice=5,
        )
        p = result[0]
        ice_validations = [
            vr for vr in p.validation_results
            if vr.validation_type == "ice_consistency"
        ]
        assert len(ice_validations) == 1

    def test_sample_support_populated(self):
        X = _make_X()
        y_pred = _make_y_pred(X)
        y_true = _make_y_true(X)
        patterns = [_make_monotonic_pattern()]
        result = validate_material_patterns(patterns, X, y_true, y_pred)
        ss = result[0].sample_support
        assert ss is not None
        assert ss.in_scope_count > 0
        assert ss.coverage > 0.0
        assert ss.in_scope_fraction > 0.0
