"""Shared fixtures for interpretability_analysis tests."""
import pytest
import numpy as np
from types import SimpleNamespace


@pytest.fixture
def sample_per_method_importance():
    """Mock importance data from 3 methods for 10 features."""
    return {
        "shap": [
            {"feature_name": f"feat_{i}", "importance_value": (10 - i) * 0.1,
             "importance_rank": i + 1, "importance_method": "shap",
             "direction": "positive" if i % 2 == 0 else "negative"}
            for i in range(10)
        ],
        "permutation_importance": [
            {"feature_name": f"feat_{i}", "importance_value": (10 - i) * 0.08,
             "importance_rank": i + 1, "importance_method": "permutation_importance",
             "direction": "positive" if i % 2 == 0 else "negative",
             "importance_std": (i + 1) * 0.01}
            for i in range(10)
        ],
        "coefficient": [
            {"feature_name": f"feat_{i}", "importance_value": (10 - i) * 0.05,
             "importance_rank": i + 1, "importance_method": "coefficient",
             "direction": "positive" if i < 5 else "negative"}
            for i in range(10)
        ],
    }


@pytest.fixture
def sample_correlation_analysis():
    return {
        "feature_names": [f"feat_{i}" for i in range(10)],
        "target_correlations": [
            {"feature_name": f"feat_{i}", "pearson_r": (10 - i) * 0.08,
             "spearman_rho": (10 - i) * 0.07}
            for i in range(10)
        ],
        "high_correlation_pairs": [
            {"feature_1": "feat_0", "feature_2": "feat_1", "correlation": 0.92},
            {"feature_1": "feat_2", "feature_2": "feat_3", "correlation": 0.75},
        ],
    }


@pytest.fixture
def sample_partial_dependence():
    return {
        "pdp_1d": [
            {"feature_name": "feat_0", "grid_values": [0, 1, 2, 3, 4],
             "pdp_values": [0.1, 0.3, 0.7, 1.0, 1.2]},
            {"feature_name": "feat_1", "grid_values": [0, 1, 2, 3, 4],
             "pdp_values": [0.1, 0.8, 0.3, 0.9, 0.2]},
            {"feature_name": "feat_5", "grid_values": [0, 1, 2, 3, 4],
             "pdp_values": [0.5, 0.5, 0.5, 0.5, 0.5]},
        ],
        "pdp_2d": [],
    }


@pytest.fixture
def sample_residual_analysis():
    return {
        "r_squared": 0.85,
        "rmse": 0.15,
        "residual_mean": 0.12,
        "residual_std": 0.10,
        "systematic_error_segments": [
            {"segment_description": "predicted < 0.2", "mean_absolute_error": 0.35,
             "n_samples": 25},
            {"segment_description": "predicted 0.8-1.0", "mean_absolute_error": 0.08,
             "n_samples": 30},
        ],
    }


@pytest.fixture
def sample_systematic_errors():
    return [
        {"feature_name": "feat_0", "quantile": 0, "value_range": "[0.0, 0.2]",
         "n_samples": 20, "mean_abs_error": 0.3, "error_ratio_to_overall": 2.5,
         "possible_cause": "extreme feature values"},
        {"feature_name": "feat_1", "quantile": 4, "value_range": "[0.8, 1.0]",
         "n_samples": 18, "mean_abs_error": 0.25, "error_ratio_to_overall": 2.1,
         "possible_cause": "extreme tail values"},
    ]


@pytest.fixture
def sample_physics_constraints():
    return {
        "constraints": [
            {"constraint_name": "band_gap", "description": "Band gap >= 0 eV",
             "passed": True, "severity": "critical", "n_violations": 0,
             "violation_rate": 0.0, "violating_sample_indices": []},
        ],
        "passed": True,
    }


@pytest.fixture
def sample_physics_constraints_violated():
    return {
        "constraints": [
            {"constraint_name": "band_gap", "description": "Band gap >= 0 eV",
             "passed": False, "severity": "critical", "n_violations": 5,
             "violation_rate": 0.05, "violating_sample_indices": [0, 1, 2, 3, 4]},
        ],
        "passed": False,
    }


@pytest.fixture
def sample_cross_method_consensus():
    return {
        "rank_correlation_matrix": {
            "shap": {"shap": 1.0, "permutation_importance": 0.85},
            "permutation_importance": {"shap": 0.85, "permutation_importance": 1.0},
        },
        "consensus_features": ["feat_0", "feat_1", "feat_2"],
        "divergent_features": [
            {"feature_name": "feat_9", "rank_std": 5.2},
        ],
        "overall_agreement_score": 0.85,
    }


@pytest.fixture
def sample_feature_lineage():
    return {
        "feat_0": {"source": "composition", "description": "Atomic fraction of element A",
                    "transformation": "normalize", "category": "composition"},
        "feat_1": {"source": "structure", "description": "Lattice constant",
                    "transformation": "raw", "category": "structure"},
        "feat_2": {"source": "elemental", "description": "Electronegativity difference",
                    "unit": "eV", "category": "elemental"},
    }


@pytest.fixture
def sample_feature_columns():
    return [f"feat_{i}" for i in range(10)]


@pytest.fixture
def sample_model_performance():
    return {
        "primary_metric": "r2",
        "primary_metric_value": 0.85,
        "r_squared": 0.85,
        "rmse": 0.15,
    }


@pytest.fixture
def sample_high_error_analysis():
    return [
        SimpleNamespace(
            sample_id="sample_001", absolute_error=0.45, error_rank=1,
            possible_error_factors=["extreme_feat_0", "low_feat_1"],
            feature_pattern_summary="feat_0 > 95th percentile, feat_1 < 5th percentile",
            review_suggestion="Check measurement validity"),
        SimpleNamespace(
            sample_id="sample_002", absolute_error=0.32, error_rank=2,
            possible_error_factors=["unusual_feat_2"],
            feature_pattern_summary="feat_2 near decision boundary",
            review_suggestion="Consider outlier status"),
    ]


@pytest.fixture
def sample_shap_interactions():
    return [
        {"feature_1": "feat_0", "feature_2": "feat_1",
         "interaction_strength": 0.15},
        {"feature_1": "feat_2", "feature_2": "feat_3",
         "interaction_strength": 0.03},
    ]


@pytest.fixture
def sample_method_statuses():
    return {
        "coefficient": "computed",
        "permutation_importance": "computed",
        "shap": "computed",
    }
