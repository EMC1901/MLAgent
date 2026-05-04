import logging
import pandas as pd
from app.modules.feature_preprocessing.preprocessors.imputer import Imputer
from app.modules.feature_preprocessing.preprocessors.scaler import Scaler
from app.modules.feature_preprocessing.preprocessors.encoder import Encoder
from app.modules.feature_preprocessing.preprocessors.feature_selector import FeatureSelector
from app.modules.feature_preprocessing.enums import (
    ImputationStrategy,
    ScalingStrategy,
    EncodingStrategy,
    FeatureSelectionStrategy,
)

logger = logging.getLogger(__name__)


def execute_preprocessing(
    df: pd.DataFrame,
    target_column: str,
    feature_columns: list,
    imputation_strategy: str = ImputationStrategy.MEDIAN,
    scaling_strategy: str = ScalingStrategy.STANDARD_SCALER,
    encoding_strategy: str = EncodingStrategy.NONE,
    feature_selection_strategy: str = FeatureSelectionStrategy.VARIANCE_THRESHOLD,
) -> dict:
    """Execute the full preprocessing pipeline: imputation -> scaling -> feature selection.

    The target column and sample_id are excluded from processing.
    Returns the processed dataframe, execution details, and the fitted components.
    """
    warnings = []
    errors = []

    # Separate target and index columns from features
    non_feature_cols = []
    if "sample_id" in df.columns:
        non_feature_cols.append("sample_id")
    if target_column and target_column in df.columns:
        non_feature_cols.append(target_column)

    feature_df = df[feature_columns].copy()
    non_feature_df = df[non_feature_cols].copy() if non_feature_cols else pd.DataFrame(index=df.index)

    # 1. Imputation
    imputer = Imputer(strategy=imputation_strategy)
    imputation_executed = False
    imputation_columns = []
    try:
        feature_df = imputer.fit_transform(feature_df, feature_columns)
        imputation_columns = imputer.fitted_columns
        if imputation_columns:
            imputation_executed = True
            warnings.append("IMPUTATION_EXECUTED")
    except Exception as e:
        errors.append(f"IMPUTATION_FAILED: {e}")
        return {
            "dataframe": None,
            "feature_columns": feature_columns,
            "imputer": imputer,
            "scaler": None,
            "encoder": None,
            "feature_selector": None,
            "imputation_executed": False,
            "scaling_executed": False,
            "feature_selection_executed": False,
            "warnings": warnings,
            "errors": errors,
        }

    # 2. Scaling
    scaler = Scaler(strategy=scaling_strategy)
    scaling_executed = False
    scaling_strategy_used = ScalingStrategy.NONE if scaling_strategy == ScalingStrategy.NONE else scaling_strategy
    try:
        if scaling_strategy != ScalingStrategy.NONE:
            feature_df = scaler.fit_transform(feature_df, feature_columns)
            if scaler.fitted_columns:
                scaling_executed = True
                warnings.append("SCALING_EXECUTED")
    except Exception as e:
        errors.append(f"SCALING_FAILED: {e}")
        return {
            "dataframe": None,
            "feature_columns": feature_columns,
            "imputer": imputer,
            "scaler": scaler,
            "encoder": None,
            "feature_selector": None,
            "imputation_executed": imputation_executed,
            "scaling_executed": scaling_executed,
            "feature_selection_executed": False,
            "warnings": warnings,
            "errors": errors,
        }

    # 3. Feature Selection
    selector = FeatureSelector(strategy=feature_selection_strategy)
    feature_selection_executed = False
    selection_dropped = []
    try:
        if feature_selection_strategy != FeatureSelectionStrategy.NONE:
            feature_df = selector.fit_transform(feature_df, feature_columns)
            selection_dropped = selector.dropped_columns
            if selection_dropped:
                feature_selection_executed = True
                warnings.append("FEATURE_SELECTION_EXECUTED")
            # Update feature columns after selection
            feature_columns = selector.retained_columns
    except Exception as e:
        errors.append(f"FEATURE_SELECTION_FAILED: {e}")
        return {
            "dataframe": None,
            "feature_columns": feature_columns,
            "imputer": imputer,
            "scaler": scaler,
            "encoder": None,
            "feature_selector": selector,
            "imputation_executed": imputation_executed,
            "scaling_executed": scaling_executed,
            "feature_selection_executed": feature_selection_executed,
            "warnings": warnings,
            "errors": errors,
        }

    # Reassemble full dataframe: non-feature cols + processed features
    result_parts = []
    if not non_feature_df.empty:
        result_parts.append(non_feature_df)
    result_parts.append(feature_df)
    result_df = pd.concat(result_parts, axis=1)

    return {
        "dataframe": result_df,
        "feature_columns": feature_columns,
        "imputer": imputer,
        "scaler": scaler,
        "encoder": None,
        "feature_selector": selector,
        "imputation_executed": imputation_executed,
        "scaling_executed": scaling_executed,
        "feature_selection_executed": feature_selection_executed,
        "selection_dropped_columns": selection_dropped,
        "warnings": warnings,
        "errors": errors,
    }
