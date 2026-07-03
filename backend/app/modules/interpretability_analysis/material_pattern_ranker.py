"""Phase 3b: Material Pattern Refinement and Ranking.

Refines MaterialPatternCandidates after validation by:
  - Computing a multi-factor scientific quality score
  - Applying downgrade rules for weak evidence
  - Deduplicating near-identical patterns
  - Separating boundary/reliability warnings from design rules
  - Assigning display priorities

The output is a sorted, deduplicated list ready for the ScientificInsightReport.
"""

import logging
from typing import List, Dict, Any, Optional

from app.modules.interpretability_analysis.schemas import (
    MaterialPatternCandidate,
    PatternScientificScore,
    FeatureEvidenceProfile,
    EvidenceUnit,
)

logger = logging.getLogger(__name__)

# Scientific score weights (sum to 1.0)
W_VALIDATION = 0.25
W_ROBUSTNESS = 0.20
W_EFFECT_SIZE = 0.20
W_SAMPLE_SUPPORT = 0.15
W_PHYS_INTERP = 0.10
W_ACTIONABILITY = 0.10


def refine_and_rank_material_patterns(
    patterns: List[MaterialPatternCandidate],
    feature_profiles: List[FeatureEvidenceProfile],
    evidence_units: List[EvidenceUnit],
    max_patterns: int = 10,
) -> List[MaterialPatternCandidate]:
    """Score, downgrade, deduplicate, and rank material pattern candidates.

    The pipeline:
      1. Compute scientific_score for every pattern.
      2. Apply downgrade rules (fail, small sample, no PDP/SHAP, opaque, boundary).
      3. Deduplicate near-identical patterns.
      4. Sort by scientific_score.total descending.
      5. Separate boundary patterns (reliability warnings) from design rules.
      6. Assign display_priority (0 = top design rule, 999 = boundary/unranked).
      7. Cap at max_patterns.

    Args:
        patterns: Validated MaterialPatternCandidates.
        feature_profiles: Per-feature evidence profiles.
        evidence_units: All evidence units.
        max_patterns: Maximum number of top-ranked patterns to include.

    Returns:
        Sorted list with scientific_score and display_priority populated.
    """
    if not patterns:
        return patterns

    # Build lookup maps
    profile_map: Dict[str, FeatureEvidenceProfile] = {
        fp.feature_name: fp for fp in feature_profiles
    }

    # --- Step 1: Score every pattern ---
    for p in patterns:
        p.scientific_score = _compute_scientific_score(p, profile_map, evidence_units)

    # --- Step 2: Apply downgrade rules ---
    for p in patterns:
        _apply_downgrades(p, profile_map, evidence_units)

    # --- Step 3: Deduplicate ---
    patterns = _deduplicate_patterns(patterns)

    # --- Step 4: Sort ---
    patterns.sort(
        key=lambda p: p.scientific_score.total if p.scientific_score else 0.0,
        reverse=True,
    )

    # --- Step 5: Separate boundary patterns ---
    design_rules = [p for p in patterns if p.pattern_type != "boundary"]
    boundaries = [p for p in patterns if p.pattern_type == "boundary"]

    # --- Step 6: Assign display_priority ---
    # Design rules ranked 0..N-1; boundaries start after design rules
    for i, p in enumerate(design_rules):
        p.display_priority = i
    for i, p in enumerate(boundaries):
        p.display_priority = len(design_rules) + i

    # --- Step 7: Filter out failed non-boundary patterns ---
    design_rules = [
        p for p in design_rules
        if p.validation_status not in ("fail",)
    ]

    # Sort boundaries by severity (error_ratio descending), then by score
    boundaries.sort(
        key=lambda p: (
            -(p.scientific_score.effect_size if p.scientific_score else 0.0),
            -(p.scientific_score.total if p.scientific_score else 0.0),
        ),
    )

    # Merge: design rules first, then boundaries (reliability warnings)
    result = design_rules[:max_patterns]
    boundary_slots = max(0, max_patterns - len(result))
    result.extend(boundaries[:boundary_slots])

    # Re-assign display_priority after final ordering
    for i, p in enumerate(result):
        p.display_priority = i
    for p in patterns:
        if p not in result:
            p.display_priority = 999  # Did not make the cut

    logger.info(
        "Ranking complete: %d design rules + %d boundaries in top %d (from %d total)",
        min(len(design_rules), max_patterns),
        min(len(boundaries), boundary_slots),
        max_patterns,
        len(patterns),
    )
    return result


# ============================================================================
# Scientific Score Computation
# ============================================================================


def _compute_scientific_score(
    pattern: MaterialPatternCandidate,
    profile_map: Dict[str, FeatureEvidenceProfile],
    evidence_units: List[EvidenceUnit],
) -> PatternScientificScore:
    """Compute multi-factor scientific quality score."""

    # 1. Validation support
    vs_map = {"pass": 1.0, "weak": 0.5, "fail": 0.2, "unvalidated": 0.3, "not_applicable": 0.6}
    validation_support = vs_map.get(pattern.validation_status, 0.3)

    # 2. Robustness: bootstrap CI + ICE agreement
    robustness = 0.5  # default
    for vr in pattern.validation_results:
        if vr.validation_type == "bootstrap" and vr.status in ("pass", "weak"):
            if vr.metrics.get("ci_excludes_zero"):
                robustness = max(robustness, 1.0)
            else:
                robustness = max(robustness, 0.4)
        if vr.validation_type == "ice_consistency":
            agr = vr.metrics.get("agreement_ratio", 0.0)
            robustness = max(robustness, min(agr, 1.0))

    # 3. Effect size: normalized from predicted effect
    raw_effect = abs(pattern.predicted_effect.effect_size)
    effect_size = min(raw_effect / 0.5, 1.0) if raw_effect > 0 else 0.3

    # 4. Sample support
    ss = pattern.sample_support
    if ss and ss.in_scope_count > 0:
        total = max(ss.in_scope_count + ss.out_scope_count, 1)
        # Logistic-like saturation
        frac = ss.in_scope_count / total
        count_factor = min(ss.in_scope_count / 30.0, 1.0)
        sample_support = 0.5 * frac + 0.5 * count_factor
    else:
        sample_support = 0.3

    # 5. Physical interpretability: from feature profiles
    condition_features = [c.feature_name for c in pattern.conditions if c.feature_name]
    phys_scores = []
    for feat in condition_features:
        fp = profile_map.get(feat)
        if fp:
            phys_scores.append(fp.physical_interpretability_score)
        elif pattern.material_concepts and any(
            "opaque" not in mc.lower() for mc in pattern.material_concepts
        ):
            phys_scores.append(0.6)
        else:
            phys_scores.append(0.2)
    physical_interpretability = (
        sum(phys_scores) / len(phys_scores) if phys_scores else 0.3
    )

    # 6. Actionability: pattern_type heuristic
    actionability_map = {
        "threshold": 0.9,
        "window": 0.85,
        "monotonic": 0.6,
        "interaction": 0.5,
        "subgroup": 0.4,
        "boundary": 0.3,
    }
    actionability = actionability_map.get(pattern.pattern_type, 0.4)

    # 7. Counterexample penalty
    counterexample_penalty = min(len(pattern.counterexamples) * 0.1, 0.4)

    # Weighted total
    total = (
        W_VALIDATION * validation_support
        + W_ROBUSTNESS * robustness
        + W_EFFECT_SIZE * effect_size
        + W_SAMPLE_SUPPORT * sample_support
        + W_PHYS_INTERP * physical_interpretability
        + W_ACTIONABILITY * actionability
        - counterexample_penalty
    )
    total = max(total, 0.0)

    # Build rank reason
    reason_parts = []
    if pattern.validation_status == "pass":
        reason_parts.append("validation passed")
    elif pattern.validation_status == "weak":
        reason_parts.append("validation weak")
    elif pattern.validation_status == "fail":
        reason_parts.append("validation failed")
    if ss and ss.in_scope_count >= 20:
        reason_parts.append(f"good sample support (n={ss.in_scope_count})")
    elif ss and ss.in_scope_count < 5:
        reason_parts.append(f"low sample support (n={ss.in_scope_count})")
    if physical_interpretability >= 0.7:
        reason_parts.append("physically interpretable")
    if counterexample_penalty > 0:
        reason_parts.append(f"counterexample penalty ({counterexample_penalty:.2f})")

    return PatternScientificScore(
        validation_support=round(validation_support, 4),
        robustness=round(robustness, 4),
        effect_size=round(effect_size, 4),
        sample_support=round(sample_support, 4),
        physical_interpretability=round(physical_interpretability, 4),
        actionability=round(actionability, 4),
        counterexample_penalty=round(counterexample_penalty, 4),
        total=round(total, 4),
        rank_reason="; ".join(reason_parts) if reason_parts else "default scoring",
    )


# ============================================================================
# Downgrade Rules
# ============================================================================


def _apply_downgrades(
    pattern: MaterialPatternCandidate,
    profile_map: Dict[str, FeatureEvidenceProfile],
    evidence_units: List[EvidenceUnit],
) -> None:
    """Apply downgrade rules to a pattern's scientific_score.total.

    Modifies pattern.scientific_score.total in place.
    """
    if not pattern.scientific_score:
        return

    score = pattern.scientific_score.total
    reasons = [pattern.scientific_score.rank_reason]

    # Downgrade: failed validation — non-boundary patterns don't get high scores
    if pattern.validation_status == "fail" and pattern.pattern_type != "boundary":
        score = min(score, 0.25)
        reasons.append("downgraded: validation failed")

    # Downgrade: in_scope_count < 5
    ss = pattern.sample_support
    if ss and ss.in_scope_count < 5:
        score = min(score, 0.30)
        reasons.append(f"downgraded: only {ss.in_scope_count} in-scope samples")

    # Downgrade: no PDP/SHAP dependence evidence
    condition_sources = {c.source for c in pattern.conditions}
    has_pdp_shap = bool({"pdp", "shap_dependence", "interaction"} & condition_sources)
    if not has_pdp_shap and pattern.pattern_type != "boundary":
        score = min(score, 0.35)
        reasons.append("downgraded: no PDP/SHAP evidence for conditions")

    # Downgrade: opaque descriptor without lineage semantics
    if pattern.material_concepts and all(
        "opaque" in mc.lower() for mc in pattern.material_concepts
    ):
        score = max(score - 0.15, 0.0)
        reasons.append("downgraded: opaque descriptor")

    # Downgrade: counterexample feature overlap with condition features
    condition_feats = {c.feature_name for c in pattern.conditions}
    for ce in pattern.counterexamples:
        ce_feats = set(ce.feature_signature.keys()) if ce.feature_signature else set()
        if condition_feats & ce_feats:
            score = max(score - 0.1, 0.0)
            reasons.append("downgraded: counterexample shares condition features")
            break

    # Ensure score is in [0, 1]
    score = max(min(score, 1.0), 0.0)

    pattern.scientific_score.total = round(score, 4)
    pattern.scientific_score.rank_reason = "; ".join(reasons)


# ============================================================================
# Deduplication
# ============================================================================


def _deduplicate_patterns(
    patterns: List[MaterialPatternCandidate],
) -> List[MaterialPatternCandidate]:
    """Deduplicate near-identical patterns.

    Two patterns are considered duplicates if they share:
      - pattern_type
      - condition feature set (same feature names)
      - overlapping value ranges

    The one with the higher scientific_score.total is kept.
    """
    if len(patterns) <= 1:
        return patterns

    kept: List[MaterialPatternCandidate] = []
    removed_ids: set = set()

    for i, p1 in enumerate(patterns):
        if p1.pattern_id in removed_ids:
            continue
        best = p1
        for j, p2 in enumerate(patterns):
            if j <= i or p2.pattern_id in removed_ids:
                continue
            if _are_duplicates(p1, p2):
                removed_ids.add(p2.pattern_id)
                s1 = best.scientific_score.total if best.scientific_score else 0.0
                s2 = p2.scientific_score.total if p2.scientific_score else 0.0
                if s2 > s1:
                    best = p2
        kept.append(best)

    if len(removed_ids) > 0:
        logger.info("Deduplication removed %d patterns", len(removed_ids))

    return kept


def _are_duplicates(
    p1: MaterialPatternCandidate,
    p2: MaterialPatternCandidate,
) -> bool:
    """Check if two patterns are near-duplicates."""
    if p1.pattern_type != p2.pattern_type:
        return False

    feats1 = {c.feature_name for c in p1.conditions}
    feats2 = {c.feature_name for c in p2.conditions}

    # Different feature sets → not duplicates
    if feats1 != feats2:
        return False

    # If no features, compare statements
    if not feats1:
        return p1.statement[:120].lower() == p2.statement[:120].lower()

    # Check overlapping value ranges for each shared feature
    for feat in feats1:
        vr1 = _extract_value_range(p1, feat)
        vr2 = _extract_value_range(p2, feat)
        if vr1 is None or vr2 is None:
            continue
        # Overlap check
        if vr1[1] < vr2[0] or vr2[1] < vr1[0]:
            return False  # No overlap → not duplicates

    return True


def _extract_value_range(
    pattern: MaterialPatternCandidate,
    feature_name: str,
) -> Optional[tuple]:
    """Extract (min, max) value range for a feature from a pattern's conditions."""
    for c in pattern.conditions:
        if c.feature_name != feature_name:
            continue
        vr = c.value_range
        vmin = vr.get("min") if vr else None
        vmax = vr.get("max") if vr else None
        qr = c.quantile_range
        if vmin is not None and vmax is not None:
            return (float(vmin), float(vmax))
        if qr and len(qr) >= 2:
            return (float(qr[0]), float(qr[1]))
    return None
