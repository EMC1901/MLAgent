"""Fold Pipeline Builder — builds FoldPipelineSpec from deferred fold_only operations."""
import logging
from typing import Dict, Any, List
from app.modules.feature_preprocessing.schemas import FoldPipelineSpec, FoldOperationSpec


logger = logging.getLogger(__name__)


def build_fold_pipeline_spec(
    deferred_operations: List[Dict[str, Any]],
    feature_columns: List[str],
    target_column: str,
    task_type: str,
    random_seed: int = 42,
) -> FoldPipelineSpec:
    """Build a FoldPipelineSpec from operations deferred from the global phase.

    Args:
        deferred_operations: List of operation dicts (from plan step + capability registry).
        feature_columns: Feature columns remaining after global phase.
        target_column: Target column name.
        task_type: 'regression' or 'classification'.
        random_seed: Random seed for reproducibility.

    Returns:
        FoldPipelineSpec for consumption by FoldPipelineExecutor.
    """
    ops = []
    for i, op in enumerate(deferred_operations):
        capability_id = op.get("capability_id", "unknown")
        op_type = _infer_operation_type(capability_id, op.get("capability_group", ""))
        ops.append(FoldOperationSpec(
            step_order=op.get("step_order", i + 1),
            operation_id=op.get("operation_id", f"fold_op_{i}"),
            capability_id=capability_id,
            capability_group=op.get("capability_group", "unknown"),
            target_columns=op.get("target_columns", []),
            target_feature_groups=op.get("target_feature_groups", []),
            parameters=op.get("parameters", {}),
            operation_type=op_type,
        ))

    spec = FoldPipelineSpec(
        spec_version="1.0.0",
        operations=ops,
        feature_columns=feature_columns,
        target_column=target_column,
        task_type=task_type,
        random_seed=random_seed,
    )

    logger.debug("built FoldPipelineSpec: %d ops — types=%s",
          len(ops), list(set(o.operation_type for o in ops)))
    for o in ops:
        logger.debug("  op %d: %s (group=%s, type=%s)", o.step_order, o.capability_id,
              o.capability_group, o.operation_type)

    return spec


def _infer_operation_type(capability_id: str, capability_group: str) -> str:
    """Infer operation_type from capability_id / group for the FoldOperationSpec."""
    if capability_id in ("median_imputer", "mean_imputer", "most_frequent_imputer",
                         "constant_imputer", "missing_indicator", "groupwise_imputer"):
        return "imputation"
    if capability_id in ("standard_scaler", "minmax_scaler", "robust_scaler",
                         "maxabs_scaler", "no_scaling", "groupwise_scaler",
                         "model_family_aware_scaling_policy"):
        return "scaling"
    if capability_id in ("log_transform", "log1p_transform", "signed_log_transform",
                         "power_transform_yeo_johnson", "quantile_transform_normal",
                         "quantile_transform_uniform", "auto_skewness_transform_selector"):
        return "transformation"
    if capability_id in ("mutual_information_selector", "f_regression_selector",
                         "f_classif_selector", "lasso_selector", "elastic_net_selector",
                         "tree_importance_selector", "recursive_feature_elimination",
                         "sequential_feature_selector", "max_feature_count_limiter"):
        return "feature_selection"
    if capability_id in ("pca_transform", "incremental_pca_transform",
                         "truncated_svd_transform", "feature_group_pca"):
        return "dimensionality_reduction"
    # Infer from group
    if "missing_value_handling" in capability_group:
        return "imputation"
    if "scaling" in capability_group:
        return "scaling"
    if "distribution" in capability_group:
        return "transformation"
    if "feature_selection" in capability_group:
        return "feature_selection"
    if "dimensionality" in capability_group:
        return "dimensionality_reduction"
    return "unknown"
