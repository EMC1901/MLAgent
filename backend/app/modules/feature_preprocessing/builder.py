from datetime import datetime
from app.modules.feature_preprocessing.enums import FeaturePreprocessingStatus
from app.modules.feature_preprocessing.schemas import (
    FeaturePreprocessingResponse,
    InputArtifact,
    ValidationSummary,
    ColumnValidation,
    DroppedFeature,
    FeatureGroupValidation,
    FeatureGroupValidationItem,
    PreprocessingExecution,
    PreprocessingStepResult,
    FeatureSelectionStepResult,
    ModelReadyArtifact,
    PreprocessingPipelineArtifact,
    ModelSearchInput,
)


def build_preprocessing_object(
    preprocessing_id: str,
    context: dict,
    status: str,
    filter_result: dict,
    group_validation: list,
    execution_result: dict,
    artifact_result: dict,
    warnings: list,
    errors: list,
) -> FeaturePreprocessingResponse:
    task_context = context.get("task_context") or {}
    plan_context = context.get("plan_context") or {}
    fe_context = context.get("feature_engineering_context") or {}
    fe_json = fe_context.get("feature_json", {})

    target_column = task_context.get("target_column")
    task_type = task_context.get("task_type")
    primary_metric = task_context.get("primary_metric")

    n_raw_features = fe_context.get("n_features", 0)
    n_samples = filter_result.get("n_samples", 0)
    retained_features = filter_result.get("retained_feature_columns", [])
    total_dropped = filter_result.get("total_dropped", [])
    n_dropped = len(total_dropped)
    n_valid_before = n_raw_features - n_dropped if n_raw_features > 0 else 0
    final_features = execution_result.get("feature_columns", retained_features)
    n_final = len(final_features)

    # Input artifact
    input_artifact = InputArtifact(
        feature_matrix_artifact_id=fe_context.get("artifact_id"),
        file_path=fe_context.get("artifact_path"),
        n_samples=n_samples,
        n_raw_features=n_raw_features or 0,
    )

    # Validation summary
    model_ready_artifact_id = artifact_result.get("model_ready_artifact_id")
    model_ready_path = artifact_result.get("model_ready_file_path")
    preprocessor_artifact_id = artifact_result.get("preprocessor_artifact_id")
    preprocessor_path = artifact_result.get("preprocessor_file_path")

    is_model_ready = (
        status in (FeaturePreprocessingStatus.PREPROCESSED, FeaturePreprocessingStatus.PREPROCESSED_WITH_WARNING)
        and len(final_features) > 0
        and n_samples > 0
        and target_column is not None
        and model_ready_artifact_id is not None
    )

    validation_summary = ValidationSummary(
        is_model_ready=is_model_ready,
        n_samples=n_samples,
        n_raw_features=n_raw_features or 0,
        n_valid_features_before_preprocessing=n_valid_before,
        n_features_after_preprocessing=n_final,
        n_dropped_features=n_dropped,
        target_column=target_column,
        task_type=task_type,
    )

    # Column validation
    column_validation = ColumnValidation(
        dropped_invalid_features=[
            DroppedFeature(**d) for d in filter_result.get("dropped_invalid_features", [])
        ],
        dropped_all_missing_features=[
            DroppedFeature(**d) for d in filter_result.get("dropped_all_missing_features", [])
        ],
        dropped_constant_features=[
            DroppedFeature(**d) for d in filter_result.get("dropped_constant_features", [])
        ],
        dropped_high_missing_features=[
            DroppedFeature(**d) for d in filter_result.get("dropped_high_missing_features", [])
        ],
        retained_features=retained_features,
    )

    # Feature group validation
    fgv_items = [FeatureGroupValidationItem(**g) for g in group_validation]
    feature_group_validation = FeatureGroupValidation(groups=fgv_items)

    # Preprocessing execution
    preprocessing_execution = PreprocessingExecution(
        imputation=PreprocessingStepResult(
            executed=execution_result.get("imputation_executed", False),
            strategy="median",
            columns=[],
            artifact_component="numeric_imputer",
        ),
        scaling=PreprocessingStepResult(
            executed=execution_result.get("scaling_executed", False),
            strategy="standard_scaler",
            columns=[],
            artifact_component="numeric_scaler",
        ),
        categorical_encoding=PreprocessingStepResult(
            executed=False,
            strategy="none",
            columns=[],
        ),
        feature_selection=FeatureSelectionStepResult(
            executed=execution_result.get("feature_selection_executed", False),
            strategy="variance_threshold",
            columns_dropped=execution_result.get("selection_dropped_columns", []),
        ),
    )

    # Model-ready artifact
    model_ready_artifact = ModelReadyArtifact(
        artifact_id=model_ready_artifact_id,
        storage_type="parquet",
        file_path=model_ready_path,
        n_samples=artifact_result.get("model_ready_n_samples", n_samples),
        n_features=artifact_result.get("model_ready_n_features", n_final),
        target_column=target_column,
    )

    # Preprocessing pipeline artifact
    preprocessing_pipeline_artifact = PreprocessingPipelineArtifact(
        artifact_id=preprocessor_artifact_id,
        storage_type="joblib",
        file_path=preprocessor_path,
    )

    # Model search input
    model_search_input = ModelSearchInput(
        model_ready_artifact_id=model_ready_artifact_id,
        model_ready_matrix_path=model_ready_path,
        preprocessing_pipeline_artifact_id=preprocessor_artifact_id,
        target_column=target_column,
        feature_columns=final_features,
        task_type=task_type,
        primary_metric=primary_metric,
        model_strategy=plan_context.get("model_strategy", {}),
        validation_strategy=plan_context.get("validation_strategy", {}),
        evaluation_strategy=plan_context.get("evaluation_strategy", {}),
        hpo_strategy=plan_context.get("hpo_strategy", {}),
        ready_for_model_search=is_model_ready,
    )

    now = datetime.now()

    return FeaturePreprocessingResponse(
        preprocessing_id=preprocessing_id,
        task_id=context["task_id"],
        interpretation_id=context.get("interpretation_id"),
        dataset_profile_id=context.get("dataset_profile_id"),
        workflow_plan_id=context.get("workflow_plan_id"),
        feature_engineering_id=context.get("feature_engineering_id"),
        status=status,
        input_artifact=input_artifact,
        validation_summary=validation_summary,
        column_validation=column_validation,
        feature_group_validation=feature_group_validation,
        preprocessing_execution=preprocessing_execution,
        model_ready_artifact=model_ready_artifact,
        preprocessing_pipeline_artifact=preprocessing_pipeline_artifact,
        model_search_input=model_search_input,
        warnings=warnings,
        errors=errors,
        created_at=now,
        updated_at=now,
    )
