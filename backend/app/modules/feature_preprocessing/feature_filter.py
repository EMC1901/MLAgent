import pandas as pd
from typing import List
from app.modules.feature_preprocessing.column_validator import (
    identify_invalid_features,
    identify_all_missing_features,
    identify_constant_features,
    identify_high_missing_features,
    handle_invalid_inf_values,
)


def filter_features(
    df: pd.DataFrame,
    feature_columns: List[str],
    max_missing_ratio: float = 0.5,
) -> dict:
    """Run all feature filtering steps sequentially.

    Returns the filtered dataframe, remaining feature columns, and detailed
    drop records for each category.
    """
    current_df = df.copy()
    current_features = list(feature_columns)

    # 1. Drop invalid (non-numeric object) features
    dropped_invalid = identify_invalid_features(current_df, current_features)
    invalid_names = {d["name"] for d in dropped_invalid}
    current_features = [c for c in current_features if c not in invalid_names]

    # 2. Drop all-missing features
    dropped_all_missing = identify_all_missing_features(current_df, current_features)
    all_missing_names = {d["name"] for d in dropped_all_missing}
    current_features = [c for c in current_features if c not in all_missing_names]

    # 3. Drop constant features
    dropped_constant = identify_constant_features(current_df, current_features)
    constant_names = {d["name"] for d in dropped_constant}
    current_features = [c for c in current_features if c not in constant_names]

    # 4. Drop high-missing features
    dropped_high_missing = identify_high_missing_features(
        current_df, current_features, max_missing_ratio
    )
    high_missing_names = {d["name"] for d in dropped_high_missing}
    current_features = [c for c in current_features if c not in high_missing_names]

    # 5. Handle inf/-inf values
    inf_result = handle_invalid_inf_values(current_df, current_features)
    current_df = inf_result["dataframe"]
    current_features = inf_result["processed_columns"]
    dropped_inf = inf_result["dropped_columns"]

    all_dropped = (
        dropped_invalid
        + dropped_all_missing
        + dropped_constant
        + dropped_high_missing
        + dropped_inf
    )

    return {
        "dataframe": current_df,
        "retained_feature_columns": current_features,
        "dropped_invalid_features": dropped_invalid,
        "dropped_all_missing_features": dropped_all_missing,
        "dropped_constant_features": dropped_constant,
        "dropped_high_missing_features": dropped_high_missing,
        "dropped_inf_features": dropped_inf,
        "total_dropped": all_dropped,
    }
