from app.modules.model_search_context.schemas import DatasetEffectiveProfile


def analyze_effective_dataset(context: dict) -> dict:
    task_ctx = context.get("task_context", {})
    fmp_ctx = context.get("feature_preprocessing_context", {})

    n_samples = fmp_ctx.get("n_samples") or 0
    n_raw_features = fmp_ctx.get("n_raw_features") or 0
    n_final_features = fmp_ctx.get("n_final_features") or 0
    n_dropped_features = max(0, n_raw_features - n_final_features)
    feature_reduction_ratio = (n_dropped_features / n_raw_features) if n_raw_features > 0 else 0.0

    profile = DatasetEffectiveProfile(
        n_samples=n_samples,
        n_raw_features=n_raw_features,
        n_final_features=n_final_features,
        n_dropped_features=n_dropped_features,
        feature_reduction_ratio=round(feature_reduction_ratio, 4),
        target_column=fmp_ctx.get("target_column") or task_ctx.get("target_column"),
        task_type=task_ctx.get("task_type"),
    )

    return {
        "profile": profile,
        "n_samples": n_samples,
        "n_raw_features": n_raw_features,
        "n_final_features": n_final_features,
        "n_dropped_features": n_dropped_features,
        "feature_reduction_ratio": feature_reduction_ratio,
        "is_low_feature": n_final_features < 20,
        "is_high_reduction": feature_reduction_ratio > 0.8,
        "is_small_sample": n_samples < 200,
    }
