import pandas as pd
import re
from typing import List, Optional


def check_modality(
    df: pd.DataFrame,
    expected_input_modality: Optional[str],
    input_columns: List[str],
) -> dict:
    if not expected_input_modality:
        return {
            "expected_input_modality": None,
            "detected_input_modality": None,
            "is_consistent": True,
            "invalid_sample_count": 0,
            "messages": ["No expected input modality specified; skipping modality check."],
        }

    detected = _detect_modality(df, input_columns)
    is_consistent = detected == expected_input_modality
    messages = []
    invalid_count = 0

    if expected_input_modality == "composition":
        invalid_count = _check_composition(df, input_columns)

    if not is_consistent:
        messages.append(
            f"Expected modality '{expected_input_modality}' but detected '{detected}'."
        )

    if invalid_count > 0:
        messages.append(
            f"{invalid_count} samples appear invalid for modality '{expected_input_modality}'."
        )

    return {
        "expected_input_modality": expected_input_modality,
        "detected_input_modality": detected,
        "is_consistent": is_consistent,
        "invalid_sample_count": invalid_count,
        "messages": messages,
    }


def _detect_modality(df: pd.DataFrame, input_columns: List[str]) -> str:
    if not input_columns:
        return "unknown"

    # Use only columns that actually exist in the dataframe.
    # LLM-interpreted expected_input_columns may not match the actual file columns.
    available_cols = [c for c in input_columns if c in df.columns]
    if not available_cols:
        available_cols = list(df.columns)
    if not available_cols:
        return "unknown"

    col_to_check = available_cols[0]
    col_names_lower = " ".join(c.lower() for c in input_columns)
    sample_values = df[col_to_check].dropna().head(20).astype(str)

    if any(kw in col_names_lower for kw in ("composition", "formula", "chemical")):
        return "composition"

    if any(kw in col_names_lower for kw in ("cif", "poscar", "structure", "struct")):
        return "structure"

    if _looks_like_composition(sample_values):
        return "composition"

    numeric_input_cols = [c for c in input_columns if c in df.columns]
    if numeric_input_cols and df[numeric_input_cols].select_dtypes(include=["number"]).shape[1] == len(numeric_input_cols):
        return "descriptor"

    sample_str = sample_values.str.cat(sep=" ")
    if len(sample_str) > 500:
        return "text"

    return "mixed"


def _looks_like_composition(series: pd.Series) -> bool:
    """Check if values look like chemical formulas."""
    pattern = re.compile(r"^[A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)*$")
    matches = series.astype(str).str.strip().apply(lambda s: bool(pattern.match(s)))
    return matches.sum() >= len(series) * 0.7


def _check_composition(df: pd.DataFrame, input_columns: List[str]) -> int:
    """Count obviously invalid composition entries."""
    if not input_columns:
        return 0
    col = input_columns[0]
    if col not in df.columns:
        return 0
    invalid = 0
    series = df[col].dropna().astype(str).str.strip()
    for val in series:
        if val == "" or val.isdigit():
            invalid += 1
    return invalid
