from app.modules.model_search_context.schemas import PreprocessingSummary


def analyze_preprocessing(context: dict) -> dict:
    fmp_ctx = context.get("feature_preprocessing_context", {})
    fmp_json = fmp_ctx.get("preprocessing_json", {})

    preprocessing_execution = fmp_json.get("preprocessing_execution", {}) or {}

    imputation_info = preprocessing_execution.get("imputation", {}) or {}
    scaling_info = preprocessing_execution.get("scaling", {}) or {}
    feature_selection_info = preprocessing_execution.get("feature_selection", {}) or {}
    encoding_info = preprocessing_execution.get("categorical_encoding", {}) or {}

    imputation_executed = imputation_info.get("executed", False) or imputation_info.get("strategy", "none") != "none"
    scaling_executed = scaling_info.get("executed", False) or scaling_info.get("strategy", "none") != "none"
    feature_selection_executed = (
        feature_selection_info.get("executed", False)
        or feature_selection_info.get("strategy", "none") != "none"
    )
    categorical_encoding_executed = (
        encoding_info.get("executed", False)
        or encoding_info.get("strategy", "none") != "none"
    )

    summary = PreprocessingSummary(
        imputation_executed=imputation_executed,
        scaling_executed=scaling_executed,
        feature_selection_executed=feature_selection_executed,
        categorical_encoding_executed=categorical_encoding_executed,
        preprocessing_pipeline_artifact_id=fmp_ctx.get("preprocessor_artifact_id"),
    )

    return {
        "summary": summary,
        "any_preprocessing_executed": any([
            imputation_executed, scaling_executed, feature_selection_executed,
        ]),
    }
