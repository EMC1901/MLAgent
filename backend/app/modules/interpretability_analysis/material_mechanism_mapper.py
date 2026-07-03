"""Phase 4: Material Mechanism Mapper.

Maps validated MaterialPatternCandidates to MaterialMechanismCandidates by
grounding descriptor-level patterns in material science concepts, causal
chains, applicable material families, and experimental validation paths.

Core entry point: map_patterns_to_mechanisms()

Mapping rules (from Phase4.md):
  1. monotonic pattern -> association mechanism
  2. threshold pattern -> transition / regime mechanism
  3. window pattern -> trade-off / optimum mechanism
  4. interaction pattern -> coupled mechanism (only if validated or has 2D PDP)
  5. boundary pattern -> NOT a mechanism; stays as applicability/limitation
"""

import uuid
import logging
from typing import List, Dict, Any, Optional

from app.modules.interpretability_analysis.schemas import (
    MaterialPatternCandidate,
    MaterialMechanismCandidate,
    FeatureEvidenceProfile,
    EvidenceUnit,
)

logger = logging.getLogger(__name__)


def map_patterns_to_mechanisms(
    patterns: List[MaterialPatternCandidate],
    feature_lineage: Optional[Dict[str, Any]],
    feature_profiles: List[FeatureEvidenceProfile],
    evidence_units: List[EvidenceUnit],
    material_domain: Optional[str] = None,
) -> List[MaterialMechanismCandidate]:
    """Map validated material patterns to material-domain mechanism candidates.

    Args:
        patterns: Validated and ranked MaterialPatternCandidates.
        feature_lineage: Feature lineage dictionary (feature_name -> info).
        feature_profiles: Per-feature evidence profiles.
        evidence_units: All evidence units.
        material_domain: Optional material domain hint.

    Returns:
        List of MaterialMechanismCandidate (empty if no patterns qualify).
    """
    if not patterns:
        logger.info("No patterns to map to mechanisms.")
        return []

    # Lazy-load registries
    semantics_registry = _get_semantics_registry()

    mechanisms: List[MaterialMechanismCandidate] = []

    for pattern in patterns:
        # Rule 5: boundary patterns are NOT mechanisms
        if pattern.pattern_type == "boundary":
            continue

        # General guard: failed non-boundary patterns do not produce mechanisms
        if pattern.validation_status == "fail":
            logger.debug("Skipping failed pattern '%s' (type=%s)", pattern.pattern_id, pattern.pattern_type)
            continue

        # Rule 4: interaction patterns only qualify with validation pass OR 2D PDP.
        # Weak interaction without 2D PDP stays a weak hypothesis, not a mechanism.
        if pattern.pattern_type == "interaction":
            has_pdp_2d = _pattern_has_2d_pdp(pattern, evidence_units)
            if not has_pdp_2d and pattern.validation_status != "pass":
                logger.debug("Interaction pattern '%s' lacks 2D PDP and is not validated-pass; "
                           "treating as weak hypothesis, not mechanism", pattern.pattern_id)
                continue

        # Collect features from conditions
        condition_features = list(dict.fromkeys(
            c.feature_name for c in pattern.conditions if c.feature_name
        ))

        # Determine grounding level for each feature
        material_concepts: List[str] = []
        descriptor_vars: List[str] = []
        mechanism_family = _infer_mechanism_family(pattern, condition_features, feature_lineage, semantics_registry)
        grounding_level = "descriptor_grounded"
        grounding_levels: List[str] = []

        for feat in condition_features:
            concept, feat_grounding = _ground_feature(
                feat, feature_lineage, semantics_registry
            )
            if concept:
                material_concepts.append(concept)
            descriptor_vars.append(feat)
            grounding_levels.append(feat_grounding)

        # Pick the best (highest) grounding level across features
        grounding_level = _best_grounding_level(grounding_levels)

        # Build causal chain
        causal_chain = _build_causal_chain(pattern, condition_features, material_concepts, mechanism_family)

        # Build mechanism statement
        mechanism_statement = _build_mechanism_statement(
            pattern, condition_features, material_concepts, mechanism_family, grounding_level
        )

        # Collect supporting evidence and validation
        supporting_validation = [
            {
                "validation_type": vr.validation_type,
                "status": vr.status,
                "interpretation": vr.interpretation,
            }
            for vr in pattern.validation_results
        ]

        # Counterexamples from pattern
        counterexamples = [ce.model_dump() for ce in pattern.counterexamples]

        # Validation suggestions
        validation_suggestions = list(pattern.validation_suggestions)
        _add_mechanism_specific_suggestions(validation_suggestions, pattern, mechanism_family, grounding_level)

        # Limitations
        limitations = list(pattern.limitations)
        if grounding_level == "descriptor_grounded":
            limitations.append(
                "Mechanism is grounded only at the descriptor-name level; "
                "no material-specific interpretation is available from lineage or semantics registry."
            )

        mechanism = MaterialMechanismCandidate(
            mechanism_id=f"mm_{uuid.uuid4().hex[:8]}",
            source_pattern_ids=[pattern.pattern_id],
            mechanism_family=mechanism_family,
            mechanism_statement=mechanism_statement,
            material_variables=material_concepts,
            descriptor_variables=descriptor_vars,
            causal_chain=causal_chain,
            applicable_material_scope=[],
            excluded_or_weak_scope=[],
            supporting_evidence_ids=list(pattern.supporting_evidence_ids),
            supporting_pattern_validation=supporting_validation,
            counterexamples=counterexamples,
            confidence_score=pattern.confidence_score,
            confidence_label=pattern.confidence_label,
            grounding_level=grounding_level,
            limitations=limitations,
            validation_suggestions=validation_suggestions,
        )
        mechanisms.append(mechanism)

    # Merge mechanisms that share the same mechanism_family and overlap in features
    mechanisms = _merge_related_mechanisms(mechanisms)

    logger.info("Mapped %d patterns to %d mechanism candidates", len(patterns), len(mechanisms))
    return mechanisms


# ============================================================================
# Grounding helpers
# ============================================================================


def _get_semantics_registry():
    try:
        from app.modules.interpretability_analysis.material_semantics_registry import get_semantics_registry
        return get_semantics_registry()
    except Exception:
        return None


def _ground_feature(
    feature_name: str,
    feature_lineage: Optional[Dict[str, Any]],
    semantics_registry,
) -> tuple:
    """Determine the material concept and grounding level for a feature.

    Returns (concept_str, grounding_level).

    Priority:
      1. feature_lineage description -> "lineage_grounded"
      2. feature_lineage category -> "lineage_grounded"
      3. material_semantics_registry -> "physics_prior_grounded"
      4. physics_rule_registry feature_semantics -> "physics_prior_grounded"
      5. keyword fallback -> "descriptor_grounded"
      6. opaque -> "descriptor_grounded" with "opaque descriptor" concept
    """
    lineage = (feature_lineage or {}).get(feature_name, {})

    # 1. lineage description
    if isinstance(lineage, dict):
        desc = lineage.get("description", "")
        if desc:
            return str(desc), "lineage_grounded"
        category = lineage.get("category", "")
        if category and category != "other":
            return str(category).replace("_", " "), "lineage_grounded"

    # 2. material semantics registry
    if semantics_registry is not None:
        try:
            sem = semantics_registry.lookup(feature_name)
            if sem:
                concept = sem.get("material_concept", "")
                if concept:
                    return str(concept), "physics_prior_grounded"
        except Exception:
            pass

    # 3. physics rule registry fallback
    try:
        from app.modules.interpretability_analysis.physics_rule_registry import get_registry
        phys = get_registry().get_feature_semantics(feature_name)
        if phys:
            category = phys.get("category", "")
            if category:
                return str(category), "physics_prior_grounded"
    except Exception:
        pass

    # 4. Keyword fallback
    concept = _keyword_fallback(feature_name)
    if concept and "opaque" not in concept.lower():
        return concept, "descriptor_grounded"

    return "opaque descriptor", "descriptor_grounded"


def _keyword_fallback(feature_name: str) -> str:
    """Lightweight keyword-based concept fallback."""
    kw_map = {
        "electronegativity": "electronegativity / bonding polarity",
        "atomic_radius": "size mismatch / atomic packing",
        "ionic_radius": "size mismatch / ionic packing",
        "radius": "size / radial descriptor",
        "volume": "structural compactness",
        "density": "structural compactness / mass density",
        "lattice": "structural / lattice descriptor",
        "valence": "electronic structure descriptor",
        "electron": "electronic structure descriptor",
        "band_gap": "electronic band structure",
        "formation_energy": "thermodynamic stability",
        "cohesive_energy": "bonding energy",
        "bulk_modulus": "mechanical stiffness",
        "melting": "thermal stability",
        "conductivity": "transport property",
        "fraction": "fractional composition",
        "temperature": "thermal condition",
        "grain": "microstructural descriptor",
        "phase": "phase descriptor",
    }
    feat_lower = feature_name.lower()
    for kw, concept in kw_map.items():
        if kw in feat_lower:
            return concept
    return "opaque descriptor"


def _best_grounding_level(levels: List[str]) -> str:
    """Pick the best (most grounded) level from a list."""
    order = {
        "externally_validated": 4,
        "physics_prior_grounded": 3,
        "lineage_grounded": 2,
        "descriptor_grounded": 1,
    }
    if not levels:
        return "descriptor_grounded"
    return max(levels, key=lambda l: order.get(l, 0))


# ============================================================================
# Mechanism family inference
# ============================================================================


def _infer_mechanism_family(
    pattern: MaterialPatternCandidate,
    condition_features: List[str],
    feature_lineage: Optional[Dict[str, Any]],
    semantics_registry,
) -> str:
    """Infer the mechanism family from pattern type + feature semantics.

    Priority: lineage.category > material_semantics_registry > pattern_type fallback.
    """
    # 1. Try lineage first (higher priority per Phase4.md chain)
    if feature_lineage:
        for feat in condition_features:
            lineage = feature_lineage.get(feat, {})
            if isinstance(lineage, dict):
                cat = lineage.get("category", "")
                mapped = _category_to_family(cat)
                if mapped:
                    return mapped

    # 2. Try semantics registry
    if semantics_registry is not None:
        families = []
        for feat in condition_features:
            try:
                sem = semantics_registry.lookup(feat)
                if sem and sem.get("mechanism_family"):
                    families.append(sem["mechanism_family"])
            except Exception:
                pass
        if families:
            # Most common family
            from collections import Counter
            return Counter(families).most_common(1)[0][0]

    # 3. Pattern-type based fallback
    return _pattern_type_to_family(pattern.pattern_type)


def _category_to_family(category: str) -> str:
    mapping = {
        "composition": "composition_complexity",
        "composition_descriptor": "composition_complexity",
        "elemental": "electronic_structure",
        "elemental_descriptor": "electronic_structure",
        "structure": "lattice_distortion",
        "structure_descriptor": "lattice_distortion",
        "electronic": "electronic_structure",
        "thermodynamic": "thermodynamic_stability",
        "processing": "processing_structure",
    }
    return mapping.get(category.lower(), "")


def _pattern_type_to_family(pattern_type: str) -> str:
    mapping = {
        "monotonic": "composition_complexity",
        "threshold": "electronic_structure",
        "window": "thermodynamic_stability",
        "interaction": "bonding_strength",
        "subgroup": "composition_complexity",
    }
    return mapping.get(pattern_type, "composition_complexity")


# ============================================================================
# Causal chain and statement builders
# ============================================================================


def _build_causal_chain(
    pattern: MaterialPatternCandidate,
    condition_features: List[str],
    material_concepts: List[str],
    mechanism_family: str,
) -> List[str]:
    """Build a causal chain linking descriptors to predicted target."""
    chain: List[str] = []

    if not condition_features:
        return chain

    descriptors_str = ", ".join(condition_features[:3])
    concepts_str = ", ".join(material_concepts[:3]) if material_concepts else descriptors_str

    chain.append(f"Descriptor(s) '{descriptors_str}' encode {concepts_str}")

    if pattern.pattern_type == "monotonic":
        chain.append(
            f"Monotonic association suggests a direct, gradual influence "
            f"of {concepts_str} on the predicted target"
        )
    elif pattern.pattern_type == "threshold":
        chain.append(
            f"Threshold behavior indicates a regime change where the influence "
            f"of {concepts_str} transitions at a critical value"
        )
    elif pattern.pattern_type == "window":
        chain.append(
            f"Window/peak pattern suggests an optimum in {concepts_str}, "
            f"consistent with a trade-off between competing effects"
        )
    elif pattern.pattern_type == "interaction":
        chain.append(
            f"Interaction between {concepts_str} suggests coupled effects "
            f"where one descriptor's influence depends on the other's value"
        )

    chain.append(
        f"Mechanism family '{mechanism_family}' provides a domain framework "
        f"for interpreting this pattern"
    )

    return chain


def _build_mechanism_statement(
    pattern: MaterialPatternCandidate,
    condition_features: List[str],
    material_concepts: List[str],
    mechanism_family: str,
    grounding_level: str,
) -> str:
    """Build a scientific mechanism statement from the pattern."""
    concepts_str = ", ".join(material_concepts) if material_concepts else ", ".join(condition_features)

    grounding_note = ""
    if grounding_level == "descriptor_grounded":
        grounding_note = (
            " This interpretation is descriptor-grounded only; "
            "material-specific meaning is inferred from feature names rather than "
            "explicit physical priors."
        )
    elif grounding_level == "lineage_grounded":
        grounding_note = (
            " This interpretation is grounded in feature lineage metadata."
        )
    elif grounding_level == "physics_prior_grounded":
        grounding_note = (
            " This interpretation is grounded in materials science physical priors."
        )

    family_labels = {
        "electronic_structure": "electronic structure effects",
        "lattice_distortion": "lattice distortion / strain effects",
        "bonding_strength": "bonding strength / character effects",
        "composition_complexity": "compositional complexity effects",
        "thermodynamic_stability": "thermodynamic stability effects",
        "processing_structure": "processing-structure relationships",
    }
    family_label = family_labels.get(mechanism_family, mechanism_family)

    if pattern.pattern_type == "monotonic":
        direction = pattern.predicted_effect.target_direction
        return (
            f"For descriptors related to {concepts_str}, "
            f"the validated {pattern.pattern_type} pattern suggests a possible "
            f"{direction} association with the target property, consistent with "
            f"{family_label}.{grounding_note}"
        )
    elif pattern.pattern_type == "threshold":
        return (
            f"For descriptors related to {concepts_str}, "
            f"the validated {pattern.pattern_type} pattern suggests a possible "
            f"regime transition, consistent with {family_label} where a critical "
            f"value separates distinct behavioral regimes.{grounding_note}"
        )
    elif pattern.pattern_type == "window":
        return (
            f"For descriptors related to {concepts_str}, "
            f"the validated {pattern.pattern_type} pattern suggests a possible "
            f"trade-off or optimum, consistent with competing {family_label}. "
            f"This pattern is supported by in-scope samples, passes validation, "
            f"but remains model-supported rather than experimentally causal.{grounding_note}"
        )
    elif pattern.pattern_type == "interaction":
        return (
            f"For descriptors related to {concepts_str}, "
            f"the validated {pattern.pattern_type} pattern suggests coupled "
            f"{family_label} where the influence of one descriptor depends on "
            f"the value of another.{grounding_note}"
        )
    else:
        return (
            f"For descriptors related to {concepts_str}, "
            f"the validated pattern suggests {family_label}.{grounding_note}"
        )


# ============================================================================
# 2D PDP check for interaction patterns
# ============================================================================


def _pattern_has_2d_pdp(
    pattern: MaterialPatternCandidate,
    evidence_units: List[EvidenceUnit],
) -> bool:
    """Check if any evidence unit backing this pattern comes from 2D PDP."""
    pattern_ev_ids = set(pattern.supporting_evidence_ids)
    has_pdp_2d_evidence = False
    for eu in evidence_units:
        if eu.evidence_id in pattern_ev_ids:
            qs = eu.quantitative_summary if isinstance(eu.quantitative_summary, dict) else {}
            if qs.get("source") == "pdp_2d" or "pdp_2d" in str(qs):
                has_pdp_2d_evidence = True
                break

    if has_pdp_2d_evidence:
        return True

    # Also check if any condition has source="interaction" with value_range populated
    # (set by _mine_interaction when 2D PDP was available).  Use "in" to handle
    # peak_value of 0 which is falsy but valid.
    for c in pattern.conditions:
        if c.source == "interaction" and isinstance(c.value_range, dict) and "peak_value" in c.value_range:
            return True

    return False


# ============================================================================
# Merging related mechanisms
# ============================================================================


def _merge_related_mechanisms(
    mechanisms: List[MaterialMechanismCandidate],
) -> List[MaterialMechanismCandidate]:
    """Merge mechanisms that share mechanism_family and overlapping features.

    Two mechanisms are merged if they have the same mechanism_family AND
    share at least one descriptor_variable or source_pattern_ids overlap.
    """
    if len(mechanisms) <= 1:
        return mechanisms

    merged: List[MaterialMechanismCandidate] = []
    used: set = set()

    for i, m1 in enumerate(mechanisms):
        if i in used:
            continue
        best = m1
        used.add(i)

        for j, m2 in enumerate(mechanisms):
            if j in used:
                continue
            if best.mechanism_family != m2.mechanism_family:
                continue

            # Check feature overlap
            feat_overlap = set(best.descriptor_variables) & set(m2.descriptor_variables)
            if not feat_overlap:
                continue

            # Merge m2 into best
            best = MaterialMechanismCandidate(
                mechanism_id=best.mechanism_id,
                source_pattern_ids=list(dict.fromkeys(
                    best.source_pattern_ids + m2.source_pattern_ids
                )),
                mechanism_family=best.mechanism_family,
                mechanism_statement=(
                    best.mechanism_statement + " " + m2.mechanism_statement
                )[:2000],
                material_variables=list(dict.fromkeys(
                    best.material_variables + m2.material_variables
                )),
                descriptor_variables=list(dict.fromkeys(
                    best.descriptor_variables + m2.descriptor_variables
                )),
                causal_chain=list(dict.fromkeys(
                    best.causal_chain + m2.causal_chain
                )),
                applicable_material_scope=list(dict.fromkeys(
                    best.applicable_material_scope + m2.applicable_material_scope
                )),
                excluded_or_weak_scope=list(dict.fromkeys(
                    best.excluded_or_weak_scope + m2.excluded_or_weak_scope
                )),
                supporting_evidence_ids=list(dict.fromkeys(
                    best.supporting_evidence_ids + m2.supporting_evidence_ids
                )),
                supporting_pattern_validation=best.supporting_pattern_validation + m2.supporting_pattern_validation,
                counterexamples=best.counterexamples + m2.counterexamples,
                confidence_score=max(best.confidence_score, m2.confidence_score),
                confidence_label=_max_label(best.confidence_label, m2.confidence_label),
                grounding_level=_best_grounding_level([best.grounding_level, m2.grounding_level]),
                limitations=list(dict.fromkeys(best.limitations + m2.limitations)),
                validation_suggestions=list(dict.fromkeys(
                    best.validation_suggestions + m2.validation_suggestions
                )),
            )
            used.add(j)

        merged.append(best)

    return merged


def _max_label(a: str, b: str) -> str:
    order = {"low": 0, "medium": 1, "high": 2}
    return a if order.get(a, 0) >= order.get(b, 0) else b


def _add_mechanism_specific_suggestions(
    suggestions: List[str],
    pattern: MaterialPatternCandidate,
    mechanism_family: str,
    grounding_level: str,
) -> None:
    """Add mechanism-specific validation suggestions."""
    if grounding_level == "descriptor_grounded":
        suggestions.append(
            "Consult a materials scientist to interpret the descriptor(s) in "
            "domain-specific physical terms before drawing conclusions."
        )
    if pattern.pattern_type == "window":
        suggestions.append(
            "Validate the proposed trade-off mechanism with targeted DFT or "
            "experiments across the identified window."
        )
    if mechanism_family == "electronic_structure":
        suggestions.append(
            "Consider electronic structure calculations (DFT, GW) to verify "
            "whether the identified descriptors capture genuine electronic effects."
        )
