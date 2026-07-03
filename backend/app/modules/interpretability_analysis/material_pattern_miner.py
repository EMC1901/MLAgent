"""Phase 1: Deterministic Material Pattern Mining.

Mines structured MaterialPatternCandidates from XAI evidence without LLM.
Each pattern includes conditions, predicted effect, evidence grounding,
counterexamples, and validation suggestions.
"""

import uuid
import logging
import numpy as np
from typing import List, Dict, Any, Optional

from app.modules.interpretability_analysis.schemas import (
    EvidenceUnit,
    FeatureEvidenceProfile,
    PatternCondition,
    PatternEffect,
    PatternCounterexample,
    MaterialPatternCandidate,
)
from app.modules.interpretability_analysis.enums import EvidenceType

logger = logging.getLogger(__name__)

# Keyword-based material concept fallback map
_CONCEPT_KEYWORDS: Dict[str, str] = {
    "electronegativity": "electronegativity / bonding polarity",
    "chi": "electronegativity / bonding polarity",
    "atomic_radius": "size mismatch / atomic packing",
    "ionic_radius": "size mismatch / ionic packing",
    "radius": "size / radial descriptor",
    "volume": "structural compactness",
    "density": "structural compactness / mass density",
    "lattice": "structural / lattice descriptor",
    "valence": "electronic structure descriptor",
    "electron": "electronic structure descriptor",
    "orbital": "electronic structure descriptor",
    "band_gap": "electronic band structure",
    "formation_energy": "thermodynamic stability",
    "cohesive_energy": "cohesive / bonding energy",
    "bulk_modulus": "mechanical stiffness",
    "shear_modulus": "mechanical / shear resistance",
    "poisson": "mechanical / elastic response",
    "melting": "thermal stability",
    "conductivity": "transport property",
    "composition": "composition descriptor",
    "stoichiometry": "stoichiometric ratio",
    "weight": "mass / concentration descriptor",
    "fraction": "fractional composition",
    "temperature": "thermal condition",
    "pressure": "mechanical condition",
}


def infer_material_concept(
    feature_name: str,
    feature_lineage: Optional[Dict[str, Any]],
    registry=None,
) -> str:
    """Map a feature name to a human-readable material concept.

    Priority:
      1. feature_lineage[feature].description
      2. feature_lineage[feature].category
      3. registry.get_feature_semantics(feature)
      4. Keyword-based fallback
    """
    lineage = (feature_lineage or {}).get(feature_name, {})

    if isinstance(lineage, dict):
        desc = lineage.get("description", "")
        if desc:
            return str(desc)
        category = lineage.get("category", "")
        if category and category != "other":
            return str(category).replace("_", " ")

    # Try registry semantics
    if registry is not None:
        try:
            semantics = registry.get_feature_semantics(feature_name)
            if semantics:
                concept = semantics.get("concept", "") or semantics.get("material_concept", "")
                if concept:
                    return str(concept)
        except Exception:
            pass

    # Keyword fallback
    feat_lower = feature_name.lower()
    for keyword, concept in _CONCEPT_KEYWORDS.items():
        if keyword in feat_lower:
            return concept

    return "opaque descriptor"


# ============================================================================
# Scoring
# ============================================================================


def _score_pattern(
    pattern: MaterialPatternCandidate,
    feature_profiles: List[FeatureEvidenceProfile],
    evidence_units: List[EvidenceUnit],
    X=None,
) -> None:
    """Score a MaterialPatternCandidate in-place using weighted formula.

    confidence =
      0.25 * cross_method_support
    + 0.20 * direction_consistency
    + 0.20 * effect_size_score
    + 0.15 * sample_support
    + 0.10 * physical_interpretability
    + 0.10 * counterexample_penalty_adjusted

    Then apply downgrade rules.
    """
    # Gather profiles for features mentioned in conditions
    feature_names = {c.feature_name for c in pattern.conditions}
    relevant_profiles = [fp for fp in feature_profiles if fp.feature_name in feature_names]

    cross_method_support = 0.0
    direction_consistency = 0.0
    phys_interp = 0.0
    if relevant_profiles:
        cross_method_support = float(np.mean([fp.consensus_score for fp in relevant_profiles]))
        direction_consistency = float(np.mean([fp.direction_consistency for fp in relevant_profiles]))
        phys_interp = float(np.mean([fp.physical_interpretability_score for fp in relevant_profiles]))

    # Effect size score: from predicted_effect.effect_size, clamped to [0, 1]
    effect_size_score = min(abs(pattern.predicted_effect.effect_size), 1.0)

    # Sample support: number of evidence units backing the pattern
    sample_support = min(len(pattern.supporting_evidence_ids) / 5.0, 1.0)

    # Counterexample penalty
    n_counterexamples = len(pattern.counterexamples)
    counterexample_penalty = min(n_counterexamples * 0.15, 0.5)
    counterexample_adjusted = 1.0 - counterexample_penalty

    confidence = (
        0.25 * cross_method_support
        + 0.20 * direction_consistency
        + 0.20 * effect_size_score
        + 0.15 * sample_support
        + 0.10 * phys_interp
        + 0.10 * counterexample_adjusted
    )
    confidence = max(0.0, min(confidence, 1.0))

    # ── Downgrade rules ──
    label_cap = "high"

    if relevant_profiles and any(fp.redundancy_risk > 0.85 for fp in relevant_profiles):
        label_cap = _min_label(label_cap, "medium")

    has_pdp_or_shapdep = any(
        eu.evidence_type in (EvidenceType.PDP_1D, EvidenceType.SHAP_DEPENDENCE)
        for eu in evidence_units
        if any(f in eu.feature_names for f in feature_names)
    )
    if not has_pdp_or_shapdep:
        label_cap = _min_label(label_cap, "low")

    if relevant_profiles and all(fp.physical_interpretability_score < 0.3 for fp in relevant_profiles):
        label_cap = _min_label(label_cap, "medium")

    if pattern.counterexamples:
        # Counterexamples whose feature_signature overlaps a condition feature
        counter_in_scope = any(
            any(f in ce.feature_signature for f in feature_names)
            for ce in pattern.counterexamples
        )
        if counter_in_scope:
            confidence = max(confidence - 0.15, 0.0)

    # Method diversity check
    n_methods = len({eu.method_name for eu in evidence_units
                     if eu.evidence_id in pattern.supporting_evidence_ids})
    if n_methods <= 1:
        if label_cap == "high":
            label_cap = "medium"
        elif label_cap == "medium":
            label_cap = "low"

    label = _confidence_label_from_score(confidence)
    label = _min_label(label, label_cap)

    pattern.confidence_score = round(confidence, 4)
    pattern.confidence_label = label


def _min_label(a: str, b: str) -> str:
    order = {"low": 0, "medium": 1, "high": 2}
    return a if order.get(a, 1) <= order.get(b, 1) else b


def _confidence_label_from_score(score: float) -> str:
    if score >= 0.7:
        return "high"
    elif score >= 0.35:
        return "medium"
    return "low"


# ============================================================================
# Mining Rules
# ============================================================================


def _mine_monotonic(
    feature_profiles: List[FeatureEvidenceProfile],
    evidence_units: List[EvidenceUnit],
    partial_dependence: Optional[Dict[str, Any]],
    feature_lineage: Optional[Dict[str, Any]],
    registry=None,
) -> List[MaterialPatternCandidate]:
    """Rule 1: Single-feature monotonic association from PDP + SHAP."""
    results: List[MaterialPatternCandidate] = []
    if not partial_dependence:
        return results

    pdp_1d_list = partial_dependence.get("pdp_1d", [])
    pdp_by_feature = {p.get("feature_name", ""): p for p in pdp_1d_list}

    for fp in feature_profiles:
        if fp.consensus_score < 0.5:
            continue
        pdp_item = pdp_by_feature.get(fp.feature_name)
        if not pdp_item:
            continue

        pdp_ev = [eu for eu in fp.evidence_units if eu.evidence_type == EvidenceType.PDP_1D]
        if not pdp_ev:
            continue

        trend = pdp_ev[0].quantitative_summary.get("trend", "")
        if trend not in ("monotonic_increasing", "monotonic_decreasing"):
            continue

        pdp_vals = pdp_item.get("pdp_values", [])
        grid_vals = pdp_item.get("grid_values", [])
        pdp_delta = max(pdp_vals) - min(pdp_vals) if len(pdp_vals) >= 2 else 0.0

        direction = "increases" if trend == "monotonic_increasing" else "decreases"
        concept = infer_material_concept(fp.feature_name, feature_lineage, registry)

        # Build value range
        val_range: Dict[str, Any] = {}
        quantile_range: Optional[List[float]] = None
        if len(grid_vals) >= 2:
            val_range = {"min": round(float(np.min(grid_vals)), 4),
                         "max": round(float(np.max(grid_vals)), 4)}
            # Approximate quantile range from PDP evidence
            pdp_range = pdp_ev[0].quantitative_summary.get("pdp_range", 0)
            val_range["pdp_delta"] = round(float(pdp_delta), 4)
            quantile_range = [0.0, 1.0]

        effect_direction = "increases" if trend == "monotonic_increasing" else "decreases"
        statement = (
            f"Within the observed range ({val_range.get('min', '?')} to {val_range.get('max', '?')}), "
            f"lower '{fp.feature_name}' is associated with higher predicted target."
            if trend == "monotonic_decreasing"
            else f"Within the observed range ({val_range.get('min', '?')} to {val_range.get('max', '?')}), "
                 f"higher '{fp.feature_name}' is associated with higher predicted target."
        )

        supporting_ids = [eu.evidence_id for eu in fp.evidence_units[:5]]

        pattern = MaterialPatternCandidate(
            pattern_id=f"mp_{uuid.uuid4().hex[:8]}",
            pattern_type="monotonic",
            statement=statement,
            material_concepts=[concept],
            conditions=[
                PatternCondition(
                    feature_name=fp.feature_name,
                    material_concept=concept,
                    operator="increasing" if trend == "monotonic_increasing" else "decreasing",
                    value_range=val_range,
                    quantile_range=quantile_range,
                    source="pdp",
                )
            ],
            predicted_effect=PatternEffect(
                target_direction=effect_direction,
                effect_size=round(abs(pdp_delta), 4),
                effect_unit="pdp_delta",
                evidence_basis="pdp_delta",
            ),
            supporting_evidence_ids=supporting_ids,
            scope_conditions=[
                f"Applies within the training data distribution for '{fp.feature_name}'."
            ],
            validation_suggestions=[
                f"Estimate an actionable value window for '{fp.feature_name}' using PDP/ICE or SHAP dependence.",
                "Check whether the monotonic association remains under leave-family-out or external holdout validation.",
            ],
            limitations=[
                "PDP assumes feature independence; relationship may differ for correlated features.",
                "Monotonicity in PDP does not guarantee physical monotonicity.",
            ],
        )
        results.append(pattern)

    return results


def _mine_threshold(
    feature_profiles: List[FeatureEvidenceProfile],
    evidence_units: List[EvidenceUnit],
    partial_dependence: Optional[Dict[str, Any]],
    shap_dependence: Optional[List[Dict[str, Any]]],
    feature_lineage: Optional[Dict[str, Any]],
    registry=None,
) -> List[MaterialPatternCandidate]:
    """Rule 2: Threshold/saturation from PDP non-monotonic or SHAP dependence sign-crossing."""
    results: List[MaterialPatternCandidate] = []

    # Source A: PDP non-monotonic single-bend
    if partial_dependence:
        pdp_1d_list = partial_dependence.get("pdp_1d", [])
        for pdp_item in pdp_1d_list:
            feat = pdp_item.get("feature_name", "")
            if not feat:
                continue
            pdp_vals = pdp_item.get("pdp_values", [])
            grid_vals = pdp_item.get("grid_values", [])
            if len(grid_vals) < 5 or len(pdp_vals) < 5:
                continue

            fp = next((p for p in feature_profiles if p.feature_name == feat), None)
            if not fp:
                continue

            pdp_ev = [eu for eu in fp.evidence_units if eu.evidence_type == EvidenceType.PDP_1D]
            if not pdp_ev:
                continue

            trend = pdp_ev[0].quantitative_summary.get("trend", "")
            if "non_monotonic" not in trend:
                continue

            # Find the bend point (where monotonicity changes)
            arr = np.asarray(pdp_vals, dtype=float)
            diffs = np.diff(arr)
            sign_changes = np.where(np.diff(np.sign(diffs)) != 0)[0]
            bend_idx = int(sign_changes[0]) + 1 if len(sign_changes) > 0 else len(arr) // 2
            threshold_val = float(grid_vals[min(bend_idx, len(grid_vals) - 1)])
            quantile_approx = bend_idx / max(len(grid_vals) - 1, 1)

            direction = "increasing" if arr[-1] > arr[0] else "decreasing"
            direction_word = "increases" if arr[-1] > arr[0] else "decreases"
            concept = infer_material_concept(feat, feature_lineage, registry)

            supporting_ids = [eu.evidence_id for eu in fp.evidence_units[:5]]
            pdp_delta = float(arr.max() - arr.min())

            statement = (
                f"The model suggests a transition near '{feat}' ≈ {threshold_val:.3g}; "
                f"below this point the descriptor contributes weakly, "
                f"above it the predicted target {direction_word}."
            )

            pattern = MaterialPatternCandidate(
                pattern_id=f"mp_{uuid.uuid4().hex[:8]}",
                pattern_type="threshold",
                statement=statement,
                material_concepts=[concept],
                conditions=[
                    PatternCondition(
                        feature_name=feat,
                        material_concept=concept,
                        operator="between",
                        value_range={"threshold": round(threshold_val, 4)},
                        quantile_range=[round(quantile_approx - 0.15, 2), round(quantile_approx + 0.15, 2)],
                        source="pdp",
                    )
                ],
                predicted_effect=PatternEffect(
                    target_direction="increases" if direction == "increasing" else "decreases",
                    effect_size=round(pdp_delta, 4),
                    effect_unit="pdp_delta",
                    evidence_basis="pdp_delta",
                ),
                supporting_evidence_ids=supporting_ids,
                scope_conditions=[f"Transition candidate near '{feat}' ≈ {threshold_val:.3g}; not a confirmed physical critical point."],
                validation_suggestions=[
                    f"Validate the suspected transition near '{feat}' ≈ {threshold_val:.3g} with subgroup analysis.",
                    "Check whether this transition is robust under different model seeds or holdout splits.",
                ],
                limitations=[
                    "This is a candidate threshold from a single model; it may reflect noise or limited sampling.",
                ],
            )
            results.append(pattern)

    # Source B: SHAP dependence sign-crossing
    if shap_dependence:
        for dep in shap_dependence:
            feat = dep.get("feature_name", dep.get("feature", ""))
            if not feat:
                continue
            dep_vals = dep.get("feature_values", [])
            shap_vals = dep.get("shap_values", [])
            if len(dep_vals) < 4 or len(shap_vals) < 4:
                continue

            fp = next((p for p in feature_profiles if p.feature_name == feat), None)
            shap_arr = np.asarray(shap_vals, dtype=float)
            if np.all(shap_arr >= 0) or np.all(shap_arr <= 0):
                continue  # No sign change, no threshold

            # Find approximate crossing point
            sign = shap_arr >= 0
            crossings = np.where(np.diff(sign.astype(int)) != 0)[0]
            if len(crossings) == 0:
                continue

            cross_idx = int(crossings[0]) + 1
            cross_val = float(dep_vals[min(cross_idx, len(dep_vals) - 1)])
            quantile_approx = cross_idx / max(len(dep_vals) - 1, 1)

            # Already handled by PDP non-monotonic? Skip if so
            already_covered = any(
                c.feature_name == feat for p in results for c in p.conditions
            )
            if already_covered:
                continue

            concept = infer_material_concept(feat, feature_lineage, registry)
            dep_ev_ids = [eu.evidence_id for eu in evidence_units
                          if eu.evidence_type == EvidenceType.SHAP_DEPENDENCE and feat in eu.feature_names]

            shap_range = float(np.ptp(shap_arr))
            statement = (
                f"SHAP dependence suggests a sign transition for '{feat}' near {cross_val:.3g}; "
                f"the model's local attribution changes direction around this value."
            )

            pattern = MaterialPatternCandidate(
                pattern_id=f"mp_{uuid.uuid4().hex[:8]}",
                pattern_type="threshold",
                statement=statement,
                material_concepts=[concept],
                conditions=[
                    PatternCondition(
                        feature_name=feat,
                        material_concept=concept,
                        operator="between",
                        value_range={"suspected_threshold": round(cross_val, 4)},
                        quantile_range=[round(max(0, quantile_approx - 0.1), 2),
                                        round(min(1, quantile_approx + 0.1), 2)],
                        source="shap_dependence",
                    )
                ],
                predicted_effect=PatternEffect(
                    target_direction="uncertain",
                    effect_size=round(shap_range, 4),
                    effect_unit="shap_range",
                    evidence_basis="predicted_target",
                ),
                supporting_evidence_ids=dep_ev_ids[:5] if dep_ev_ids else [],
                scope_conditions=[f"SHAP sign transition candidate near {cross_val:.3g}; confirm with PDP or ICE."],
                validation_suggestions=[
                    f"Plot PDP or ICE for '{feat}' to confirm the suspected transition.",
                ],
                limitations=[
                    "SHAP dependence sign changes can be noisy; validate with multiple methods.",
                ],
            )
            results.append(pattern)

    return results


def _mine_window(
    feature_profiles: List[FeatureEvidenceProfile],
    evidence_units: List[EvidenceUnit],
    partial_dependence: Optional[Dict[str, Any]],
    feature_lineage: Optional[Dict[str, Any]],
    registry=None,
) -> List[MaterialPatternCandidate]:
    """Rule 3: Window/peak mode — PDP maximum in middle, not at boundaries."""
    results: List[MaterialPatternCandidate] = []
    if not partial_dependence:
        return results

    pdp_1d_list = partial_dependence.get("pdp_1d", [])
    for pdp_item in pdp_1d_list:
        feat = pdp_item.get("feature_name", "")
        if not feat:
            continue
        pdp_vals = pdp_item.get("pdp_values", [])
        grid_vals = pdp_item.get("grid_values", [])
        if len(pdp_vals) < 5 or len(grid_vals) < 5:
            continue

        arr = np.asarray(pdp_vals, dtype=float)
        max_idx = int(np.argmax(arr))
        total = len(arr)

        # Peak must be in the middle 60% (not at boundaries)
        if max_idx < total * 0.2 or max_idx > total * 0.8:
            continue

        peak_val = float(grid_vals[max_idx])
        edge_max = max(float(arr[0]), float(arr[-1]))
        peak_drop = float(arr[max_idx]) - edge_max

        if peak_drop < 0.02:  # Too flat to call a window
            continue

        fp = next((p for p in feature_profiles if p.feature_name == feat), None)
        if not fp or fp.consensus_score < 0.3:
            continue

        concept = infer_material_concept(feat, feature_lineage, registry)
        supporting_ids = [eu.evidence_id for eu in fp.evidence_units[:5]]

        # Window range: 15% around peak
        lo_idx = max(0, max_idx - max(1, total // 6))
        hi_idx = min(total - 1, max_idx + max(1, total // 6))
        lo_val = float(grid_vals[lo_idx])
        hi_val = float(grid_vals[hi_idx])

        statement = (
            f"Intermediate '{feat}' ({lo_val:.3g} to {hi_val:.3g}) appears favorable; "
            f"both low and high extremes show weaker predicted response."
        )

        pattern = MaterialPatternCandidate(
            pattern_id=f"mp_{uuid.uuid4().hex[:8]}",
            pattern_type="window",
            statement=statement,
            material_concepts=[concept],
            conditions=[
                PatternCondition(
                    feature_name=feat,
                    material_concept=concept,
                    operator="between",
                    value_range={"min": round(lo_val, 4), "max": round(hi_val, 4), "peak_value": round(peak_val, 4)},
                    quantile_range=[round(lo_idx / max(total - 1, 1), 2),
                                    round(hi_idx / max(total - 1, 1), 2)],
                    source="pdp",
                )
            ],
            predicted_effect=PatternEffect(
                target_direction="peaks",
                effect_size=round(peak_drop, 4),
                effect_unit="pdp_delta",
                evidence_basis="pdp_delta",
            ),
            supporting_evidence_ids=supporting_ids,
            scope_conditions=[f"Favorable window candidate for '{feat}' in [{lo_val:.3g}, {hi_val:.3g}]."],
            validation_suggestions=[
                f"Validate the favorable window for '{feat}' using subgroup analysis on held-out data.",
                "Check if the window reflects a genuine physical optimum or a model artifact.",
            ],
            limitations=[
                "Window modes in PDP can arise from sampling noise; confirm with ICE plots.",
            ],
        )
        results.append(pattern)

    return results


def _mine_interaction(
    feature_profiles: List[FeatureEvidenceProfile],
    evidence_units: List[EvidenceUnit],
    shap_interactions: Optional[List[Dict[str, Any]]],
    partial_dependence: Optional[Dict[str, Any]],
    feature_lineage: Optional[Dict[str, Any]],
    registry=None,
) -> List[MaterialPatternCandidate]:
    """Rule 4: Interaction pairs from SHAP interaction + optional 2D PDP."""
    results: List[MaterialPatternCandidate] = []
    if not shap_interactions:
        return results

    pdp_2d_list = partial_dependence.get("pdp_2d", []) if partial_dependence else []
    pdp_2d_index = {}
    for p2 in pdp_2d_list:
        key = tuple(sorted([p2.get("feature_1", ""), p2.get("feature_2", "")]))
        pdp_2d_index[key] = p2

    for si in shap_interactions:
        f1 = si.get("feature_1", "")
        f2 = si.get("feature_2", "")
        interaction_strength = si.get("interaction_strength", 0.0)
        if interaction_strength < 0.03 or not f1 or not f2:
            continue

        c1 = infer_material_concept(f1, feature_lineage, registry)
        c2 = infer_material_concept(f2, feature_lineage, registry)

        int_ev_ids = [eu.evidence_id for eu in evidence_units
                      if eu.evidence_type == EvidenceType.SHAP_INTERACTION
                      and f1 in eu.feature_names and f2 in eu.feature_names]

        # Check 2D PDP
        pair_key = tuple(sorted([f1, f2]))
        pdp_2d = pdp_2d_index.get(pair_key)
        has_2d_pdp = pdp_2d is not None

        if has_2d_pdp and pdp_2d:
            matrix = pdp_2d.get("pdp_matrix", [])
            grid1 = pdp_2d.get("grid_1", [])
            grid2 = pdp_2d.get("grid_2", [])
            if matrix and len(matrix) > 0 and len(matrix[0]) > 0:
                flat = [v for row in matrix for v in row]
                max_val = max(flat)
                min_val = min(flat)
                effect_size = max_val - min_val
                # Extract the grid region of maximum response
                max_flat_idx = flat.index(max_val)
                ncols = len(matrix[0])
                max_row = max_flat_idx // ncols
                max_col = max_flat_idx % ncols
                if grid1 and grid2 and max_row < len(grid2) and max_col < len(grid1):
                    g1_val = grid1[max_col]
                    g2_val = grid2[max_row]
                    statement = (
                        f"'{f1}' and '{f2}' show a coupled effect: "
                        f"2D PDP peaks near '{f1}' ≈ {g1_val:.3g}, '{f2}' ≈ {g2_val:.3g}. "
                        f"This suggests an interaction where the descriptors jointly influence the target."
                    )
                else:
                    statement = (
                        f"'{f1}' and '{f2}' show a coupled effect: "
                        f"2D PDP shows a non-flat response surface (range={effect_size:.3g}), "
                        f"suggesting a descriptor interaction."
                    )
                confidence_init = 0.55
            else:
                effect_size = interaction_strength
                statement = (
                    f"SHAP interaction detected between '{f1}' ({c1}) and '{f2}' ({c2}) "
                    f"(strength={interaction_strength:.3f}). This suggests coupled effects "
                    f"where one descriptor's influence depends on the other's value."
                )
                confidence_init = 0.4
        else:
            effect_size = interaction_strength
            statement = (
                f"SHAP interaction detected between '{f1}' ({c1}) and '{f2}' ({c2}) "
                f"(strength={interaction_strength:.3f}). Without 2D PDP this is a weak "
                f"candidate; validate with bivariate analysis."
            )
            confidence_init = 0.35

        # Build conditions from available data
        conditions: List[PatternCondition] = []
        _matrix_ok = has_2d_pdp and pdp_2d and matrix and len(matrix) > 0 and len(matrix[0]) > 0
        _peak_ok = _matrix_ok and grid1 and grid2 and max_row < len(grid2) and max_col < len(grid1)

        if _peak_ok:
            # Derive operator and value_range from actual peak position
            n_rows = len(grid2)
            n_cols = len(grid1)
            f1_frac = max_col / max(n_cols - 1, 1)
            f2_frac = max_row / max(n_rows - 1, 1)

            def _op(frac):
                if frac < 0.25:
                    return "low"
                elif frac > 0.75:
                    return "high"
                else:
                    return "between"

            conditions = [
                PatternCondition(
                    feature_name=f1,
                    material_concept=c1,
                    operator=_op(f1_frac),
                    value_range={"peak_value": round(grid1[max_col], 4)},
                    quantile_range=[round(max(0, f1_frac - 0.1), 2), round(min(1, f1_frac + 0.1), 2)],
                    source="interaction",
                ),
                PatternCondition(
                    feature_name=f2,
                    material_concept=c2,
                    operator=_op(f2_frac),
                    value_range={"peak_value": round(grid2[max_row], 4)},
                    quantile_range=[round(max(0, f2_frac - 0.1), 2), round(min(1, f2_frac + 0.1), 2)],
                    source="interaction",
                ),
            ]
        else:
            # No 2D PDP — weak conditions only, no specific low/high claims
            conditions = [
                PatternCondition(
                    feature_name=f1,
                    material_concept=c1,
                    operator="",
                    value_range={},
                    source="interaction",
                ),
                PatternCondition(
                    feature_name=f2,
                    material_concept=c2,
                    operator="",
                    value_range={},
                    source="interaction",
                ),
            ]

        pattern = MaterialPatternCandidate(
            pattern_id=f"mp_{uuid.uuid4().hex[:8]}",
            pattern_type="interaction",
            statement=statement,
            material_concepts=[c1, c2],
            conditions=conditions,
            predicted_effect=PatternEffect(
                target_direction="uncertain",
                effect_size=round(effect_size, 4),
                effect_unit="interaction_strength",
                evidence_basis="predicted_target",
            ),
            supporting_evidence_ids=int_ev_ids[:5] if int_ev_ids else [],
            scope_conditions=["Interaction effects may be model-specific."],
            validation_suggestions=[
                f"Examine 2D partial dependence of '{f1}' and '{f2}' to confirm the interaction.",
                "Consider if the interaction reflects a known physical coupling mechanism.",
            ],
            limitations=[
                "SHAP interaction is approximated from SHAP-value covariance.",
                "Without 2D PDP confirmation, treat as a weak candidate.",
            ],
        )
        results.append(pattern)

    return results


def _mine_counterexample_boundary(
    feature_profiles: List[FeatureEvidenceProfile],
    evidence_units: List[EvidenceUnit],
    high_error_analysis: Optional[List[Any]],
    systematic_errors: Optional[List[Dict[str, Any]]],
    feature_lineage: Optional[Dict[str, Any]],
    registry=None,
) -> List[MaterialPatternCandidate]:
    """Rule 5: Counterexample / applicability boundary patterns."""
    results: List[MaterialPatternCandidate] = []

    err_ev_ids = [eu.evidence_id for eu in evidence_units
                  if eu.evidence_type == EvidenceType.ERROR_CONCENTRATION]

    # From systematic errors
    if systematic_errors:
        for se in systematic_errors:
            er = se.get("error_ratio_to_overall", 1.0)
            if er < 1.5:
                continue
            feat = se.get("feature_name", "")
            if not feat:
                continue

            concept = infer_material_concept(feat, feature_lineage, registry)
            value_range = se.get("value_range", "")
            quantile = se.get("quantile", 0)
            n_samples = se.get("n_samples", 0)

            statement = (
                f"Model reliability boundary: prediction error is {er:.1f}x higher "
                f"for '{feat}' in {value_range} (quantile {quantile}, {n_samples} samples). "
                f"Predictions in this region should carry lower confidence."
            )

            pattern = MaterialPatternCandidate(
                pattern_id=f"mp_{uuid.uuid4().hex[:8]}",
                pattern_type="boundary",
                statement=statement,
                material_concepts=[concept],
                conditions=[
                    PatternCondition(
                        feature_name=feat,
                        material_concept=concept,
                        operator="outside" if quantile <= 1 or quantile >= 3 else "between",
                        value_range={"value_range": value_range},
                        quantile_range=[max(0, quantile - 0.5) / 5.0, min(5, quantile + 0.5) / 5.0],
                        source="subgroup_contrast",
                    )
                ],
                predicted_effect=PatternEffect(
                    target_direction="uncertain",
                    effect_size=round(er, 2),
                    effect_unit="error_ratio",
                    evidence_basis="observed_target",
                ),
                supporting_evidence_ids=err_ev_ids[:3] if err_ev_ids else [],
                scope_conditions=[f"Boundary applies to '{feat}' in {value_range}."],
                validation_suggestions=[
                    f"Collect more training data for '{feat}' in {value_range}.",
                    "Apply prediction uncertainty quantification for samples in this regime.",
                ],
                limitations=[
                    "Error concentration may be sensitive to binning strategy.",
                    "This is a reliability warning, not a material design rule.",
                ],
            )
            results.append(pattern)

    # From high-error samples as counterexamples.
    # Extract feature names from error summaries and attach only to boundary
    # patterns that share at least one feature.  Unmatched counterexamples get
    # a standalone collector pattern — never force-attached to an unrelated pattern.
    if high_error_analysis:
        # Build a set of known feature names for text matching
        known_features: set = set()
        for fp in feature_profiles:
            known_features.add(fp.feature_name)
        if feature_lineage:
            known_features.update(feature_lineage.keys())

        counterexamples: List[PatternCounterexample] = []
        for he in high_error_analysis[:5]:
            try:
                if hasattr(he, "sample_id"):
                    sid = he.sample_id
                    ae = he.absolute_error
                    summary = he.feature_pattern_summary
                    factors = he.possible_error_factors
                elif isinstance(he, dict):
                    sid = he.get("sample_id", "")
                    ae = he.get("absolute_error", 0.0)
                    summary = he.get("feature_pattern_summary", "")
                    factors = he.get("possible_error_factors", [])
                else:
                    continue
            except Exception:
                continue

            if ae < 0.1:
                continue

            # Extract feature names from summary/factors text by matching
            # against known feature names
            search_text = f"{summary} {' '.join(factors if factors else [])}".lower()
            matched_feats: Dict[str, Any] = {
                "sample_id": sid,
                "absolute_error": round(ae, 6),
            }
            for fname in known_features:
                if fname.lower() in search_text:
                    matched_feats[fname] = "implicated"

            counterexamples.append(PatternCounterexample(
                description=f"High-error sample '{sid}' (error={ae:.4f}): {summary}",
                sample_count=1,
                feature_signature=matched_feats,
                supporting_evidence_ids=err_ev_ids[:2] if err_ev_ids else [],
            ))

        if counterexamples:
            # Attach to boundary patterns whose condition feature_names overlap
            # with the counterexample's feature_signature
            unattached: List[PatternCounterexample] = []
            for ce in counterexamples:
                sig_feats = set(ce.feature_signature.keys()) - {"sample_id", "absolute_error"}
                matched = False
                for pattern in results:
                    pattern_feats = {c.feature_name for c in pattern.conditions}
                    if pattern_feats & sig_feats:
                        pattern.counterexamples.append(ce)
                        matched = True
                        break
                if not matched:
                    unattached.append(ce)

            # Unmatched counterexamples → standalone collector (never force-attach)
            if unattached:
                collector = MaterialPatternCandidate(
                    pattern_id=f"mp_{uuid.uuid4().hex[:8]}",
                    pattern_type="boundary",
                    statement=f"High-error samples ({len(unattached)}) suggest potential reliability boundaries outside the model's confident region.",
                    material_concepts=[],
                    conditions=[],
                    predicted_effect=PatternEffect(
                        target_direction="uncertain",
                        effect_size=0.0,
                        effect_unit="error_ratio",
                        evidence_basis="observed_target",
                    ),
                    supporting_evidence_ids=err_ev_ids[:3] if err_ev_ids else [],
                    counterexamples=unattached,
                    scope_conditions=["High-error samples may indicate extrapolation or data quality issues."],
                    validation_suggestions=["Review high-error samples for measurement errors or novel regions."],
                    limitations=["Counterexamples collected from high-error analysis."],
                )
                results.append(collector)

    return results


# ============================================================================
# Main Entry Point
# ============================================================================


def mine_material_patterns(
    X,
    y_true,
    y_pred,
    feature_profiles: List[FeatureEvidenceProfile],
    evidence_units: List[EvidenceUnit],
    partial_dependence: Optional[Dict[str, Any]],
    shap_dependence: Optional[List[Dict[str, Any]]],
    shap_interactions: Optional[List[Dict[str, Any]]],
    correlation_analysis: Optional[Dict[str, Any]],
    high_error_analysis: Optional[List[Any]],
    systematic_errors: Optional[List[Dict[str, Any]]],
    feature_lineage: Optional[Dict[str, Any]],
    target_name: str = "",
    material_domain: Optional[str] = None,
    max_patterns: int = 10,
) -> List[MaterialPatternCandidate]:
    """Mine deterministic MaterialPatternCandidates from XAI evidence.

    This is the Phase 1 core function. It applies 5 rule classes to the
    available evidence and returns scored, structured pattern candidates.
    No LLM is called.
    """
    # Lazy import to avoid circular dependency at module level
    try:
        from app.modules.interpretability_analysis.physics_rule_registry import get_registry
        registry = get_registry()
    except Exception:
        registry = None

    all_patterns: List[MaterialPatternCandidate] = []

    # Rule 1: Monotonic
    all_patterns.extend(_mine_monotonic(
        feature_profiles, evidence_units, partial_dependence, feature_lineage, registry,
    ))

    # Rule 2: Threshold / saturation
    all_patterns.extend(_mine_threshold(
        feature_profiles, evidence_units, partial_dependence, shap_dependence,
        feature_lineage, registry,
    ))

    # Rule 3: Window / peak
    all_patterns.extend(_mine_window(
        feature_profiles, evidence_units, partial_dependence, feature_lineage, registry,
    ))

    # Rule 4: Interaction
    all_patterns.extend(_mine_interaction(
        feature_profiles, evidence_units, shap_interactions, partial_dependence,
        feature_lineage, registry,
    ))

    # Rule 5: Counterexample / boundary
    all_patterns.extend(_mine_counterexample_boundary(
        feature_profiles, evidence_units, high_error_analysis, systematic_errors,
        feature_lineage, registry,
    ))

    # Score all patterns
    for p in all_patterns:
        _score_pattern(p, feature_profiles, evidence_units, X)

    # Sort by confidence_score descending
    all_patterns.sort(key=lambda p: p.confidence_score, reverse=True)

    # Deduplicate by statement (approximate)
    seen = set()
    deduped: List[MaterialPatternCandidate] = []
    for p in all_patterns:
        key = p.statement.lower().strip()[:120]
        if key not in seen:
            seen.add(key)
            deduped.append(p)

    patterns = deduped[:max_patterns]
    logger.info("Material pattern mining complete — %d candidates (from %d raw, capped at %d)",
                len(patterns), len(all_patterns), max_patterns)
    return patterns
