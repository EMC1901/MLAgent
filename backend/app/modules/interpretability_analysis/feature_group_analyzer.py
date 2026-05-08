import logging
from typing import List, Dict, Any

from app.modules.interpretability_analysis.schemas import (
    FeatureGroupSummary,
    GlobalFeatureImportanceItem,
)
from app.modules.interpretability_analysis.enums import FeatureGroup

logger = logging.getLogger(__name__)

GROUP_PATTERNS = {
    "electronegativity": FeatureGroup.COMPOSITION_DESCRIPTOR,
    "electroneg": FeatureGroup.COMPOSITION_DESCRIPTOR,
    "atomic_radius": FeatureGroup.COMPOSITION_DESCRIPTOR,
    "ionization": FeatureGroup.COMPOSITION_DESCRIPTOR,
    "valence": FeatureGroup.ELEMENTAL_DESCRIPTOR,
    "orbital": FeatureGroup.ELEMENTAL_DESCRIPTOR,
    "magpie": FeatureGroup.COMPOSITION_DESCRIPTOR,
    "stoichiometry": FeatureGroup.COMPOSITION_DESCRIPTOR,
    "composition": FeatureGroup.COMPOSITION_DESCRIPTOR,
    "element": FeatureGroup.ELEMENTAL_DESCRIPTOR,
    "structure": FeatureGroup.STRUCTURE_DESCRIPTOR,
    "lattice": FeatureGroup.STRUCTURE_DESCRIPTOR,
    "space_group": FeatureGroup.STRUCTURE_DESCRIPTOR,
    "statistical": FeatureGroup.STATISTICAL_DESCRIPTOR,
    "derived": FeatureGroup.DERIVED_FEATURE,
    "mean": FeatureGroup.STATISTICAL_DESCRIPTOR,
    "std": FeatureGroup.STATISTICAL_DESCRIPTOR,
    "var": FeatureGroup.STATISTICAL_DESCRIPTOR,
    "min": FeatureGroup.STATISTICAL_DESCRIPTOR,
    "max": FeatureGroup.STATISTICAL_DESCRIPTOR,
    "range": FeatureGroup.STATISTICAL_DESCRIPTOR,
}


def classify_feature_group(feature_name: str) -> str:
    name_lower = feature_name.lower()
    for pattern, group in GROUP_PATTERNS.items():
        if pattern in name_lower:
            return group
    return FeatureGroup.OTHER


def build_feature_group_summary(
    feature_importance: List[GlobalFeatureImportanceItem],
) -> FeatureGroupSummary:
    groups: Dict[str, Dict[str, Any]] = {}

    for fi in feature_importance:
        group_name = fi.feature_group if fi.feature_group and fi.feature_group != "other" else classify_feature_group(fi.feature_name)
        if group_name not in groups:
            groups[group_name] = {
                "feature_count": 0,
                "total_importance": 0.0,
                "top_features": [],
                "mean_importance": 0.0,
            }
        groups[group_name]["feature_count"] += 1
        groups[group_name]["total_importance"] += fi.importance_value
        if len(groups[group_name]["top_features"]) < 5:
            groups[group_name]["top_features"].append(fi.feature_name)

    for g in groups.values():
        if g["feature_count"] > 0:
            g["mean_importance"] = g["total_importance"] / g["feature_count"]

    sorted_groups = sorted(groups.items(), key=lambda x: x[1]["total_importance"], reverse=True)

    group_labels = {
        FeatureGroup.COMPOSITION_DESCRIPTOR: "Composition-based features dominate the model's predictive behavior.",
        FeatureGroup.STRUCTURE_DESCRIPTOR: "Structure-based features contribute to the model's predictions.",
        FeatureGroup.ELEMENTAL_DESCRIPTOR: "Elemental property features play a role in model behavior.",
        FeatureGroup.STATISTICAL_DESCRIPTOR: "Statistical descriptor features provide supplementary contributions.",
        FeatureGroup.DERIVED_FEATURE: "Derived features from feature engineering have notable influence.",
        FeatureGroup.OTHER: "Unclassified features contribute to model predictions.",
    }

    summary_parts = []
    for group_name, group_data in sorted_groups:
        label = group_labels.get(group_name, f"{group_name} features contribute to the model.")
        summary_parts.append(label)

    summary_text = " ".join(summary_parts) if summary_parts else "No feature groups identified."

    logger.info("Built feature group summary for %d groups.", len(groups))
    return FeatureGroupSummary(
        feature_groups=dict(sorted_groups),
        summary_text=summary_text,
    )
