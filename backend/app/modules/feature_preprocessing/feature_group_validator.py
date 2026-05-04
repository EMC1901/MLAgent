from typing import List
from app.modules.feature_preprocessing.enums import FeatureGroupStatus


def validate_feature_groups(
    feature_groups: List[dict],
    retained_feature_columns: List[str],
) -> List[dict]:
    """Validate each feature group after filtering.

    Groups whose features are all dropped get status 'dropped'.
    Groups with some retained features get 'retained' or 'retained_with_warning'.
    """
    retained_set = set(retained_feature_columns)
    groups = []

    for group in feature_groups:
        group_name = group.get("group_name", "unknown")
        gcols = group.get("feature_columns", [])
        n_raw = len(gcols)
        valid_in_group = [c for c in gcols if c in retained_set]
        n_valid = len(valid_in_group)

        if n_raw == 0:
            status = FeatureGroupStatus.RETAINED
            reason = ""
        elif n_valid == 0:
            status = FeatureGroupStatus.DROPPED
            reason = "all_features_invalid_or_constant"
        elif n_valid < n_raw:
            status = FeatureGroupStatus.RETAINED_WITH_WARNING
            reason = f"{n_raw - n_valid} features dropped"
        else:
            status = FeatureGroupStatus.RETAINED
            reason = ""

        groups.append({
            "group_name": group_name,
            "n_raw_features": n_raw,
            "n_valid_features": n_valid,
            "status": status,
            "reason": reason,
        })

    return groups
