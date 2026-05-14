import hashlib
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
    FeatureQualityProfile,
    GlobalQualitySummary,
    PerFeatureSummary,
    PerGroupSummary,
    QualityWarning,
    ExecutionReport,
    ActionResult,
    FeatureProvenance,
    FeatureGroup,
    FeaturePreprocessingDecisionInput,
    PreprocessingRequirements,
    DownstreamInput,
)
from app.shared.registry.fe_capability_registry import get_registry_snapshot


def _compute_artifact_hash(artifact_path: str) -> str:
    try:
        return hashlib.sha256(artifact_path.encode()).hexdigest()[:16]
    except Exception:
        return "hash_unavailable"


def _build_quality_profile(feature_df, quality_result, feature_groups_list) -> FeatureQualityProfile:
    """Build a detailed feature quality profile from the feature matrix."""
    import pandas as pd
    import numpy as np

    n_rows = len(feature_df)
    n_cols = len(feature_df.columns)
    numeric_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()

    # Global summary
    missing_ratio = float(feature_df.isnull().mean().mean()) if n_cols > 0 else 0.0
    constant_count = len(quality_result.get("constant_features", []))
    near_constant_count = 0
    low_info_count = 0
    high_missing_count = 0
    high_corr_pair_count = 0
    high_skewness_count = 0

    per_feature = []
    for col in feature_df.columns:
        col_data = feature_df[col]
        col_missing = float(col_data.isnull().mean())
        if col_missing > 0.5:
            high_missing_count += 1

        is_numeric = col in numeric_cols
        variance_val = None
        skewness_val = None
        unique_ratio = float(col_data.nunique() / max(len(col_data), 1))

        if is_numeric and len(col_data.dropna()) > 0:
            variance_val = float(col_data.dropna().var())
            if variance_val is not None and variance_val < 1e-8:
                near_constant_count += 1
            try:
                skewness_val = float(col_data.dropna().skew())
            except Exception:
                skewness_val = 0.0
            if skewness_val is not None and abs(skewness_val) > 2.0:
                high_skewness_count += 1
        if unique_ratio < 0.02:
            low_info_count += 1

        source_group = ""
        for fg in feature_groups_list:
            if col in fg.get("feature_columns", []):
                source_group = fg.get("group_name", fg.get("display_name", ""))
                break

        per_feature.append(PerFeatureSummary(
            feature_name=col,
            dtype=str(col_data.dtype),
            missing_ratio=round(col_missing, 4),
            variance=round(variance_val, 6) if variance_val is not None else None,
            skewness=round(skewness_val, 4) if skewness_val is not None else None,
            unique_ratio=round(unique_ratio, 4),
            is_constant=col in quality_result.get("constant_features", []),
            is_near_constant=(variance_val is not None and variance_val < 1e-8),
            is_low_variance=unique_ratio < 0.02,
            source_feature_group=source_group,
        ))

    # Per-group summary
    per_group = []
    for fg in feature_groups_list:
        fg_cols = [c for c in fg.get("feature_columns", []) if c in feature_df.columns]
        if fg_cols:
            fg_df = feature_df[fg_cols]
            fg_numeric = fg_df.select_dtypes(include=[np.number])
            per_group.append(PerGroupSummary(
                group_name=fg.get("group_name", fg.get("display_name", "")),
                feature_count=len(fg_cols),
                missing_ratio=round(float(fg_df.isnull().mean().mean()), 4),
                constant_feature_count=len([c for c in fg_cols if c in quality_result.get("constant_features", [])]),
                near_constant_feature_count=0,
                avg_variance=round(float(fg_numeric.var().mean()), 6) if len(fg_numeric.columns) > 0 else None,
                avg_skewness=round(float(fg_numeric.skew().mean()), 4) if len(fg_numeric.columns) > 0 else None,
            ))

    # Quality warnings
    quality_warnings = []
    if missing_ratio > 0.1:
        quality_warnings.append(QualityWarning(warning_type="high_overall_missing", severity="high", message=f"Overall missing ratio {missing_ratio:.2%} exceeds 10%"))
    if high_missing_count > 0:
        quality_warnings.append(QualityWarning(warning_type="high_missing_features", severity="medium", message=f"{high_missing_count} features have >50% missing values"))
    if near_constant_count > 0:
        quality_warnings.append(QualityWarning(warning_type="near_constant_features", severity="low", message=f"{near_constant_count} near-constant features detected"))
    if high_skewness_count > 5:
        quality_warnings.append(QualityWarning(warning_type="high_skewness", severity="medium", message=f"{high_skewness_count} features with |skewness| > 2.0"))

    return FeatureQualityProfile(
        global_summary=GlobalQualitySummary(
            row_count=n_rows,
            feature_count=n_cols,
            numeric_feature_count=len(numeric_cols),
            categorical_feature_count=n_cols - len(numeric_cols),
            missing_value_ratio=round(missing_ratio, 4),
            constant_feature_count=constant_count,
            near_constant_feature_count=near_constant_count,
            low_information_feature_count=low_info_count,
            high_missing_feature_count=high_missing_count,
            high_correlation_pair_count=high_corr_pair_count,
            high_skewness_feature_count=high_skewness_count,
        ),
        per_feature_summary=per_feature,
        per_group_summary=per_group,
        quality_warnings=quality_warnings,
    )


def _build_execution_report(featurization_result, resolved_strategy) -> ExecutionReport:
    """Build action-level execution report."""
    action_results = []
    executed = featurization_result.get("executed_featurizers", [])
    selected = resolved_strategy.get("selected_featurizers", [])

    for i, featurizer_id in enumerate(selected):
        ef_match = next((e for e in executed if e.get("name") == featurizer_id), None)
        if ef_match:
            action_results.append(ActionResult(
                action_id=f"action_{i}_{featurizer_id}",
                capability_id=featurizer_id,
                status=ef_match.get("status", "unknown"),
                generated_feature_count=ef_match.get("n_features_generated", 0),
                warnings=[],
                error_message=None,
                fallback_action_id=None,
            ))
        else:
            action_results.append(ActionResult(
                action_id=f"action_{i}_{featurizer_id}",
                capability_id=featurizer_id,
                status="skipped",
                generated_feature_count=0,
                warnings=["Featurizer not executed"],
                error_message="Featurizer not found in execution results",
            ))

    return ExecutionReport(action_results=action_results)


def _build_feature_groups(featurization_result, resolved_strategy) -> list:
    """Build structured feature groups list."""
    groups = []
    executed = featurization_result.get("executed_featurizers", [])
    fg_list = featurization_result.get("feature_groups", [])

    for i, fg in enumerate(fg_list):
        ef_match = next((e for e in executed if e.get("name") == fg.get("group_name", "")), None)
        groups.append(FeatureGroup(
            group_id=f"fg_{i}_{fg.get('group_name', 'unknown')}",
            source_action_id=f"action_{i}_{fg.get('group_name', 'unknown')}",
            capability_id=fg.get("group_name", ""),
            feature_family="composition" if "composition" in str(fg.get("display_name", "")).lower() else "descriptor",
            feature_names=fg.get("feature_columns", [])[:50],  # Cap at 50 for response size
            feature_count=fg.get("n_features", 0),
            semantic_description=fg.get("display_name", ""),
        ))

    return groups


def _build_feature_provenance(artifact_result, featurization_result) -> FeatureProvenance:
    """Build feature provenance."""
    registry_snapshot = get_registry_snapshot()
    artifact_path = artifact_result.get("file_path", "")

    featurizer_versions = {}
    for ef in featurization_result.get("executed_featurizers", []):
        name = ef.get("name", "unknown")
        dep_versions = ef.get("dependency_versions", {})
        featurizer_versions[name] = dep_versions.get("version", "unknown")

    return FeatureProvenance(
        registry_snapshot_version=registry_snapshot["snapshot_version"],
        input_artifact_hash=_compute_artifact_hash(artifact_path),
        featurizer_versions=featurizer_versions,
        dependency_versions={},
        created_at=datetime.now(),
    )


def _build_preprocessing_decision_input(
    context, featurization_result, quality_profile, task_type, target_column, primary_metric, status
) -> dict:
    """Build the FeaturePreprocessingDecisionInput for module 6."""
    data_context = context.get("data_context") or {}
    task_context = context.get("task_context") or {}

    return {
        "task_context": {
            "task_type": task_type,
            "prediction_target": target_column,
            "evaluation_metric": primary_metric,
            "user_priority": task_context.get("user_priority", []),
        },
        "dataset_context": {
            "row_count": quality_profile.global_summary.row_count,
            "target_column": target_column,
            "input_modalities": [data_context.get("input_modality", "")],
            "data_quality_summary": {},
        },
        "workflow_context": {
            "workflow_plan_id": context.get("workflow_plan_id"),
            "feature_strategy_summary": {},
            "preprocessing_intent": {},
        },
        "feature_matrix_context": {
            "artifact_path": featurization_result.get("artifact_path", ""),
            "row_count": quality_profile.global_summary.row_count,
            "feature_count": quality_profile.global_summary.feature_count,
            "feature_groups": featurization_result.get("feature_groups", []),
            "feature_quality_profile": quality_profile.model_dump(mode="json"),
        },
        "execution_context": {
            "feature_engineering_status": status,
            "warnings": [],
            "failed_actions": [],
            "fallback_used": [],
        },
        "known_preprocessing_risks": [
            "missing_values" if quality_profile.global_summary.missing_value_ratio > 0 else None,
            "high_collinearity" if quality_profile.global_summary.feature_count > 50 else None,
            "skewed_distribution" if quality_profile.global_summary.high_skewness_feature_count > 0 else None,
            "low_information_features" if quality_profile.global_summary.low_information_feature_count > 0 else None,
            "possible_leakage",
        ],
    }


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

    # Feature generation (legacy)
    executed_featurizers = []
    fallback_ids = []
    skipped_ids = []
    feature_groups_list = []
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
            feature_groups_list.append({
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
        feature_groups=feature_schema.get("feature_groups", feature_groups_list),
        numeric_feature_count=feature_schema.get("numeric_feature_count", 0),
        categorical_feature_count=feature_schema.get("categorical_feature_count", 0),
        constant_feature_count=feature_schema.get("constant_feature_count", 0),
        all_missing_feature_count=feature_schema.get("all_missing_feature_count", 0),
    )

    # Feature quality (legacy)
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

    # NEW: Feature Quality Profile
    feature_df = featurization_result.get("feature_dataframe")
    if feature_df is not None:
        quality_profile = _build_quality_profile(feature_df, q, feature_groups_list)
    else:
        quality_profile = FeatureQualityProfile()

    # NEW: Execution Report
    execution_report = _build_execution_report(featurization_result, resolved_strategy)

    # NEW: Feature Groups (structured)
    feature_groups = _build_feature_groups(featurization_result, resolved_strategy)

    # NEW: Feature Provenance
    feature_provenance = _build_feature_provenance(artifact_result, featurization_result)

    # NEW: Preprocessing Decision Input
    preprocessing_decision_input = _build_preprocessing_decision_input(
        context, featurization_result, quality_profile,
        task_type, target_column, primary_metric, status
    )

    # Preprocessing requirements (legacy)
    preprocessing = PreprocessingRequirements(
        scaling_required=resolved_strategy.get("scaling_required", False),
        imputation_required=len(q.get("missing_values", {}).get("columns_with_missing", [])) > 0,
        feature_selection_required=resolved_strategy.get("feature_selection_required", False),
    )

    # Downstream input (legacy)
    feature_cols = feature_schema.get("feature_columns", [])
    downstream = DownstreamInput(
        feature_matrix_artifact_id=artifact_result.get("artifact_id"),
        feature_matrix_path=artifact_result.get("file_path"),
        target_column=target_column,
        feature_columns=feature_cols,
        feature_groups=feature_schema.get("feature_groups", feature_groups_list),
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
        executed_feature_strategy_id=resolved_strategy.get("strategy_id"),
        feature_groups=feature_groups,
        feature_quality_profile=quality_profile,
        execution_report=execution_report,
        feature_provenance=feature_provenance,
        feature_preprocessing_decision_input=FeaturePreprocessingDecisionInput(**preprocessing_decision_input),
        preprocessing_requirements=preprocessing,
        downstream_input=downstream,
        warnings=warnings,
        errors=errors,
        created_at=now,
        updated_at=now,
    )
