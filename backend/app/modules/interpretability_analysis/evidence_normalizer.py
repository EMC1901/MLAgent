import uuid
import logging
import numpy as np
from typing import List, Dict, Any, Optional

from app.modules.interpretability_analysis.schemas import (
    EvidenceUnit,
    FeatureEvidenceProfile,
)
from app.modules.interpretability_analysis.enums import EvidenceType

logger = logging.getLogger(__name__)


def build_evidence_units(
    per_method_importance: Dict[str, List[Dict[str, Any]]],
    correlation_analysis: Optional[Dict[str, Any]],
    partial_dependence: Optional[Dict[str, Any]],
    residual_analysis: Optional[Dict[str, Any]],
    systematic_errors: Optional[List[Dict[str, Any]]],
    physics_constraints: Optional[Dict[str, Any]],
    shap_summary: Optional[Any],
    cross_method_consensus: Optional[Dict[str, Any]],
    shap_interactions: Optional[List[Dict[str, Any]]] = None,
    shap_dependence: Optional[List[Dict[str, Any]]] = None,
) -> List[EvidenceUnit]:
    """Collect raw outputs from all analyzers and produce unified EvidenceUnit list.

    Each EvidenceUnit represents a single piece of evidence from one method.
    Different methods have different evidence_type values and quantitative_summary shapes.

    Raises:
        EvidenceNormalizationException: if input data is fundamentally malformed (missing
            required fields that make normalization impossible). Empty/missing optional
            inputs are handled gracefully by returning fewer EvidenceUnits.
    """
    units: List[EvidenceUnit] = []

    # --- Importance-based evidence ---
    for method_name, items in per_method_importance.items():
        if not items:
            continue
        evidence_type_map = {
            "shap": EvidenceType.SHAP_IMPORTANCE,
            "permutation_importance": EvidenceType.PERMUTATION_IMPORTANCE,
            "coefficient": EvidenceType.COEFFICIENT_IMPORTANCE,
            "native_importance": EvidenceType.NATIVE_IMPORTANCE,
        }
        etype = evidence_type_map.get(method_name, method_name)
        n_items = len(items)
        max_val = max(abs(it.get("importance_value", 0)) for it in items) if items else 0.0
        if max_val < 1e-12:
            max_val = 1.0  # Avoid division by zero for flat importance

        for item in items:
            feature_name = item.get("feature_name", "")
            if not feature_name:
                logger.warning("Skipping importance item with empty feature_name in method=%s", method_name)
                continue
            raw_val = item.get("importance_value", 0.0)
            qs: Dict[str, Any] = {
                "importance_value": raw_val,
                "normalized_importance": abs(raw_val) / max_val,
                "importance_rank": item.get("importance_rank", 0),
                "total_features_evaluated": n_items,
            }
            if "importance_std" in item:
                qs["importance_std"] = item["importance_std"]
            if "shap_variance" in item:
                qs["shap_variance"] = item["shap_variance"]
            units.append(EvidenceUnit(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                evidence_type=etype,
                feature_names=[feature_name],
                quantitative_summary=qs,
                direction=item.get("direction", "unknown"),
                strength=min(abs(raw_val) / max_val, 1.0) if max_val > 0 else 0.0,
                reliability=0.7,
                limitations=[],
                method_name=method_name,
            ))

    # --- PDP-based evidence ---
    if partial_dependence:
        pdp_1d_list = partial_dependence.get("pdp_1d", [])
        for pdp_item in pdp_1d_list:
            feature_name = pdp_item.get("feature_name", "")
            if not feature_name:
                continue
            pdp_vals = pdp_item.get("pdp_values", [])
            trend = _detect_pdp_monotonicity(pdp_item)
            strength_val = _compute_pdp_strength(pdp_item)
            direction = "positive" if trend.startswith("monotonic_increasing") else (
                "negative" if trend.startswith("monotonic_decreasing") else (
                    "non_monotonic" if "non_monotonic" in trend else "flat"))

            grid_vals = pdp_item.get("grid_values", [])
            units.append(EvidenceUnit(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                evidence_type=EvidenceType.PDP_1D,
                feature_names=[feature_name],
                quantitative_summary={
                    "grid_values": grid_vals[:20],
                    "pdp_values": pdp_vals[:20],
                    "trend": trend,
                    "pdp_range": max(pdp_vals) - min(pdp_vals) if len(pdp_vals) >= 2 else 0.0,
                },
                direction=direction,
                strength=strength_val,
                reliability=0.6,
                limitations=["PDP assumes feature independence; may be misleading for correlated features."],
                method_name="partial_dependence",
            ))

    # --- Correlation-based evidence ---
    if correlation_analysis:
        target_corrs = correlation_analysis.get("target_correlations", [])
        max_corr = max(abs(c.get("pearson_r", 0)) for c in target_corrs) if target_corrs else 1.0
        if max_corr < 1e-12:
            max_corr = 1.0
        for tc in target_corrs:
            feature_name = tc.get("feature_name", "")
            if not feature_name:
                continue
            pearson_r = tc.get("pearson_r", 0.0)
            units.append(EvidenceUnit(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                evidence_type=EvidenceType.CORRELATION_LINEAR,
                feature_names=[feature_name],
                quantitative_summary={
                    "pearson_r": pearson_r,
                    "spearman_rho": tc.get("spearman_rho", 0.0),
                },
                direction="positive" if pearson_r > 0 else "negative" if pearson_r < 0 else "flat",
                strength=min(abs(pearson_r) / max_corr, 1.0) if max_corr > 0 else 0.0,
                reliability=0.5,
                limitations=["Correlation does not imply causality; non-linear relationships may be missed."],
                method_name="correlation",
            ))

        high_pairs = correlation_analysis.get("high_correlation_pairs", [])
        for hp in high_pairs:
            units.append(EvidenceUnit(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                evidence_type=EvidenceType.CORRELATION_RANK,
                feature_names=[hp.get("feature_1", ""), hp.get("feature_2", "")],
                quantitative_summary={"correlation": hp.get("correlation", 0.0)},
                direction="unknown",
                strength=min(abs(hp.get("correlation", 0)), 1.0),
                reliability=0.7,
                limitations=["High inter-feature correlation may inflate importance."],
                method_name="correlation",
            ))

    # --- Residual-based evidence ---
    if residual_analysis:
        systematic_segments = residual_analysis.get("systematic_error_segments", [])
        for seg in systematic_segments:
            units.append(EvidenceUnit(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                evidence_type=EvidenceType.RESIDUAL_SEGMENT,
                feature_names=[],
                quantitative_summary={
                    "segment_description": seg.get("segment_description", ""),
                    "mean_absolute_error": seg.get("mean_absolute_error", 0.0),
                    "n_samples": seg.get("n_samples", 0),
                },
                direction="unknown",
                strength=min(seg.get("mean_absolute_error", 0) / max(
                    residual_analysis.get("rmse", 1.0), 1e-6), 1.0),
                reliability=0.5,
                limitations=["Systematic error patterns may indicate model misspecification."],
                method_name="residual_analysis",
            ))

    # --- Systematic error concentration ---
    if systematic_errors:
        for se in systematic_errors:
            units.append(EvidenceUnit(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                evidence_type=EvidenceType.ERROR_CONCENTRATION,
                feature_names=[se.get("feature_name", "")],
                quantitative_summary={
                    "quantile": se.get("quantile", 0),
                    "value_range": se.get("value_range", ""),
                    "n_samples": se.get("n_samples", 0),
                    "mean_abs_error": se.get("mean_abs_error", 0.0),
                    "error_ratio_to_overall": se.get("error_ratio_to_overall", 1.0),
                    "possible_cause": se.get("possible_cause", ""),
                },
                direction="unknown",
                strength=min(se.get("error_ratio_to_overall", 1.0) / 3.0, 1.0),
                reliability=0.4,
                limitations=["Error concentration may be sensitive to binning strategy."],
                method_name="systematic_error",
            ))

    # --- Physics constraint evidence ---
    if physics_constraints:
        constraints = physics_constraints.get("constraints", [])
        for c in constraints:
            units.append(EvidenceUnit(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                evidence_type=EvidenceType.PHYSICS_CONSTRAINT,
                feature_names=[],
                quantitative_summary={
                    "constraint_name": c.get("constraint_name", ""),
                    "description": c.get("description", ""),
                    "passed": c.get("passed", True),
                    "n_violations": c.get("n_violations", 0),
                    "violation_rate": c.get("violation_rate", 0.0),
                    "severity": c.get("severity", "warning"),
                },
                direction="unknown",
                strength=1.0 if c.get("passed", True) else 0.0,
                reliability=1.0,
                limitations=["Physics constraints represent domain invariants."],
                method_name="physics_constraint_check",
            ))

    # --- SHAP interaction evidence ---
    if shap_interactions:
        max_strength = max(abs(x.get("interaction_strength", 0.0)) for x in shap_interactions) or 1.0
        for item in shap_interactions:
            f1 = item.get("feature_1", "")
            f2 = item.get("feature_2", "")
            if not f1 or not f2:
                continue
            strength = abs(item.get("interaction_strength", 0.0))
            units.append(EvidenceUnit(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                evidence_type=EvidenceType.SHAP_INTERACTION,
                feature_names=[f1, f2],
                quantitative_summary=item,
                direction=item.get("direction", "unknown"),
                strength=min(strength / max_strength, 1.0),
                reliability=0.45,
                limitations=[
                    "SHAP interaction is approximated from SHAP-value covariance; validate with 2D PDP or subgroup analysis."
                ],
                method_name="shap_interaction",
            ))

    # --- SHAP dependence light evidence ---
    # Retain dependence data so it's not discarded before Material Pattern Mining.
    # Each entry captures: feature, value range, SHAP sign split, suspected threshold.
    if shap_dependence:
        for dep in shap_dependence:
            feat = dep.get("feature_name", dep.get("feature", ""))
            if not feat:
                continue
            dep_vals = dep.get("feature_values", [])
            shap_vals = dep.get("shap_values", [])
            qs: Dict[str, Any] = {
                "feature": feat,
                "value_range": [float(np.min(dep_vals)), float(np.max(dep_vals))] if len(dep_vals) > 0 else [],
            }
            if len(shap_vals) > 0:
                shap_arr = np.asarray(shap_vals, dtype=float)
                pos_frac = float(np.mean(shap_arr > 0))
                qs["shap_sign_split"] = {"positive_fraction": round(pos_frac, 3)}
                if len(dep_vals) == len(shap_arr) and len(dep_vals) >= 4:
                    # Simple suspected threshold: where mean SHAP crosses zero
                    try:
                        mid = len(shap_arr) // 2
                        left_mean = float(np.mean(shap_arr[:mid]))
                        right_mean = float(np.mean(shap_arr[mid:]))
                        if np.sign(left_mean) != np.sign(right_mean):
                            qs["suspected_threshold_quantile"] = 0.5
                    except Exception:
                        pass
            units.append(EvidenceUnit(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                evidence_type=EvidenceType.SHAP_DEPENDENCE,
                feature_names=[feat],
                quantitative_summary=qs,
                direction="unknown",
                strength=0.3,
                reliability=0.35,
                limitations=[
                    "SHAP dependence shows local attribution patterns; confirm with PDP/ICE."
                ],
                method_name="shap_dependence",
            ))

    logger.info("Built %d evidence units from %d methods",
                len(units), len(per_method_importance))
    return units


def build_feature_evidence_profiles(
    evidence_units: List[EvidenceUnit],
    feature_columns: List[str],
    correlation_analysis: Optional[Dict[str, Any]],
    cross_method_consensus: Optional[Dict[str, Any]],
    feature_lineage: Optional[Dict[str, Any]],
) -> List[FeatureEvidenceProfile]:
    """Compute unified evidence profiles per feature.

    Each profile aggregates evidence from all methods for one feature,
    computing consensus scores, direction consistency, and derived metrics.

    Args:
        evidence_units: All evidence units from build_evidence_units().
        feature_columns: List of feature column names.
        correlation_analysis: Correlation analysis dict (for redundancy_risk).
        cross_method_consensus: Cross-method consensus dict.
        feature_lineage: Feature lineage dict (for physical_interpretability_score).

    Returns:
        List of FeatureEvidenceProfile, one per feature that has any evidence.
    """
    if not evidence_units or not feature_columns:
        logger.warning("No evidence units or feature columns; returning empty profiles.")
        return []

    profiles: List[FeatureEvidenceProfile] = []

    for feat in feature_columns:
        feat_units = [eu for eu in evidence_units if feat in eu.feature_names]
        if not feat_units:
            continue

        # Compute rank percentile: average of normalized importance ranks
        importance_units = [
            eu for eu in feat_units
            if eu.evidence_type in (
                EvidenceType.SHAP_IMPORTANCE,
                EvidenceType.PERMUTATION_IMPORTANCE,
                EvidenceType.COEFFICIENT_IMPORTANCE,
                EvidenceType.NATIVE_IMPORTANCE,
            )
        ]
        rank_percentile = 0.0
        z_score = 0.0
        if importance_units:
            n_contrib = len(importance_units)
            percentiles = []
            z_scores = []
            for iu in importance_units:
                rank = iu.quantitative_summary.get("importance_rank", 0)
                total = iu.quantitative_summary.get("total_features_evaluated", 0)
                if total > 0:
                    percentiles.append(100.0 * (1.0 - rank / total))
                strength = iu.strength
                if strength > 0:
                    z_scores.append(strength)
            rank_percentile = float(np.mean(percentiles)) if percentiles else 0.0
            z_score = float(np.mean(z_scores)) if z_scores else 0.0

        # Top-k membership: which methods have this feature in their top-10
        top_k_membership: Dict[str, bool] = {}
        for iu in importance_units:
            rank = iu.quantitative_summary.get("importance_rank", 999)
            top_k_membership[iu.method_name] = rank <= 10

        # Method agreement: per-method normalized importance
        method_agreement: Dict[str, float] = {}
        for iu in importance_units:
            method_agreement[iu.method_name] = iu.strength

        # Consensus score: fraction of methods that rank this feature in top-k
        if top_k_membership:
            consensus_score = sum(1 for v in top_k_membership.values() if v) / len(top_k_membership)
        else:
            consensus_score = 0.0

        # Direction consistency
        direction_consistency = _compute_direction_consistency(feat, feat_units)

        # Stability score from permutation std or SHAP variance
        stability_score = _compute_stability_score(feat, feat_units)

        # Redundancy risk from correlation
        redundancy_risk = _compute_redundancy_risk(feat, correlation_analysis)
        if redundancy_risk is None:
            redundancy_risk = 0.0

        # Physical interpretability score from feature lineage
        physical_interpretability_score = 0.0
        if feature_lineage:
            physical_interpretability_score = _compute_physical_interpretability(
                feat, feature_lineage)

        profiles.append(FeatureEvidenceProfile(
            feature_name=feat,
            rank_percentile=round(rank_percentile, 2),
            z_score=round(z_score, 4),
            top_k_membership=top_k_membership,
            consensus_score=round(consensus_score, 4),
            direction_consistency=round(direction_consistency, 4),
            method_agreement=method_agreement,
            stability_score=round(stability_score, 4),
            redundancy_risk=round(redundancy_risk, 4),
            physical_interpretability_score=round(physical_interpretability_score, 4),
            evidence_units=feat_units,
        ))

    # Sort by consensus_score * rank_percentile descending
    profiles.sort(key=lambda p: p.consensus_score * p.rank_percentile / 100.0, reverse=True)
    logger.info("Built %d feature evidence profiles (from %d features)",
                len(profiles), len(feature_columns))
    return profiles


def _detect_pdp_monotonicity(pdp_item: Dict[str, Any]) -> str:
    """Classify PDP trend: monotonic_increasing, monotonic_decreasing, non_monotonic_X,
    or flat."""
    values = pdp_item.get("pdp_values", [])
    if not values or len(values) < 3:
        return "insufficient_data"

    arr = np.asarray(values, dtype=float)
    rng = arr.max() - arr.min()
    if rng < 1e-12:
        return "flat"

    diffs = np.diff(arr)
    sign_changes = int(np.sum(np.abs(np.diff(np.sign(diffs))) > 0))
    total_change = arr[-1] - arr[0]

    if sign_changes == 0:
        if abs(total_change) / rng < 0.05:
            return "flat"
        return "monotonic_increasing" if total_change > 0 else "monotonic_decreasing"
    elif sign_changes == 1:
        direction = "increasing" if total_change > 0 else "decreasing"
        return f"non_monotonic_single_bend_{direction}"
    else:
        direction = "increasing" if total_change > 0 else "decreasing"
        return f"non_monotonic_multi_bend_{direction}"


def _compute_pdp_strength(pdp_item: Dict[str, Any]) -> float:
    """Compute PDP effect strength [0, 1]."""
    values = pdp_item.get("pdp_values", [])
    if not values or len(values) < 2:
        return 0.0
    arr = np.asarray(values, dtype=float)
    rng = arr.max() - arr.min()
    if rng < 1e-12:
        return 0.0
    # Normalize by range and scale: larger range -> stronger signal
    return min(rng / (abs(arr).mean() + 1e-8), 1.0)


def _compute_direction_consistency(
    feature_name: str,
    evidence_units: List[EvidenceUnit],
) -> float:
    """Fraction of evidence units that agree on direction for a feature."""
    dirs = [eu.direction for eu in evidence_units
            if eu.direction not in ("unknown", "flat")]
    if len(dirs) < 2:
        return 0.5  # Neutral when not enough data
    # Group directions: positive vs negative
    pos = sum(1 for d in dirs if d == "positive")
    neg = sum(1 for d in dirs if d == "negative")
    total = pos + neg
    if total == 0:
        return 0.5
    return max(pos, neg) / total


def _compute_stability_score(
    feature_name: str,
    evidence_units: List[EvidenceUnit],
) -> float:
    """Compute stability from permutation std and SHAP variance."""
    perm_std = 0.0
    shap_var = 0.0
    has_perm = False
    has_shap = False

    for eu in evidence_units:
        if eu.evidence_type == EvidenceType.PERMUTATION_IMPORTANCE:
            qs = eu.quantitative_summary
            mean_val = abs(qs.get("importance_value", 0.0))
            std_val = qs.get("importance_std", 0.0)
            if mean_val > 1e-12:
                perm_std = std_val / mean_val  # coefficient of variation
            has_perm = True
        elif eu.evidence_type == EvidenceType.SHAP_IMPORTANCE:
            qs = eu.quantitative_summary
            shap_var = qs.get("shap_variance", 0.0)
            has_shap = True

    if has_perm and has_shap:
        # Lower cv + lower variance = higher stability
        stability = 1.0 - min(perm_std + shap_var, 1.0)
    elif has_perm:
        stability = 1.0 - min(perm_std, 1.0)
    elif has_shap:
        stability = 1.0 - min(shap_var, 1.0)
    else:
        stability = 0.5  # Neutral

    return max(stability, 0.0)


def _compute_redundancy_risk(
    feature_name: str,
    correlation_analysis: Optional[Dict[str, Any]],
) -> float:
    """Max absolute correlation with any other feature. High = high redundancy risk."""
    if not correlation_analysis:
        return 0.0
    high_pairs = correlation_analysis.get("high_correlation_pairs", [])
    max_corr = 0.0
    for pair in high_pairs:
        f1 = pair.get("feature_1", "")
        f2 = pair.get("feature_2", "")
        if feature_name in (f1, f2):
            corr = abs(pair.get("correlation", 0.0))
            if corr > max_corr:
                max_corr = corr
    return min(max_corr, 1.0)


def _compute_physical_interpretability(
    feature_name: str,
    feature_lineage: Dict[str, Any],
) -> float:
    """Compute how interpretable a feature is based on its lineage metadata.

    Features with clear provenance (e.g., from known descriptors) score higher
    than features with opaque or missing lineage.
    """
    lineage = feature_lineage.get(feature_name, {})
    if not lineage:
        return 0.0
    score = 0.4  # Base: has lineage
    if lineage.get("source"):
        score += 0.1
    if lineage.get("description"):
        score += 0.15
    if lineage.get("transformation"):
        score += 0.1
    if lineage.get("unit"):
        score += 0.1
    if lineage.get("category") in ("composition", "structure", "elemental"):
        score += 0.15
    return min(score, 1.0)
