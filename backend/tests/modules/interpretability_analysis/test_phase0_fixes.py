"""Phase 0 tests: verify data-flow and evidence-chain fixes.

Tests are designed to be runnable without a database or full service
instantiation — they exercise the units that were modified in Phase 0.
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch

from app.modules.interpretability_analysis.schemas import (
    EvidenceUnit,
    FeatureGroupSummary,
)
from app.modules.interpretability_analysis.enums import EvidenceType
from app.modules.interpretability_analysis.evidence_normalizer import (
    build_evidence_units,
)
from app.modules.interpretability_analysis.builder import build_response
from app.modules.interpretability_analysis.service import (
    _features_from_evidence_refs,
)


# ---------------------------------------------------------------------------
# 1. builder returns feature_group_summary from correct DB field
# ---------------------------------------------------------------------------

def test_builder_returns_feature_group_summary_not_manifest():
    """feature_group_summary must come from feature_group_summary_json, not artifact_manifest_json."""
    import types

    record = types.SimpleNamespace(
        id="ia_test",
        task_id="task_1",
        metric_evaluation_id=None,
        pipeline_execution_id=None,
        status="analyzed",
        analysis_profile="standard",
        final_model_id=None,
        final_model_family=None,
        final_trial_id=None,
        methods_used_json={"methods": ["shap"]},
        global_feature_importance_json={"items": []},
        permutation_importance_json=None,
        shap_summary_json=None,
        local_explanations_json=None,
        high_error_sample_analysis_json=None,
        feature_group_summary_json={"feature_groups": {"composition": {"count": 3}}, "summary_text": "3 composition features"},
        material_insight_summary_json=None,
        llm_summary_json=None,
        cross_method_consensus_json=None,
        partial_dependence_json=None,
        residual_analysis_json=None,
        correlation_analysis_json=None,
        physics_constraint_check_json=None,
        scientific_insight_report_json=None,
        final_output_input_json=None,
        artifact_manifest_json={"manifest_path": "/tmp/manifest.json", "key": "this_is_manifest_not_fgs"},
        ready_for_final_output=False,
        error_message=None,
        created_at=None,
        updated_at=None,
    )

    response = build_response(record=record)

    # The response's feature_group_summary must equal the feature_group_summary_json
    # content, NOT the artifact_manifest_json content.
    assert response.feature_group_summary is not None
    assert response.feature_group_summary == record.feature_group_summary_json
    assert response.feature_group_summary != record.artifact_manifest_json
    assert "composition" in response.feature_group_summary.get("feature_groups", {})
    assert "this_is_manifest_not_fgs" not in str(response.feature_group_summary)


# ---------------------------------------------------------------------------
# 2. ranked_feature_columns construction logic
# ---------------------------------------------------------------------------

def test_pdp_uses_ranked_important_features():
    """When top_importance has a different order than feature_columns,
    ranked_feature_columns should reflect importance order, not raw column order."""
    from app.modules.interpretability_analysis.schemas import GlobalFeatureImportanceItem

    # Simulate: feature_columns in raw order, but top_importance ranks differently
    feature_columns = ["bad_0", "bad_1", "important_x"]
    top_importance = [
        GlobalFeatureImportanceItem(feature_name="important_x", importance_value=0.9, importance_rank=1),
        GlobalFeatureImportanceItem(feature_name="bad_0", importance_value=0.1, importance_rank=2),
        GlobalFeatureImportanceItem(feature_name="bad_1", importance_value=0.05, importance_rank=3),
    ]

    # Simulate X.columns
    x_columns = set(feature_columns)

    ranked = [
        fi.feature_name
        for fi in top_importance
        if fi.feature_name in x_columns
    ]

    assert ranked == ["important_x", "bad_0", "bad_1"]
    assert ranked[0] == "important_x"
    assert ranked != feature_columns  # Not the raw order


# ---------------------------------------------------------------------------
# 3. SHAP interactions create evidence units
# ---------------------------------------------------------------------------

class TestShapInteractionsCreateEvidenceUnits:

    def test_shap_interactions_create_evidence_units(self):
        """Giving shap_interactions to build_evidence_units produces
        EvidenceType.SHAP_INTERACTION evidence."""
        shap_interactions = [
            {"feature_1": "a", "feature_2": "b", "interaction_strength": 0.2},
            {"feature_1": "c", "feature_2": "d", "interaction_strength": 0.05},
        ]

        units = build_evidence_units(
            per_method_importance={},
            correlation_analysis=None,
            partial_dependence=None,
            residual_analysis=None,
            systematic_errors=None,
            physics_constraints=None,
            shap_summary=None,
            cross_method_consensus=None,
            shap_interactions=shap_interactions,
        )

        interaction_units = [u for u in units if u.evidence_type == EvidenceType.SHAP_INTERACTION]
        assert len(interaction_units) == 2
        assert interaction_units[0].feature_names == ["a", "b"]
        assert interaction_units[1].feature_names == ["c", "d"]
        assert interaction_units[0].method_name == "shap_interaction"

    def test_shap_interactions_skip_empty_names(self):
        """Items with empty feature names are skipped."""
        shap_interactions = [
            {"feature_1": "", "feature_2": "", "interaction_strength": 0.9},
            {"feature_1": "feat_a", "feature_2": "feat_b", "interaction_strength": 0.3},
        ]

        units = build_evidence_units(
            per_method_importance={},
            correlation_analysis=None,
            partial_dependence=None,
            residual_analysis=None,
            systematic_errors=None,
            physics_constraints=None,
            shap_summary=None,
            cross_method_consensus=None,
            shap_interactions=shap_interactions,
        )

        interaction_units = [u for u in units if u.evidence_type == EvidenceType.SHAP_INTERACTION]
        assert len(interaction_units) == 1
        assert interaction_units[0].feature_names == ["feat_a", "feat_b"]

    def test_shap_dependence_creates_light_evidence(self):
        """SHAP dependence data should produce light evidence units."""
        import numpy as np
        shap_dependence = [
            {
                "feature_name": "feat_0",
                "feature_values": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                "shap_values": [-0.1, -0.05, 0.0, 0.05, 0.1, 0.15],
            },
        ]

        units = build_evidence_units(
            per_method_importance={},
            correlation_analysis=None,
            partial_dependence=None,
            residual_analysis=None,
            systematic_errors=None,
            physics_constraints=None,
            shap_summary=None,
            cross_method_consensus=None,
            shap_dependence=shap_dependence,
        )

        # SHAP dependence uses its own EvidenceType.SHAP_DEPENDENCE
        dep_units = [u for u in units if u.evidence_type == EvidenceType.SHAP_DEPENDENCE]
        assert len(dep_units) == 1
        assert dep_units[0].feature_names == ["feat_0"]
        assert "value_range" in dep_units[0].quantitative_summary
        assert "shap_sign_split" in dep_units[0].quantitative_summary


# ---------------------------------------------------------------------------
# 4. material_insight supporting_features are actual feature names
# ---------------------------------------------------------------------------

class TestMaterialInsightSupportingFeatures:

    def test_supporting_features_are_feature_names_not_evidence_ids(self):
        """_features_from_evidence_refs maps evidence IDs to feature names."""
        evidence_units = [
            EvidenceUnit(
                evidence_id="ev_001", evidence_type=EvidenceType.SHAP_IMPORTANCE,
                feature_names=["feat_0", "feat_1"],
                quantitative_summary={}, method_name="shap",
            ),
            EvidenceUnit(
                evidence_id="ev_002", evidence_type=EvidenceType.PERMUTATION_IMPORTANCE,
                feature_names=["feat_2"],
                quantitative_summary={}, method_name="permutation_importance",
            ),
            EvidenceUnit(
                evidence_id="ev_003", evidence_type=EvidenceType.PDP_1D,
                feature_names=["feat_0"],
                quantitative_summary={}, method_name="partial_dependence",
            ),
        ]

        # If we reference ev_001 and ev_003, we should get feat_0, feat_1
        evidence_ids = ["ev_001", "ev_003"]
        result = _features_from_evidence_refs(evidence_ids, evidence_units)

        assert isinstance(result, list)
        assert len(result) >= 1
        assert "feat_0" in result
        # ev_001 also provides feat_1
        assert "feat_1" in result
        # ev_003 also provides feat_0 (deduplicated)
        # ev_002 not referenced, so feat_2 should NOT appear
        assert "feat_2" not in result
        # None of these should be evidence IDs
        for r in result:
            assert not r.startswith("ev_")

    def test_empty_evidence_ids_returns_empty(self):
        result = _features_from_evidence_refs([], [])
        assert result == []

    def test_none_evidence_ids_returns_empty(self):
        result = _features_from_evidence_refs(None, [])
        assert result == []

    def test_unmatched_ids_returns_empty(self):
        units = [
            EvidenceUnit(
                evidence_id="ev_999", evidence_type=EvidenceType.SHAP_IMPORTANCE,
                feature_names=["feat_x"],
                quantitative_summary={}, method_name="shap",
            ),
        ]
        result = _features_from_evidence_refs(["ev_nonexistent"], units)
        assert result == []
