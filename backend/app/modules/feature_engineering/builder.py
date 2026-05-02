from datetime import datetime
from app.modules.feature_engineering.enums import FeatureEngineeringStatus
from app.modules.feature_engineering.schemas import (
    FeatureEngineeringResponse,
    FeatureGeneration,
    ExecutedFeaturizer,
    FeatureMatrixInfo,
    FeatureSchemaInfo,
    FeatureQuality,
    MissingValues,
    PreprocessingRequirements,
    DownstreamInput,
)


def build_feature_engineering_object(
    feature_engineering_id: str,
    task_id: str,
    context: dict,
    status: str,
    featurization_result: dict,
    artifact_result: dict,
    feature_schema: dict,
    quality_result: dict,
    resolved_strategy: dict,
    warnings: list,
    errors: list,
) -> FeatureEngineeringResponse:

    data_context = context.get("data_context") or {}
    task_context = context.get("task_context") or {}

    target_column = data_context.get("target_column")
    task_type = task_context.get("task_type")
    primary_metric = task_context.get("evaluation_metric")

    # Feature generation
    executed_featurizers = []
    fallback_ids = []
    skipped_ids = []
    feature_groups = []
    for ef in featurization_result.get("executed_featurizers", []):
        executed_featurizers.append(ExecutedFeaturizer(
            name=ef.get("name", ""),
            display_name=ef.get("display_name", ""),
            status=ef.get("status", "unknown"),
            n_features_generated=ef.get("n_features_generated", 0),
            failed_sample_count=ef.get("failed_sample_count", 0),
            execution_time_ms=ef.get("execution_time_ms", 0),
            dependency_versions=ef.get("dependency_versions", {}),
        ))
        ef_status = ef.get("status", "")
        if ef_status in ("unavailable", "skipped"):
            skipped_ids.append(ef.get("name", ""))
        elif ef_status == "fallback_used":
            fallback_ids.append(ef.get("name", ""))

        if ef.get("n_features_generated", 0) > 0:
            feature_groups.append({
                "group_name": ef.get("name", ""),
                "display_name": ef.get("display_name", ""),
                "n_features": ef.get("n_features_generated", 0),
                "feature_columns": featurization_result.get("feature_columns", []),
                "status": ef.get("status", "unknown"),
            })

    feature_generation = FeatureGeneration(
        selected_featurizers=resolved_strategy.get("selected_featurizers", []),
        semantic_featurizers=resolved_strategy.get("semantic_featurizers", []),
        unsupported_future_featurizers=resolved_strategy.get("unsupported_featurizers", []),
        fallback_featurizers=fallback_ids,
        skipped_featurizers=skipped_ids,
        executed_featurizers=executed_featurizers,
    )

    # Feature matrix
    feature_matrix = FeatureMatrixInfo(
        artifact_id=artifact_result.get("artifact_id"),
        storage_type=artifact_result.get("storage_type", "local_file"),
        file_path=artifact_result.get("file_path"),
        n_samples=artifact_result.get("n_samples", 0),
        n_features=artifact_result.get("n_features", 0),
        target_column=target_column,
        index_column="sample_id",
    )

    # Feature schema
    feature_schema_obj = FeatureSchemaInfo(
        feature_columns=feature_schema.get("feature_columns", []),
        feature_groups=feature_schema.get("feature_groups", feature_groups),
        numeric_feature_count=feature_schema.get("numeric_feature_count", 0),
        categorical_feature_count=feature_schema.get("categorical_feature_count", 0),
        constant_feature_count=feature_schema.get("constant_feature_count", 0),
        all_missing_feature_count=feature_schema.get("all_missing_feature_count", 0),
    )

    # Feature quality
    q = quality_result
    feature_quality = FeatureQuality(
        missing_values=MissingValues(
            total_missing=q.get("missing_values", {}).get("total_missing", 0),
            columns_with_missing=q.get("missing_values", {}).get("columns_with_missing", []),
        ),
        invalid_features=q.get("invalid_features", []),
        dropped_features=q.get("dropped_features", []),
        failed_samples=featurization_result.get("failed_samples", []),
        constant_features=q.get("constant_features", []),
        all_missing_features=q.get("all_missing_features", []),
        is_valid_feature_matrix=q.get("is_valid_feature_matrix", False),
        warnings=q.get("warnings", []),
        errors=q.get("errors", []),
    )

    # Preprocessing requirements
    preprocessing = PreprocessingRequirements(
        scaling_required=resolved_strategy.get("scaling_required", False),
        imputation_required=len(q.get("missing_values", {}).get("columns_with_missing", [])) > 0,
        feature_selection_required=resolved_strategy.get("feature_selection_required", False),
    )

    # Downstream input
    feature_cols = feature_schema.get("feature_columns", [])
    downstream = DownstreamInput(
        feature_matrix_artifact_id=artifact_result.get("artifact_id"),
        feature_matrix_path=artifact_result.get("file_path"),
        target_column=target_column,
        feature_columns=feature_cols,
        feature_groups=feature_schema.get("feature_groups", feature_groups),
        task_type=task_type,
        primary_metric=primary_metric,
        scaling_required=resolved_strategy.get("scaling_required", False),
        imputation_required=preprocessing.imputation_required,
        feature_selection_required=resolved_strategy.get("feature_selection_required", False),
        ready_for_pipeline_generation=status in (
            FeatureEngineeringStatus.COMPLETED,
            FeatureEngineeringStatus.COMPLETED_WITH_WARNING,
        ),
    )

    now = datetime.now()

    return FeatureEngineeringResponse(
        feature_engineering_id=feature_engineering_id,
        task_id=context["task_id"],
        interpretation_id=context["interpretation_id"],
        dataset_profile_id=context["dataset_profile_id"],
        workflow_plan_id=context["workflow_plan_id"],
        status=status,
        input_modality=data_context.get("input_modality"),
        feature_type=resolved_strategy.get("feature_type"),
        feature_generation=feature_generation,
        feature_matrix=feature_matrix,
        feature_schema=feature_schema_obj,
        feature_quality=feature_quality,
        preprocessing_requirements=preprocessing,
        downstream_input=downstream,
        warnings=warnings,
        errors=errors,
        created_at=now,
        updated_at=now,
    )
