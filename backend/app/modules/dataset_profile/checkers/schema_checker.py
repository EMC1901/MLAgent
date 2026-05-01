import pandas as pd
from typing import List, Optional


def check_schema(
    df: pd.DataFrame,
    expected_input_columns: List[str],
    expected_target_column: Optional[str],
) -> dict:
    errors: List[str] = []
    warnings: List[str] = []

    if df.empty:
        errors.append("DataFrame is empty.")
        return {
            "target_column_exists": False,
            "input_columns_exist": False,
            "duplicate_columns": [],
            "schema_errors": errors,
            "schema_warnings": warnings,
        }

    columns = list(df.columns)

    dup_cols = [c for c in columns if columns.count(c) > 1]
    dup_cols = list(set(dup_cols))
    if dup_cols:
        errors.append(f"Duplicate column names: {dup_cols}")

    target_exists = True
    if expected_target_column:
        if expected_target_column not in columns:
            # Try case-insensitive match
            col_lower = {c.lower(): c for c in columns}
            if expected_target_column.lower() in col_lower:
                warnings.append(
                    f"Target column '{expected_target_column}' matched "
                    f"case-insensitively to '{col_lower[expected_target_column.lower()]}'."
                )
            else:
                target_exists = False
                errors.append(
                    f"Target column '{expected_target_column}' not found in dataset. "
                    f"Available columns: {columns}"
                )

    input_cols_exist = True
    missing_inputs = []
    found_inputs = []
    for col in expected_input_columns:
        if col not in columns:
            col_lower = {c.lower(): c for c in columns}
            if col.lower() in col_lower:
                found_inputs.append((col, col_lower[col.lower()]))
            else:
                missing_inputs.append(col)
        else:
            found_inputs.append((col, col))

    if missing_inputs:
        if len(missing_inputs) == len(expected_input_columns):
            input_cols_exist = False
            errors.append(
                f"None of the expected input columns {expected_input_columns} found. "
                f"Available columns: {columns}"
            )
        else:
            warnings.append(
                f"Some expected input columns not found: {missing_inputs}"
            )

    for orig, found in found_inputs:
        if orig != found:
            warnings.append(
                f"Input column '{orig}' matched case-insensitively to '{found}'."
            )

    # Check for fully-null columns
    for col in columns:
        if df[col].isna().all():
            warnings.append(f"Column '{col}' is entirely null.")

    return {
        "target_column_exists": target_exists,
        "input_columns_exist": input_cols_exist,
        "duplicate_columns": dup_cols,
        "schema_errors": errors,
        "schema_warnings": warnings,
    }
