from app.modules.model_search_context.schemas import PreprocessingSummary


def analyze_preprocessing(context: dict) -> dict:
    fmp_ctx = context.get("feature_preprocessing_context", {})
    fmp_json = fmp_ctx.get("preprocessing_json", {})

    preprocessing_execution = fmp_json.get("preprocessing_execution", {}) or {}

    imputation_info = preprocessing_execution.get("imputation", {}) or {}
    scaling_info = preprocessing_execution.get("scaling", {}) or {}
    feature_selection_info = preprocessing_execution.get("feature_selection", {}) or {}
    encoding_info = preprocessing_execution.get("categorical_encoding", {}) or {}
    fold_safe_deferred = preprocessing_execution.get("fold_safe_deferred") or {}

    imputation_executed = (
        imputation_info.get("executed", False)
        or imputation_info.get("strategy", "none") != "none"
    )
    scaling_executed = (
        scaling_info.get("executed", False)
        or scaling_info.get("strategy", "none") != "none"
    )
    feature_selection_executed = (
        feature_selection_info.get("executed", False)
        or feature_selection_info.get("strategy", "none") != "none"
    )
    categorical_encoding_executed = (
        encoding_info.get("executed", False)
        or encoding_info.get("strategy", "none") != "none"
    )

    # Read execution_mode (new field: "global" | "fold_safe" | "none")
    imputation_mode = imputation_info.get("execution_mode", "global" if imputation_executed else "none")
    scaling_mode = scaling_info.get("execution_mode", "global" if scaling_executed else "none")
    feature_selection_mode = feature_selection_info.get("execution_mode", "global" if feature_selection_executed else "none")

    summary = PreprocessingSummary(
        imputation_executed=imputation_executed,
        scaling_executed=scaling_executed,
        feature_selection_executed=feature_selection_executed,
        categorical_encoding_executed=categorical_encoding_executed,
        preprocessing_pipeline_artifact_id=fmp_ctx.get("preprocessor_artifact_id"),
        imputation_execution_mode=imputation_mode,
        scaling_execution_mode=scaling_mode,
        feature_selection_execution_mode=feature_selection_mode,
        fold_safe_deferred=fold_safe_deferred if fold_safe_deferred else None,
    )

    return {
        "summary": summary,
        "any_preprocessing_executed": any([
            imputation_executed, scaling_executed, feature_selection_executed,
        ]),
        "has_fold_safe_deferred": bool(fold_safe_deferred and fold_safe_deferred.get("has_deferred")),
        "n_deferred_operations": (
            fold_safe_deferred.get("n_deferred_operations", 0)
            if fold_safe_deferred else 0
        ),
    }
