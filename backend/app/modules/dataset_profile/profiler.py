from typing import List


def determine_quality_level(
    schema_errors: List[str],
    quality_warnings: List[str],
    quality_errors: List[str],
    modality_consistent: bool,
    target_errors: List[str],
) -> str:
    """Determine overall data quality level from check results."""
    all_errors = schema_errors + quality_errors + target_errors
    if all_errors:
        return "unusable"

    total_issues = len(quality_warnings)
    if not modality_consistent:
        total_issues += 1

    if total_issues == 0:
        return "good"
    elif total_issues <= 2:
        return "fair"
    else:
        return "poor"


def determine_sample_size_level(n_samples: int) -> str:
    if n_samples < 100:
        return "very_small"
    elif n_samples < 1000:
        return "small"
    elif n_samples < 10000:
        return "medium"
    else:
        return "large"


def determine_recommended_step(
    is_usable: bool,
    quality_level: str,
) -> str:
    if not is_usable:
        return "needs_review"
    if quality_level == "poor":
        return "needs_cleaning"
    if quality_level == "unusable":
        return "blocked"
    return "ready_for_workflow_planning"


def aggregate_profiling_summary(
    is_loaded: bool,
    n_samples: int,
    schema_errors: List[str],
    modality_consistent: bool,
    quality_result: dict,
    target_result: dict,
) -> dict:
    quality_warnings = quality_result.get("warnings", [])
    quality_errors = quality_result.get("errors", [])
    target_errors = target_result.get("errors", [])

    is_usable = (
        is_loaded
        and n_samples > 0
        and len(schema_errors) == 0
        and len(target_errors) == 0
    )

    quality_level = determine_quality_level(
        schema_errors=schema_errors,
        quality_warnings=quality_warnings,
        quality_errors=quality_errors,
        modality_consistent=modality_consistent,
        target_errors=target_errors,
    )

    if not is_usable:
        quality_level = "unusable"

    sample_size_level = determine_sample_size_level(n_samples)

    main_issues = list(schema_errors) + list(quality_errors) + list(target_errors)
    if modality_consistent is False:
        main_issues.append("Input modality mismatch.")

    return {
        "is_loadable": is_loaded,
        "is_usable_for_ml": is_usable,
        "sample_size_level": sample_size_level,
        "quality_level": quality_level,
        "main_issues": main_issues,
        "recommended_next_step": determine_recommended_step(is_usable, quality_level),
    }


def build_workflow_planning_input(
    context: dict,
    n_samples: int,
    n_columns: int,
    input_columns: list,
    target_column: str,
    quality_result: dict,
    target_result: dict,
    quality_level: str,
    is_usable: bool,
) -> dict:
    has_missing = quality_result.get("missing_values", {}).get("total_missing", 0) > 0
    has_duplicates = quality_result.get("duplicates", {}).get("duplicate_rows", 0) > 0
    requires_cleaning = has_missing or has_duplicates

    skew_val = target_result.get("skewness")
    has_outliers = target_result.get("outlier_count", 0) > 0
    requires_target_transform = (
        (skew_val is not None and abs(skew_val) > 1) or has_outliers
    )

    target_dist = None
    if target_result.get("task_type") == "regression":
        target_dist = {
            "is_skewed": abs(target_result.get("skewness", 0)) > 1 if target_result.get("skewness") is not None else False,
            "has_outliers": has_outliers,
        }

    return {
        "input_modality": context.get("expected_input_modality"),
        "task_type": context.get("expected_task_type"),
        "target_column": target_column,
        "input_columns": input_columns,
        "n_samples": n_samples,
        "n_columns": n_columns,
        "n_features_raw": len(input_columns),
        "sample_size_level": determine_sample_size_level(n_samples),
        "has_missing_values": has_missing,
        "has_duplicates": has_duplicates,
        "requires_cleaning": requires_cleaning,
        "requires_target_transformation_check": requires_target_transform,
        "target_distribution": target_dist,
        "quality_level": quality_level,
        "is_usable_for_ml": is_usable,
    }
