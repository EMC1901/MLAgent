import uuid
import logging
from typing import List, Dict, Any, Optional

from app.modules.interpretability_analysis.schemas import (
    EvidenceUnit,
    FeatureEvidenceProfile,
    ScientificHypothesis,
    ModelApplicabilityBoundary,
    AnomalyPattern,
    ScientificInsightReport,
)
from app.modules.interpretability_analysis.enums import (
    EvidenceType,
    HypothesisClaimType,
)

logger = logging.getLogger(__name__)


def generate_scientific_hypotheses(
    evidence_units: List[EvidenceUnit],
    feature_profiles: List[FeatureEvidenceProfile],
    partial_dependence: Optional[Dict[str, Any]],
    correlation_analysis: Optional[Dict[str, Any]],
    residual_analysis: Optional[Dict[str, Any]],
    systematic_errors: Optional[List[Dict[str, Any]]],
    high_error_analysis: Optional[List[Any]],
    physics_constraints: Optional[Dict[str, Any]],
    shap_interactions: Optional[List[Dict[str, Any]]],
    feature_lineage: Optional[Dict[str, Any]],
    sample_size: int,
) -> List[ScientificHypothesis]:
    """Rule-driven hypothesis generation. All rules are evaluated and results merged.

    Each rule function takes the available evidence and returns a list of
    ScientificHypothesis objects (empty list if the rule conditions are not met).

    Returns:
        List of ScientificHypothesis, sorted by confidence_score descending.
    """
    all_hypotheses: List[ScientificHypothesis] = []

    if not feature_profiles:
        logger.warning("No feature profiles available; hypothesis generation skipped.")
        return all_hypotheses

    # Rule 1: Strong association (SHAP + permutation + PDP monotonic)
    all_hypotheses.extend(_rule_shap_permutation_strong_association(
        feature_profiles, evidence_units, partial_dependence))

    # Rule 2: Importance without correlation (nonlinear/interaction)
    all_hypotheses.extend(_rule_importance_no_correlation(
        feature_profiles, correlation_analysis, evidence_units))

    # Rule 3: SHAP high but PDP non-monotonic (threshold/saturation)
    all_hypotheses.extend(_rule_shap_high_pdp_nonmonotonic(
        feature_profiles, partial_dependence, evidence_units))

    # Rule 4: Feature group pattern
    all_hypotheses.extend(_rule_feature_group_multi_important(
        feature_profiles, feature_lineage, evidence_units))

    # Rule 5: Residual range boundary
    all_hypotheses.extend(_rule_residual_range_boundary(
        residual_analysis, evidence_units))

    # Rule 6: Error concentration in extreme quantiles
    all_hypotheses.extend(_rule_error_concentration_extreme_quantiles(
        systematic_errors, evidence_units))

    # Rule 7: Physics constraint violations
    all_hypotheses.extend(_rule_physics_violation_warning(
        physics_constraints, evidence_units))

    # Rule 8: Interaction pair discovery
    all_hypotheses.extend(_rule_interaction_pair_discovery(
        shap_interactions, evidence_units))

    # Deduplicate by (claim, claim_type)
    seen = set()
    deduped: List[ScientificHypothesis] = []
    for h in all_hypotheses:
        key = (h.claim.lower().strip(), h.claim_type)
        if key not in seen:
            seen.add(key)
            deduped.append(h)
    all_hypotheses = deduped

    # Assign initial confidence heuristic before scorer runs
    for h in all_hypotheses:
        n_supporting = len(h.supporting_evidence_ids)
        n_contradicting = len(h.contradicting_evidence_ids)
        base = 0.5 if n_supporting > 0 else 0.3
        boost = min(n_supporting * 0.1, 0.3)
        penalty = min(n_contradicting * 0.15, 0.3)
        h.confidence_score = round(min(max(base + boost - penalty, 0.0), 1.0), 4)

    all_hypotheses.sort(key=lambda h: h.confidence_score, reverse=True)
    logger.info("Generated %d scientific hypotheses (%d unique after dedup)",
                len(all_hypotheses) + len(seen) - len(all_hypotheses) if len(seen) > 0 else len(all_hypotheses),
                len(all_hypotheses))
    return all_hypotheses


def generate_applicability_boundaries(
    residual_analysis: Optional[Dict[str, Any]],
    systematic_errors: Optional[List[Dict[str, Any]]],
    high_error_analysis: Optional[List[Any]],
    evidence_units: List[EvidenceUnit],
    feature_profiles: List[FeatureEvidenceProfile],
) -> List[ModelApplicabilityBoundary]:
    """Generate model applicability boundaries from residual and error evidence.

    All supporting_evidence_ids are resolved from the passed-in evidence_units
    list, never hand-crafted, so that every boundary is traceably evidence-grounded.
    """
    boundaries: List[ModelApplicabilityBoundary] = []
    residual_ev_ids = sorted([
        eu.evidence_id for eu in evidence_units
        if eu.evidence_type == EvidenceType.RESIDUAL_SEGMENT
    ])
    error_conc_ev_ids = sorted([
        eu.evidence_id for eu in evidence_units
        if eu.evidence_type == EvidenceType.ERROR_CONCENTRATION
    ])

    def _lookup_error_ev_id(feature_name: str) -> str:
        for eu in evidence_units:
            if eu.evidence_type == EvidenceType.ERROR_CONCENTRATION and feature_name in eu.feature_names:
                return eu.evidence_id
        return ""

    # From residual systematic error segments
    if residual_analysis:
        segments = residual_analysis.get("systematic_error_segments", [])
        for i, seg in enumerate(segments):
            mae = seg.get("mean_absolute_error", 0.0)
            n_samples = seg.get("n_samples", 0)
            if mae <= 0 or n_samples < 5:
                continue
            desc = seg.get("segment_description", f"segment_{i}")
            real_id = residual_ev_ids[i] if i < len(residual_ev_ids) else ""
            severity = "critical" if mae > 2.0 else ("warning" if mae > 1.0 else "info")
            boundaries.append(ModelApplicabilityBoundary(
                boundary_id=f"bnd_{uuid.uuid4().hex[:8]}",
                description=f"Model performance degrades in prediction range: {desc}. "
                            f"Mean absolute error is {mae:.4f} ({n_samples} samples).",
                feature_conditions={"prediction_range": desc},
                error_ratio=round(mae, 4),
                supporting_evidence_ids=[real_id] if real_id else [],
                severity=severity,
            ))

    # From systematic error concentration
    if systematic_errors:
        for se in systematic_errors:
            er = se.get("error_ratio_to_overall", 1.0)
            if er <= 1.5:
                continue
            feat = se.get("feature_name", "")
            if not feat:
                continue
            eid = _lookup_error_ev_id(feat)
            boundaries.append(ModelApplicabilityBoundary(
                boundary_id=f"bnd_{uuid.uuid4().hex[:8]}",
                description=f"Model error is {er:.1f}x higher than average for feature "
                            f"'{feat}' in {se.get('value_range', '?')} range "
                            f"(quantile {se.get('quantile', '?')}, {se.get('n_samples', 0)} samples). "
                            f"Possible cause: {se.get('possible_cause', 'unknown')}",
                feature_conditions={feat: se.get("value_range", "")},
                error_ratio=round(er, 2),
                supporting_evidence_ids=[eid] if eid else [],
                severity="warning" if er > 2.0 else "info",
            ))

    # From high-error samples
    if high_error_analysis:
        for he in high_error_analysis:
            try:
                ae = getattr(he, "absolute_error", 0.0) if hasattr(he, "absolute_error") else he.get("absolute_error", 0.0) if isinstance(he, dict) else 0.0
            except Exception:
                ae = 0.0
            if ae < 0.1:
                continue
            try:
                sid = getattr(he, "sample_id", "") if hasattr(he, "sample_id") else he.get("sample_id", "") if isinstance(he, dict) else ""
            except Exception:
                sid = ""
            boundaries.append(ModelApplicabilityBoundary(
                boundary_id=f"bnd_{uuid.uuid4().hex[:8]}",
                description=f"High-error sample '{sid}' with absolute error {ae:.4f} "
                            f"suggests potential applicability boundary.",
                feature_conditions={},
                error_ratio=round(ae, 4),
                supporting_evidence_ids=error_conc_ev_ids[:1] if error_conc_ev_ids else [],
                severity="info",
            ))

    logger.info("Generated %d applicability boundaries", len(boundaries))
    return boundaries


def generate_anomaly_patterns(
    high_error_analysis: Optional[List[Any]],
    systematic_errors: Optional[List[Dict[str, Any]]],
    evidence_units: List[EvidenceUnit],
) -> List[AnomalyPattern]:
    """Identify anomaly/counterexample patterns from high-error samples.

    All supporting_evidence_ids are resolved from actual EvidenceUnit objects.
    """
    patterns: List[AnomalyPattern] = []
    error_conc_ev_ids = sorted([
        eu.evidence_id for eu in evidence_units
        if eu.evidence_type == EvidenceType.ERROR_CONCENTRATION
    ])
    phys_ev_ids = sorted([
        eu.evidence_id for eu in evidence_units
        if eu.evidence_type == EvidenceType.PHYSICS_CONSTRAINT
    ])

    if high_error_analysis:
        for he in high_error_analysis[:5]:
            try:
                if hasattr(he, "sample_id"):
                    sid = he.sample_id
                    ae = he.absolute_error
                    pattern_summary = he.feature_pattern_summary
                elif isinstance(he, dict):
                    sid = he.get("sample_id", "")
                    ae = he.get("absolute_error", 0.0)
                    pattern_summary = he.get("feature_pattern_summary", "")
                else:
                    continue
            except Exception:
                continue

            if ae < 0.1:
                continue

            patterns.append(AnomalyPattern(
                pattern_id=f"anm_{uuid.uuid4().hex[:8]}",
                description=f"High-error sample '{sid}' (error={ae:.4f}) "
                            f"may represent an outlier, data quality issue, "
                            f"or novel material region. Pattern: {pattern_summary}" if pattern_summary
                            else f"High-error sample '{sid}' (error={ae:.4f}) "
                                 f"may represent an outlier or novel region.",
                sample_count=1,
                feature_signature={"sample_id": sid, "absolute_error": round(ae, 6)},
                supporting_evidence_ids=error_conc_ev_ids[:2] if error_conc_ev_ids else [],
            ))

    # Cluster similar systematic error patterns
    if systematic_errors:
        high_ratio = [se for se in systematic_errors
                      if se.get("error_ratio_to_overall", 1.0) > 2.0]
        if high_ratio:
            features_involved = [se.get("feature_name", "") for se in high_ratio]
            patterns.append(AnomalyPattern(
                pattern_id=f"anm_{uuid.uuid4().hex[:8]}",
                description=f"Systematic error concentration in features: "
                            f"{', '.join(features_involved[:5])}. "
                            f"Error rates are >2x the overall average in these regions.",
                sample_count=sum(se.get("n_samples", 0) for se in high_ratio),
                feature_signature={"affected_features": features_involved[:5]},
                supporting_evidence_ids=error_conc_ev_ids[:3] if error_conc_ev_ids else [],
            ))

    logger.info("Generated %d anomaly patterns", len(patterns))
    return patterns


def build_scientific_insight_report(
    hypotheses: List[ScientificHypothesis],
    boundaries: List[ModelApplicabilityBoundary],
    anomalies: List[AnomalyPattern],
    physics_constraints: Optional[Dict[str, Any]],
    evidence_units: List[EvidenceUnit],
    feature_profiles: List[FeatureEvidenceProfile],
    method_statuses: Dict[str, str],
    material_patterns: Optional[List[Any]] = None,
    material_mechanisms: Optional[List[Any]] = None,
) -> ScientificInsightReport:
    """Assemble the full structured scientific insight report."""
    # Executive insights: top association + mechanism hypotheses (max 5)
    exec_insights = [h for h in hypotheses
                     if h.claim_type in (HypothesisClaimType.ASSOCIATION,
                                         HypothesisClaimType.MECHANISM_HYPOTHESIS)]
    exec_insights.sort(key=lambda h: h.confidence_score, reverse=True)
    exec_insights = exec_insights[:5]

    # Mechanism candidates
    mechanisms = [h for h in hypotheses if h.claim_type == HypothesisClaimType.MECHANISM_HYPOTHESIS]
    mechanisms.sort(key=lambda h: h.confidence_score, reverse=True)

    # Physics consistency summary
    physics_summary: Dict[str, Any] = {
        "all_passed": True,
        "violation_count": 0,
        "critical_violations": 0,
    }
    if physics_constraints:
        constraints = physics_constraints.get("constraints", [])
        physics_summary["all_passed"] = physics_constraints.get("passed", True)
        physics_summary["violation_count"] = sum(
            1 for c in constraints if not c.get("passed", True))
        physics_summary["critical_violations"] = sum(
            1 for c in constraints
            if not c.get("passed", True) and c.get("severity") == "critical")
        physics_summary["constraint_details"] = [
            {"name": c.get("constraint_name", ""),
             "passed": c.get("passed", True),
             "severity": c.get("severity", "warning")}
            for c in constraints
        ]

    # Evidence graph: feature_name -> list of evidence_ids
    evidence_graph: Dict[str, Any] = {}
    for eu in evidence_units:
        for feat in eu.feature_names:
            if feat not in evidence_graph:
                evidence_graph[feat] = []
            evidence_graph[feat].append(eu.evidence_id)

    # Limitations
    limitations: List[str] = []
    if not hypotheses:
        limitations.append("No scientific hypotheses could be generated from the available evidence.")
    if not evidence_units:
        limitations.append("Insufficient evidence: no interpretability methods produced results.")
    method_count = len(method_statuses)
    if method_count < 2:
        limitations.append(
            f"Only {method_count} interpretability method(s) available; "
            "cross-method validation is limited.")
    failed_methods = [m for m, s in method_statuses.items() if s == "failed"]
    if failed_methods:
        limitations.append(f"Methods that failed: {', '.join(failed_methods)}. "
                           "Evidence from these methods is unavailable.")
    if feature_profiles and all(p.redundancy_risk > 0.7 for p in feature_profiles[:5]):
        limitations.append("Top features show high inter-correlation; "
                           "importance may be distributed across redundant features.")

    return ScientificInsightReport(
        executive_insights=exec_insights,
        ranked_hypotheses=hypotheses,
        mechanism_candidates=mechanisms,
        model_applicability_boundaries=boundaries,
        anomaly_or_counterexample_patterns=anomalies,
        material_pattern_candidates=material_patterns if material_patterns else [],
        material_mechanism_candidates=material_mechanisms if material_mechanisms else [],
        physics_consistency_summary=physics_summary,
        evidence_graph=evidence_graph,
        limitations=limitations,
        feature_profiles=feature_profiles,
    )


# ============================================================================
# Individual Rule Functions
# ============================================================================


def _rule_shap_permutation_strong_association(
    feature_profiles: List[FeatureEvidenceProfile],
    evidence_units: List[EvidenceUnit],
    partial_dependence: Optional[Dict[str, Any]],
) -> List[ScientificHypothesis]:
    """Feature high in SHAP + permutation + PDP monotonic -> strong association."""
    results: List[ScientificHypothesis] = []
    for fp in feature_profiles[:15]:  # Top 15
        if fp.consensus_score < 0.5:
            continue
        shap_in_top = fp.top_k_membership.get("shap", False)
        perm_in_top = fp.top_k_membership.get("permutation_importance", False)
        if not (shap_in_top or perm_in_top):
            continue

        # Check PDP monotonicity
        pdp_ev = [eu for eu in fp.evidence_units if eu.evidence_type == EvidenceType.PDP_1D]
        is_monotonic = False
        pdp_trend = "unknown"
        for pe in pdp_ev:
            trend = pe.quantitative_summary.get("trend", "")
            if trend.startswith("monotonic"):
                is_monotonic = True
                pdp_trend = trend
                break

        method_count = sum(1 for v in fp.top_k_membership.values() if v)
        evidence_ids = [eu.evidence_id for eu in fp.evidence_units[:5]]

        if is_monotonic:
            claim = (f"Within the observed data distribution, descriptor '{fp.feature_name}' "
                     f"shows a model-supported monotonic association with the target "
                     f"({pdp_trend}), confirmed by {method_count} importance methods "
                     f"(consensus={fp.consensus_score:.2f}). The available evidence supports "
                     f"this as an interpretation candidate, not a material design rule yet.")
            claim_type = HypothesisClaimType.ASSOCIATION
            confidence_init = 0.7 + (fp.consensus_score * 0.2)
        else:
            claim = (f"Within the observed data distribution, descriptor '{fp.feature_name}' "
                     f"shows a model-supported association with the target, identified by "
                     f"{method_count} importance methods (consensus={fp.consensus_score:.2f}). "
                     f"The available evidence supports this as an interpretation candidate, "
                     f"not a material design rule yet.")
            claim_type = HypothesisClaimType.ASSOCIATION
            confidence_init = 0.5 + (fp.consensus_score * 0.2)

        results.append(ScientificHypothesis(
            hypothesis_id=f"hyp_{uuid.uuid4().hex[:8]}",
            claim=claim,
            claim_type=claim_type,
            supporting_evidence_ids=evidence_ids,
            contradicting_evidence_ids=[],
            confidence_score=round(min(confidence_init, 0.95), 4),
            confidence_label="high" if confidence_init > 0.7 else "medium",
            scope_conditions=[f"Applies within the training data distribution for '{fp.feature_name}'."],
            validation_suggestions=[
                f"Estimate an actionable value window for '{fp.feature_name}' using PDP/ICE or SHAP dependence.",
                "Check whether the association remains under leave-family-out or external holdout validation.",
            ],
            hypothesis_pattern="shap_permutation_consensus",
        ))
    return results


def _rule_importance_no_correlation(
    feature_profiles: List[FeatureEvidenceProfile],
    correlation_analysis: Optional[Dict[str, Any]],
    evidence_units: List[EvidenceUnit],
) -> List[ScientificHypothesis]:
    """High importance but weak target correlation -> nonlinear or interaction effect."""
    results: List[ScientificHypothesis] = []
    if not correlation_analysis:
        return results

    target_corrs = {tc.get("feature_name", ""): abs(tc.get("pearson_r", 0.0))
                    for tc in correlation_analysis.get("target_correlations", [])}

    for fp in feature_profiles[:15]:
        if fp.consensus_score < 0.4:
            continue
        pearson_abs = target_corrs.get(fp.feature_name, None)
        if pearson_abs is None:
            continue
        if pearson_abs < 0.3 and fp.consensus_score > 0.5:
            evidence_ids = [eu.evidence_id for eu in fp.evidence_units[:5]]
            results.append(ScientificHypothesis(
                hypothesis_id=f"hyp_{uuid.uuid4().hex[:8]}",
                claim=(f"Feature '{fp.feature_name}' has high model importance "
                       f"(consensus={fp.consensus_score:.2f}) but weak linear correlation "
                       f"with the target (|r|={pearson_abs:.2f}). This suggests a "
                       f"non-linear relationship or interaction effect captured by the model."),
                claim_type=HypothesisClaimType.MECHANISM_HYPOTHESIS,
                supporting_evidence_ids=evidence_ids,
                contradicting_evidence_ids=[],
                confidence_score=0.55,
                confidence_label="medium",
                scope_conditions=[
                    f"Non-linearity may not generalize beyond the training distribution."],
                validation_suggestions=[
                    f"Plot PDP or ICE for '{fp.feature_name}' to visualize the non-linear pattern.",
                    f"Check SHAP dependence for interaction effects with other features.",
                ],
                hypothesis_pattern="importance_no_correlation",
            ))
    return results


def _rule_shap_high_pdp_nonmonotonic(
    feature_profiles: List[FeatureEvidenceProfile],
    partial_dependence: Optional[Dict[str, Any]],
    evidence_units: List[EvidenceUnit],
) -> List[ScientificHypothesis]:
    """SHAP high + PDP non-monotonic -> threshold/saturation/regime-dependent behavior."""
    results: List[ScientificHypothesis] = []
    for fp in feature_profiles[:15]:
        shap_in_top = fp.top_k_membership.get("shap", False)
        if not shap_in_top:
            continue
        pdp_ev = [eu for eu in fp.evidence_units if eu.evidence_type == EvidenceType.PDP_1D]
        for pe in pdp_ev:
            trend = pe.quantitative_summary.get("trend", "")
            if "non_monotonic" in trend:
                evidence_ids = [eu.evidence_id for eu in fp.evidence_units[:5]]
                results.append(ScientificHypothesis(
                    hypothesis_id=f"hyp_{uuid.uuid4().hex[:8]}",
                    claim=(f"Feature '{fp.feature_name}' has high SHAP importance but a "
                           f"non-monotonic partial dependence ({trend}). This suggests "
                           f"threshold, saturation, or regime-dependent behavior."),
                    claim_type=HypothesisClaimType.MECHANISM_HYPOTHESIS,
                    supporting_evidence_ids=evidence_ids,
                    contradicting_evidence_ids=[],
                    confidence_score=0.55,
                    confidence_label="medium",
                    scope_conditions=[
                        f"The non-monotonic relationship may only hold within the observed range."],
                    validation_suggestions=[
                        f"Investigate the physical mechanism causing the non-monotonicity in '{fp.feature_name}'.",
                        f"Consider if the non-monotonicity reflects a genuine physical effect or a model artifact.",
                    ],
                    hypothesis_pattern="shap_high_pdp_nonmonotonic",
                ))
                break  # One hypothesis per feature for this pattern
    return results


def _rule_feature_group_multi_important(
    feature_profiles: List[FeatureEvidenceProfile],
    feature_lineage: Optional[Dict[str, Any]],
    evidence_units: List[EvidenceUnit],
) -> List[ScientificHypothesis]:
    """Same feature group has multiple important features -> group-level materials pattern."""
    results: List[ScientificHypothesis] = []
    if not feature_lineage:
        return results

    group_features: Dict[str, List[FeatureEvidenceProfile]] = {}
    for fp in feature_profiles[:30]:
        lineage = feature_lineage.get(fp.feature_name, {})
        group = lineage.get("category", lineage.get("group", "other"))
        if group not in group_features:
            group_features[group] = []
        group_features[group].append(fp)

    for group, members in group_features.items():
        if len(members) >= 2 and all(m.consensus_score > 0.3 for m in members):
            evidence_ids = []
            for m in members:
                evidence_ids.extend([eu.evidence_id for eu in m.evidence_units[:2]])
            # Deduplicate evidence IDs
            evidence_ids = list(dict.fromkeys(evidence_ids))[:10]
            feature_names = [m.feature_name for m in members[:5]]
            results.append(ScientificHypothesis(
                hypothesis_id=f"hyp_{uuid.uuid4().hex[:8]}",
                claim=(f"Multiple features from the '{group}' group are important "
                       f"({', '.join(feature_names)}). This suggests that '{group}' "
                       f"as a class is meaningful for predicting the target property."),
                claim_type=HypothesisClaimType.ASSOCIATION,
                supporting_evidence_ids=evidence_ids,
                contradicting_evidence_ids=[],
                confidence_score=0.6,
                confidence_label="medium",
                scope_conditions=[f"Group-level pattern applies to the '{group}' category."],
                validation_suggestions=[
                    f"Consider feature engineering to create composite '{group}' descriptors.",
                    f"Verify if the importance is due to genuine physical relevance or feature redundancy.",
                ],
                hypothesis_pattern="feature_group_multi_important",
            ))
    return results


def _rule_residual_range_boundary(
    residual_analysis: Optional[Dict[str, Any]],
    evidence_units: List[EvidenceUnit],
) -> List[ScientificHypothesis]:
    """Residual high in specific prediction range -> model applicability boundary."""
    results: List[ScientificHypothesis] = []
    if not residual_analysis:
        return results

    segments = residual_analysis.get("systematic_error_segments", [])
    r_squared = residual_analysis.get("r_squared", 0.0)
    rmse = residual_analysis.get("rmse", 1.0)
    # Use RMSE as baseline error magnitude; residual_mean is the signed mean
    # of residuals and can be near zero for unbiased models.
    baseline_error = rmse if rmse > 1e-12 else 1.0

    for seg in segments:
        seg_mae = seg.get("mean_absolute_error", 0.0)
        n_samples = seg.get("n_samples", 0)
        if n_samples < 5 or seg_mae < baseline_error * 0.5:
            continue
        ratio = seg_mae / max(baseline_error, 1e-6)
        if ratio < 1.5:
            continue
        desc = seg.get("segment_description", "unknown range")
        res_ev_ids = [eu.evidence_id for eu in evidence_units
                      if eu.evidence_type == EvidenceType.RESIDUAL_SEGMENT]
        results.append(ScientificHypothesis(
            hypothesis_id=f"hyp_{uuid.uuid4().hex[:8]}",
            claim=(f"Model reliability boundary identified: in the prediction range "
                   f"'{desc}', the mean absolute error is {ratio:.1f}x higher than "
                   f"the RMSE baseline ({seg_mae:.4f} vs RMSE={baseline_error:.4f}). "
                   f"Model predictions in this range should be treated with caution."),
            claim_type=HypothesisClaimType.LIMITATION,
            supporting_evidence_ids=res_ev_ids[:5],
            contradicting_evidence_ids=[],
            confidence_score=0.65,
            confidence_label="medium",
            scope_conditions=[f"Boundary applies to predictions in range: {desc}."],
            validation_suggestions=[
                "Collect additional training data in this prediction range.",
                "Consider if a specialized model or calibration is needed for this regime.",
            ],
            hypothesis_pattern="residual_range_boundary",
        ))
    return results


def _rule_error_concentration_extreme_quantiles(
    systematic_errors: Optional[List[Dict[str, Any]]],
    evidence_units: List[EvidenceUnit],
) -> List[ScientificHypothesis]:
    """High-error samples concentrated in extreme feature quantiles -> extrapolation risk."""
    results: List[ScientificHypothesis] = []
    if not systematic_errors:
        return results

    for se in systematic_errors[:5]:
        er = se.get("error_ratio_to_overall", 1.0)
        if er < 2.0:
            continue
        feat = se.get("feature_name", "")
        if not feat:
            continue
        quantile = se.get("quantile", 0)
        is_extreme = quantile <= 1 or quantile >= 4  # 5-quantile system: 0 or 4 are extremes

        claim_type = HypothesisClaimType.LIMITATION if is_extreme else HypothesisClaimType.LIMITATION
        err_ev_ids = [eu.evidence_id for eu in evidence_units
                      if eu.evidence_type == EvidenceType.ERROR_CONCENTRATION
                      and feat in eu.feature_names]
        results.append(ScientificHypothesis(
            hypothesis_id=f"hyp_{uuid.uuid4().hex[:8]}",
            claim=(f"Model error is {er:.1f}x higher than average for samples where "
                   f"'{feat}' is in the {se.get('value_range', 'extreme')} range "
                   f"(quantile {quantile}). "
                   f"{'This indicates potential extrapolation risk.' if is_extreme else ''} "
                   f"Possible cause: {se.get('possible_cause', 'unknown')}."),
            claim_type=claim_type,
            supporting_evidence_ids=err_ev_ids[:5],
            contradicting_evidence_ids=[],
            confidence_score=0.5,
            confidence_label="medium" if er > 2.5 else "low",
            scope_conditions=[
                f"Warning applies when '{feat}' is in {se.get('value_range', '')}."],
            validation_suggestions=[
                f"Collect more training data for '{feat}' in the affected range.",
                "Apply prediction uncertainty quantification for samples in this regime.",
            ],
            hypothesis_pattern="error_concentration_extreme_quantiles",
        ))
    return results


def _rule_physics_violation_warning(
    physics_constraints: Optional[Dict[str, Any]],
    evidence_units: List[EvidenceUnit],
) -> List[ScientificHypothesis]:
    """Physics constraint violations -> lower confidence, reliability warning."""
    results: List[ScientificHypothesis] = []
    if not physics_constraints:
        return results

    constraints = physics_constraints.get("constraints", [])
    if not constraints:
        return results

    violations = [c for c in constraints if not c.get("passed", True)]
    if not violations:
        return results

    phys_ev_ids = [eu.evidence_id for eu in evidence_units
                   if eu.evidence_type == EvidenceType.PHYSICS_CONSTRAINT]

    for v in violations:
        severity = v.get("severity", "warning")
        n_violations = v.get("n_violations", 0)
        violation_rate = v.get("violation_rate", 0.0)
        constraint_name = v.get("constraint_name", "unknown")
        results.append(ScientificHypothesis(
            hypothesis_id=f"hyp_{uuid.uuid4().hex[:8]}",
            claim=(f"Physics constraint violation: '{constraint_name}' is violated "
                   f"in {n_violations} predictions ({violation_rate:.1%}). "
                   f"Severity: {severity}. Model predictions that violate this "
                   f"constraint should not be trusted."),
            claim_type=HypothesisClaimType.LIMITATION,
            supporting_evidence_ids=phys_ev_ids[:5],
            contradicting_evidence_ids=[],
            confidence_score=0.9,  # Physics constraints are high-certainty
            confidence_label="high",
            scope_conditions=[f"All predictions violating '{constraint_name}'."],
            validation_suggestions=[
                f"Filter out predictions that violate '{constraint_name}'.",
                "Investigate why the model produces physically impossible values.",
            ],
            hypothesis_pattern="physics_violation",
        ))
    return results


def _rule_interaction_pair_discovery(
    shap_interactions: Optional[List[Dict[str, Any]]],
    evidence_units: List[EvidenceUnit],
) -> List[ScientificHypothesis]:
    """Strong SHAP interaction pair -> coupled effects hypothesis."""
    results: List[ScientificHypothesis] = []
    if not shap_interactions:
        return results

    for si in shap_interactions[:5]:
        feat_1 = si.get("feature_1", si.get("feature_name_1", ""))
        feat_2 = si.get("feature_2", si.get("feature_name_2", ""))
        interaction_strength = si.get("interaction_strength",
                                       si.get("mean_abs_interaction", 0.0))
        if interaction_strength < 0.05:
            continue
        if not feat_1 or not feat_2:
            continue

        int_ev_ids = [eu.evidence_id for eu in evidence_units
                      if eu.evidence_type == EvidenceType.SHAP_INTERACTION]
        results.append(ScientificHypothesis(
            hypothesis_id=f"hyp_{uuid.uuid4().hex[:8]}",
            claim=(f"Strong SHAP interaction detected between '{feat_1}' and "
                   f"'{feat_2}' (strength={interaction_strength:.4f}). This suggests "
                   f"coupled physical effects where the influence of one feature "
                   f"depends on the value of the other."),
            claim_type=HypothesisClaimType.MECHANISM_HYPOTHESIS,
            supporting_evidence_ids=int_ev_ids[:5],
            contradicting_evidence_ids=[],
            confidence_score=0.5,
            confidence_label="medium",
            scope_conditions=["Interaction effects may be model-specific."],
            validation_suggestions=[
                f"Examine 2D partial dependence of '{feat_1}' and '{feat_2}'.",
                "Consider if the interaction reflects a known physical coupling mechanism.",
            ],
            hypothesis_pattern="interaction_pair_discovery",
        ))
    return results
