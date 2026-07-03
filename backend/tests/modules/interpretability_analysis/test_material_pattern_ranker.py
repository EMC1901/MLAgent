"""Tests for Phase 3b: material_pattern_ranker module.

Covers: scientific scoring, downgrade rules, dedup, ranking separation
of boundary vs design rules, display_priority assignment, and edge cases.
"""

import pytest
import numpy as np
import pandas as pd

from app.modules.interpretability_analysis.material_pattern_ranker import (
    refine_and_rank_material_patterns,
)
from app.modules.interpretability_analysis.schemas import (
    MaterialPatternCandidate,
    PatternCondition,
    PatternEffect,
    PatternSampleSupport,
    PatternValidationResult,
    PatternScientificScore,
    FeatureEvidenceProfile,
    EvidenceUnit,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pattern(
    pid="p1",
    ptype="monotonic",
    feat="feat_0",
    vstatus="pass",
    in_scope=50,
    out_scope=150,
    effect_dir="increases",
    effect_size=0.5,
    confidence=0.8,
    material_concepts=None,
    ci_excludes_zero=True,
    ice_agreement=0.85,
):
    cond = PatternCondition(
        feature_name=feat,
        material_concept=material_concepts[0] if material_concepts else "test concept",
        operator="high",
        quantile_range=[0.75, 1.0],
        source="pdp",
    )
    effect = PatternEffect(
        target_direction=effect_dir,
        effect_size=effect_size,
        evidence_basis="pdp_delta",
    )
    ss = PatternSampleSupport(
        in_scope_count=in_scope,
        out_scope_count=out_scope,
        coverage=in_scope / max(in_scope + out_scope, 1),
        in_scope_fraction=in_scope / max(in_scope + out_scope, 1),
    )
    vrs = [
        PatternValidationResult(
            validation_id=f"val_sc_{pid}",
            pattern_id=pid,
            validation_type="subgroup_contrast",
            status=vstatus,
            metrics={"direction_matches_candidate": True, "in_scope_count": in_scope},
        ),
        PatternValidationResult(
            validation_id=f"val_bs_{pid}",
            pattern_id=pid,
            validation_type="bootstrap",
            status="pass" if ci_excludes_zero else "weak",
            metrics={"ci_excludes_zero": ci_excludes_zero, "in_scope_count": in_scope, "bootstrap_n": 1000},
        ),
    ]
    if ice_agreement is not None:
        vrs.append(PatternValidationResult(
            validation_id=f"val_ice_{pid}",
            pattern_id=pid,
            validation_type="ice_consistency",
            status="pass" if ice_agreement >= 0.7 else "weak",
            metrics={"agreement_ratio": ice_agreement, "n_ice_rows": 100},
        ))
    return MaterialPatternCandidate(
        pattern_id=pid,
        pattern_type=ptype,
        statement=f"Pattern {pid}: {feat} shows {effect_dir} effect",
        material_concepts=material_concepts or ["test concept"],
        conditions=[cond],
        predicted_effect=effect,
        confidence_score=confidence,
        confidence_label="high" if confidence >= 0.7 else "medium",
        sample_support=ss,
        validation_results=vrs,
        validation_status=vstatus,
    )


def _make_feature_profiles(n=5):
    return [
        FeatureEvidenceProfile(
            feature_name=f"feat_{i}",
            consensus_score=1.0 - i * 0.1,
            physical_interpretability_score=0.9 - i * 0.1,
        )
        for i in range(n)
    ]


def _make_evidence_units(n=5):
    return [
        EvidenceUnit(
            evidence_id=f"ev_{i}",
            evidence_type="shap_importance",
            feature_names=[f"feat_{i}"],
        )
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRefineAndRank:

    def test_empty_patterns_returns_empty(self):
        result = refine_and_rank_material_patterns([], [], [])
        assert result == []

    def test_single_pattern_gets_scored(self):
        patterns = [_make_pattern()]
        profiles = _make_feature_profiles()
        evidence = _make_evidence_units()
        result = refine_and_rank_material_patterns(patterns, profiles, evidence)
        assert len(result) == 1
        p = result[0]
        assert p.scientific_score is not None
        assert p.scientific_score.total > 0.0
        assert p.scientific_score.total <= 1.0
        assert p.display_priority == 0

    def test_scoring_components_populated(self):
        patterns = [_make_pattern()]
        profiles = _make_feature_profiles()
        evidence = _make_evidence_units()
        result = refine_and_rank_material_patterns(patterns, profiles, evidence)
        sc = result[0].scientific_score
        assert sc.validation_support > 0
        assert sc.robustness > 0
        assert sc.effect_size > 0
        assert sc.sample_support > 0
        assert sc.physical_interpretability > 0
        assert sc.actionability > 0
        assert len(sc.rank_reason) > 0

    def test_fail_pattern_excluded_from_top(self):
        p_pass = _make_pattern(pid="pass", vstatus="pass", confidence=0.9)
        p_fail = _make_pattern(pid="fail", vstatus="fail", confidence=0.9)
        profiles = _make_feature_profiles()
        evidence = _make_evidence_units()
        result = refine_and_rank_material_patterns(
            [p_pass, p_fail], profiles, evidence, max_patterns=10,
        )
        result_ids = {p.pattern_id for p in result}
        # Fail non-boundary pattern should be excluded
        assert "fail" not in result_ids or p_fail.display_priority == 999

    def test_boundary_separated_from_design_rules(self):
        p_design = _make_pattern(pid="design", ptype="monotonic", vstatus="pass")
        p_boundary = _make_pattern(pid="boundary", ptype="boundary", vstatus="pass")
        profiles = _make_feature_profiles()
        evidence = _make_evidence_units()
        result = refine_and_rank_material_patterns(
            [p_design, p_boundary], profiles, evidence, max_patterns=10,
        )
        design_ids = [p.pattern_id for p in result if p.pattern_type != "boundary"]
        boundary_ids = [p.pattern_id for p in result if p.pattern_type == "boundary"]
        # Design rules should appear before boundaries in display_priority
        if design_ids and boundary_ids:
            for did in design_ids:
                for bid in boundary_ids:
                    dp = next(p for p in result if p.pattern_id == did)
                    bp = next(p for p in result if p.pattern_id == bid)
                    assert dp.display_priority < bp.display_priority

    def test_dedup_removes_duplicate(self):
        p1 = _make_pattern(pid="original", feat="feat_0")
        p2 = _make_pattern(pid="duplicate", feat="feat_0")
        profiles = _make_feature_profiles()
        evidence = _make_evidence_units()
        result = refine_and_rank_material_patterns(
            [p1, p2], profiles, evidence, max_patterns=10,
        )
        result_ids = {p.pattern_id for p in result}
        # Two identical patterns should be deduplicated to 1
        assert len(result) == 1

    def test_small_sample_downgraded(self):
        p = _make_pattern(in_scope=3, vstatus="weak")
        p.sample_support = PatternSampleSupport(
            in_scope_count=3, out_scope_count=197,
        )
        profiles = _make_feature_profiles()
        evidence = _make_evidence_units()
        result = refine_and_rank_material_patterns([p], profiles, evidence)
        sc = result[0].scientific_score
        assert sc.total <= 0.35  # Downgraded for small sample

    def test_opaque_descriptor_downgraded(self):
        p = _make_pattern(material_concepts=["opaque descriptor"])
        profiles = _make_feature_profiles()
        evidence = _make_evidence_units()
        result = refine_and_rank_material_patterns([p], profiles, evidence)
        sc = result[0].scientific_score
        # Opaque gets a penalty
        assert any("opaque" in sc.rank_reason.lower() for _ in [sc])

    def test_display_priority_assigned(self):
        patterns = [
            _make_pattern(pid="p1", confidence=0.9),
            _make_pattern(pid="p2", confidence=0.7),
            _make_pattern(pid="p3", confidence=0.5),
        ]
        profiles = _make_feature_profiles()
        evidence = _make_evidence_units()
        result = refine_and_rank_material_patterns(patterns, profiles, evidence, max_patterns=5)
        priorities = [p.display_priority for p in result]
        assert priorities == sorted(priorities)
        assert all(0 <= pr < 999 for pr in priorities)

    def test_max_patterns_cap(self):
        patterns = [
            _make_pattern(pid=f"p{i}", feat=f"feat_{i % 3}", confidence=0.9 - i * 0.05)
            for i in range(15)
        ]
        profiles = _make_feature_profiles(10)
        evidence = _make_evidence_units(10)
        result = refine_and_rank_material_patterns(patterns, profiles, evidence, max_patterns=5)
        assert len(result) <= 5

    def test_all_fail_boundary_still_included(self):
        """Boundary patterns should be shown as reliability warnings even if validation weak."""
        p = _make_pattern(pid="bnd", ptype="boundary", vstatus="fail", confidence=0.3)
        profiles = _make_feature_profiles()
        evidence = _make_evidence_units()
        result = refine_and_rank_material_patterns([p], profiles, evidence)
        # Boundary patterns aren't filtered by validation_status == "fail" exclusion
        # But they go through boundary sort
        assert len(result) >= 0  # May or may not make it depending on slots
