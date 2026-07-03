"""Phase 4: Material Scope Analyzer.

Analyzes which material families, composition families, or formula families
a given pattern applies to.  Uses feature lineage and material metadata to
identify stable vs. weak vs. excluded material families for each pattern.

When no material-family information is available, explicitly records that
scope is limited to the global data distribution — which is important for
scientific reporting because material rules are rarely universal.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional

from app.modules.interpretability_analysis.schemas import (
    MaterialPatternCandidate,
    MaterialMechanismCandidate,
)

logger = logging.getLogger(__name__)


def analyze_material_scope(
    patterns: List[MaterialPatternCandidate],
    X,
    material_metadata: Optional[Dict[str, Any]],
    feature_lineage: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Analyze material family scope for each pattern.

    Args:
        patterns: Validated MaterialPatternCandidates.
        X: Feature matrix (DataFrame).
        material_metadata: Optional material metadata (formulas, families, etc.).
        feature_lineage: Optional feature lineage dictionary.

    Returns:
        List of scope analysis dicts, one per pattern.
    """
    if patterns is None:
        return []

    results: List[Dict[str, Any]] = []

    # Try to identify material-family columns from X or lineage
    family_cols = _detect_material_family_columns(X, material_metadata, feature_lineage)

    for pattern in patterns:
        scope = _analyze_pattern_scope(pattern, X, family_cols)
        results.append(scope)

    return results


def apply_scope_to_mechanisms(
    mechanisms: List[MaterialMechanismCandidate],
    scope_results: List[Dict[str, Any]],
) -> List[MaterialMechanismCandidate]:
    """Apply material scope analysis results to mechanism candidates.

    Updates each mechanism's applicable_material_scope and excluded_or_weak_scope
    based on the scope analysis of its source patterns.
    """
    if not mechanisms or not scope_results:
        return mechanisms

    scope_by_pattern: Dict[str, Dict[str, Any]] = {
        sr.get("pattern_id", ""): sr for sr in scope_results
    }

    for mech in mechanisms:
        stable: List[str] = []
        weak: List[str] = []
        excluded: List[str] = []

        for pid in mech.source_pattern_ids:
            sr = scope_by_pattern.get(pid, {})
            stable.extend(sr.get("stable_families", []))
            weak.extend(sr.get("weak_families", []))
            excluded.extend(sr.get("excluded_families", []))

        mech.applicable_material_scope = list(dict.fromkeys(stable))
        mech.excluded_or_weak_scope = list(dict.fromkeys(weak + excluded))

    return mechanisms


# ============================================================================
# Family column detection
# ============================================================================


def _detect_material_family_columns(
    X,
    material_metadata: Optional[Dict[str, Any]],
    feature_lineage: Optional[Dict[str, Any]],
) -> Dict[str, str]:
    """Detect columns in X that encode material family membership.

    Returns dict: column_name -> family_type
      family_type is one of: "formula_family", "composition_family", "crystal_family", "material_family"
    """
    family_cols: Dict[str, str] = {}

    if X is None:
        return family_cols

    # Check material_metadata
    meta = material_metadata or {}
    for key in ["formula_column", "composition_column", "family_column", "material_class_column"]:
        val = meta.get(key, "")
        if val and val in X.columns:
            family_cols[val] = key.replace("_column", "").replace("material_class", "material_family")

    # Check feature_lineage for category-based family hints
    if feature_lineage:
        for col in X.columns:
            if col in family_cols:
                continue
            lineage = feature_lineage.get(col, {})
            if isinstance(lineage, dict):
                cat = lineage.get("category", "")
                if cat in ("formula_family", "composition_family", "crystal_family"):
                    family_cols[col] = cat

    # Heuristic: look for columns whose name suggests family
    family_keywords = ["family", "group", "class", "system", "crystal", "space_group", "prototype"]
    for col in X.columns:
        if col in family_cols:
            continue
        col_lower = col.lower()
        if any(kw in col_lower for kw in family_keywords):
            # Only include if it has few unique values (categorical)
            try:
                n_unique = X[col].nunique()
                if n_unique <= 50 and n_unique >= 2:
                    family_cols[col] = "material_family"
            except Exception:
                pass

    return family_cols


# ============================================================================
# Per-pattern scope analysis
# ============================================================================


def _analyze_pattern_scope(
    pattern: MaterialPatternCandidate,
    X,
    family_cols: Dict[str, str],
) -> Dict[str, Any]:
    """Analyze scope for a single pattern.

    Returns a dict with pattern_id, stable_families, weak_families,
    excluded_families, and family_support_counts.
    """
    scope: Dict[str, Any] = {
        "pattern_id": pattern.pattern_id,
        "stable_families": [],
        "weak_families": [],
        "excluded_families": [],
        "family_support_counts": {},
        "scope_note": "",
    }

    if not family_cols or X is None:
        scope["scope_note"] = (
            "No material-family metadata available; "
            "scope limited to global data distribution."
        )
        return scope

    condition_features = [c.feature_name for c in pattern.conditions if c.feature_name and c.feature_name in X.columns]

    # Pre-compute global column references for _feature_in_range quantile lookups
    global_X = X

    for fam_col, fam_type in family_cols.items():
        try:
            families = X[fam_col].dropna().unique()
        except Exception:
            continue

        for family in families:
            try:
                mask = X[fam_col] == family
                family_X = X.loc[mask]
                if len(family_X) < 5:
                    scope["excluded_families"].append(f"{family} (n={len(family_X)}, too few samples)")
                    continue

                # For each condition feature, check if the family's distribution
                # overlaps with the pattern's value range
                overlaps = 0
                total = 0
                for feat in condition_features:
                    if feat not in family_X.columns:
                        continue
                    total += 1
                    cond = _find_condition(pattern, feat)
                    if cond and _feature_in_range(family_X[feat], cond, global_X[feat]):
                        overlaps += 1

                support_count = len(family_X)
                if total > 0 and overlaps / total >= 0.5:
                    scope["stable_families"].append(family)
                    scope["family_support_counts"][str(family)] = support_count
                elif total > 0:
                    scope["weak_families"].append(family)
                    scope["family_support_counts"][str(family)] = support_count
                else:
                    scope["weak_families"].append(family)
                    scope["family_support_counts"][str(family)] = support_count

            except Exception as e:
                logger.debug("Error analyzing family '%s': %s", family, str(e))
                continue

    if not scope["stable_families"] and not scope["weak_families"]:
        scope["scope_note"] = (
            f"Material-family columns detected ({', '.join(family_cols.keys())}) "
            f"but no families showed sufficient feature-range overlap."
        )
    elif not scope["stable_families"]:
        scope["scope_note"] = (
            f"No material families showed strong alignment with this pattern's value ranges. "
            f"Pattern may be noisy or not family-specific."
        )

    return scope


def _find_condition(pattern: MaterialPatternCandidate, feature_name: str):
    """Find the PatternCondition for a given feature."""
    for c in pattern.conditions:
        if c.feature_name == feature_name:
            return c
    return None


def _feature_in_range(family_values, condition, global_values=None) -> bool:
    """Check if the family's feature values overlap with the pattern's condition range.

    For quantile_range conditions, computes actual value thresholds from the global
    distribution so that high-quantile patterns exclude low-value families and
    vice versa.
    """
    if family_values is None or len(family_values) == 0:
        return False

    try:
        fmin = float(family_values.min())
        fmax = float(family_values.max())
    except (ValueError, TypeError):
        return False

    vr = condition.value_range or {}
    qr = condition.quantile_range

    # Check explicit value_range bounds (min/max)
    if "min" in vr and "max" in vr:
        vmin = float(vr["min"])
        vmax = float(vr["max"])
        return fmax >= vmin and fmin <= vmax

    if "threshold" in vr:
        thresh = float(vr["threshold"])
        return fmin <= thresh <= fmax

    # Check quantile_range: convert to actual value thresholds from global distribution.
    # This distinguishes e.g. a high-quantile pattern (only high-value families) from
    # a low-quantile pattern (only low-value families).
    if qr and len(qr) >= 2 and global_values is not None:
        try:
            gv = global_values.dropna()
            if len(gv) == 0:
                return True
            q_lo = float(qr[0])
            q_hi = float(qr[1])
            v_lo = float(gv.quantile(max(0.0, q_lo)))
            v_hi = float(gv.quantile(min(1.0, q_hi)))
            # Family range must overlap with the quantile-derived value range
            return fmax >= v_lo and fmin <= v_hi
        except Exception:
            pass

    return True  # If no range constraints, assume family is in scope
