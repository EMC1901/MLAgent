import logging
from app.modules.interpretability_analysis.schemas import (
    LLMInterpretabilitySummary,
    MaterialPattern,
    FeatureGroupInterpretation,
)
from app.modules.interpretability_analysis.enums import LLMInterpretabilityConfidence

logger = logging.getLogger(__name__)

CONFIDENCE_ALIASES = {
    "low": LLMInterpretabilityConfidence.LOW,
    "medium": LLMInterpretabilityConfidence.MEDIUM,
    "high": LLMInterpretabilityConfidence.HIGH,
    "l": LLMInterpretabilityConfidence.LOW,
    "m": LLMInterpretabilityConfidence.MEDIUM,
    "h": LLMInterpretabilityConfidence.HIGH,
}

EVIDENCE_STRENGTH_ALIASES = {
    "weak": "weak",
    "moderate": "moderate",
    "strong": "strong",
    "low": "weak",
    "medium": "moderate",
    "high": "strong",
    "w": "weak",
    "m": "moderate",
    "s": "strong",
}


def normalize_llm_interpretability_summary(
    summary: LLMInterpretabilitySummary,
) -> LLMInterpretabilitySummary:
    confidence = CONFIDENCE_ALIASES.get(
        (summary.confidence_level or "").lower().strip(),
        LLMInterpretabilityConfidence.MEDIUM,
    )
    summary.confidence_level = confidence

    normalized_patterns = []
    for mp in summary.top_material_patterns:
        if isinstance(mp, dict):
            mp = MaterialPattern(**mp)
        mp.evidence_strength = EVIDENCE_STRENGTH_ALIASES.get(
            (mp.evidence_strength or "").lower().strip(), "moderate"
        )
        if not mp.caution:
            mp.caution = "This is a model-based association, not a causal mechanism."
        normalized_patterns.append(mp)
    summary.top_material_patterns = normalized_patterns

    normalized_groups = []
    for fg in summary.feature_groups_interpretation:
        if isinstance(fg, dict):
            fg = FeatureGroupInterpretation(**fg)
        normalized_groups.append(fg)
    summary.feature_groups_interpretation = normalized_groups

    if not summary.limitations:
        summary.limitations = [
            "Interpretation is limited by the available descriptors and dataset size.",
            "SHAP values describe model behavior, not necessarily physical causality.",
        ]

    logger.info("Normalized LLM interpretability summary: confidence=%s", confidence)
    return summary
