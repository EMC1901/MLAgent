from app.modules.model_search_context.schemas import FeatureGroupSummary


def analyze_feature_groups(context: dict) -> dict:
    fe_ctx = context.get("feature_engineering_context", {})
    fmp_ctx = context.get("feature_preprocessing_context", {})
    fmp_json = fmp_ctx.get("preprocessing_json", {})

    feature_json = fe_ctx.get("feature_json", {})
    feature_schema = feature_json.get("feature_schema", {}) or {}
    raw_feature_groups = (
        feature_schema.get("feature_groups", [])
        or feature_json.get("feature_groups", [])
    )

    group_validation = fmp_json.get("feature_group_validation", {}) or {}
    groups = group_validation.get("groups", [])

    retained_groups = []
    dropped_groups = []
    partially_retained_groups = []

    if groups:
        for g in groups:
            group_name = g.get("group_name", "")
            status = g.get("status", "")
            if status == "retained":
                retained_groups.append(group_name)
            elif status == "retained_with_warning":
                partially_retained_groups.append(group_name)
            elif status == "dropped":
                dropped_groups.append(group_name)
    else:
        for rg in raw_feature_groups:
            group_name = rg.get("group_name", rg.get("name", str(rg)))
            retained_groups.append(group_name)

    n_final = fmp_ctx.get("n_final_features") or 0
    low_effective_feature_warning = n_final < 20

    summary = FeatureGroupSummary(
        retained_groups=retained_groups,
        dropped_groups=dropped_groups,
        partially_retained_groups=partially_retained_groups,
        low_effective_feature_warning=low_effective_feature_warning,
    )

    return {
        "summary": summary,
        "has_dropped_groups": len(dropped_groups) > 0,
        "has_partial_groups": len(partially_retained_groups) > 0,
        "dropped_group_count": len(dropped_groups),
    }
