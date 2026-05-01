import pandas as pd
from typing import List, Optional


def check_quality(
    df: pd.DataFrame,
    input_columns: List[str],
    target_column: Optional[str],
) -> dict:
    warnings: List[str] = []
    errors: List[str] = []

    n_rows, n_cols = df.shape

    # Missing values
    missing = df.isna().sum()
    total_missing = int(missing.sum())
    cols_with_missing = [c for c in df.columns if missing[c] > 0]

    if total_missing > 0:
        missing_pct = total_missing / (n_rows * n_cols) * 100
        warnings.append(
            f"Dataset contains {total_missing} missing values ({missing_pct:.1f}%) "
            f"across {len(cols_with_missing)} columns: {cols_with_missing}"
        )

    # Target column missing
    if target_column and target_column in df.columns:
        target_missing = int(df[target_column].isna().sum())
        if target_missing > 0:
            warnings.append(
                f"Target column '{target_column}' has {target_missing} missing values "
                f"({target_missing / n_rows * 100:.1f}%)."
            )

    # Duplicate rows
    dup_rows = int(df.duplicated().sum())
    if dup_rows > 0:
        warnings.append(f"Dataset contains {dup_rows} duplicate rows.")

    # Duplicate input samples
    dup_input = 0
    if input_columns:
        valid_input_cols = [c for c in input_columns if c in df.columns]
        if valid_input_cols:
            dup_input = int(df.duplicated(subset=valid_input_cols).sum())

    if dup_input > 0:
        warnings.append(
            f"Dataset contains {dup_input} rows with duplicate input values."
        )

    # Invalid values
    invalid_count = 0
    invalid_examples: list = []
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        empty_str = 0
        if df[col].dtype == object:
            empty_str = int((df[col].astype(str).str.strip() == "").sum())
        if empty_str > 0:
            invalid_count += empty_str
            if len(invalid_examples) < 5:
                invalid_examples.append({
                    "column": col,
                    "issue": "empty_string",
                    "count": empty_str,
                })

    # Constant columns
    for col in df.columns:
        if df[col].nunique(dropna=True) <= 1 and not df[col].isna().all():
            warnings.append(f"Column '{col}' is constant (only one unique value).")

    # High-missing-rate columns
    for col in df.columns:
        miss_rate = missing[col] / n_rows
        if miss_rate > 0.5:
            warnings.append(
                f"Column '{col}' has {miss_rate:.1%} missing values."
            )

    # Small sample
    if n_rows < 100:
        warnings.append(f"Dataset has only {n_rows} samples, which is very small.")

    return {
        "missing_values": {
            "total_missing": total_missing,
            "columns_with_missing": cols_with_missing,
        },
        "duplicates": {
            "duplicate_rows": dup_rows,
            "duplicate_input_samples": dup_input,
        },
        "invalid_rows": {
            "count": invalid_count,
            "examples": invalid_examples,
        },
        "warnings": warnings,
        "errors": errors,
    }
