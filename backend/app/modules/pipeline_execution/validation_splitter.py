"""Validation Splitter - creates train/validation and external test splits."""

import numpy as np
from typing import List
from sklearn.model_selection import KFold, StratifiedKFold, train_test_split
from app.modules.pipeline_execution.exceptions import ValidationSplitException


def create_validation_splits(
    X,
    y,
    validation_plan: dict,
) -> List[dict]:
    """Generate validation splits.

    Args:
        X: Feature DataFrame or array.
        y: Target Series or array.
        validation_plan: Dict from execution_input with:
            - split_strategy: one of the upstream strategy names
            - n_splits: int (for k-fold variants)
            - random_state: int
            - shuffle: bool
            - test_size: float (for train_test_split/holdout)
            - stratification_required: bool

    Returns:
        List of dicts, each with:
            - fold_index: int
            - train_indices: np.ndarray
            - validation_indices: np.ndarray
            - train_size: int
            - validation_size: int
    """
    strategy = validation_plan.get("split_strategy", "train_test_split")
    random_state = validation_plan.get("random_state", 42)
    n = len(X)

    if n == 0:
        raise ValidationSplitException("Cannot split empty dataset.")

    # Normalize strategy names from upstream to local canonical names
    strategy = _normalize_strategy(strategy)

    if strategy in ("train_test_split", "holdout"):
        test_size = validation_plan.get("test_size", 0.2)
        shuffle = validation_plan.get("shuffle", True)
        stratify = None
        if validation_plan.get("stratification_required") and strategy != "holdout":
            try:
                stratify = y
            except Exception:
                stratify = None

        try:
            train_idx, val_idx = train_test_split(
                np.arange(n),
                test_size=test_size,
                random_state=random_state,
                shuffle=shuffle,
                stratify=stratify,
            )
        except Exception as e:
            raise ValidationSplitException(f"train_test_split failed: {e}")

        return [{
            "fold_index": 0,
            "train_indices": train_idx,
            "validation_indices": val_idx,
            "train_size": len(train_idx),
            "validation_size": len(val_idx),
        }]

    elif strategy == "k_fold":
        n_splits = validation_plan.get("n_splits", 5)
        shuffle = validation_plan.get("shuffle", True)
        try:
            kf = KFold(
                n_splits=n_splits, shuffle=shuffle, random_state=random_state
            )
        except Exception as e:
            raise ValidationSplitException(f"KFold setup failed: {e}")

        splits = []
        for fold_idx, (train_idx, val_idx) in enumerate(kf.split(X)):
            splits.append({
                "fold_index": fold_idx,
                "train_indices": train_idx,
                "validation_indices": val_idx,
                "train_size": len(train_idx),
                "validation_size": len(val_idx),
            })
        return splits

    elif strategy == "stratified_k_fold":
        n_splits = validation_plan.get("n_splits", 5)
        shuffle = validation_plan.get("shuffle", True)
        try:
            skf = StratifiedKFold(
                n_splits=n_splits, shuffle=shuffle, random_state=random_state
            )
        except Exception as e:
            raise ValidationSplitException(f"StratifiedKFold setup failed: {e}")

        splits = []
        for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X, y)):
            splits.append({
                "fold_index": fold_idx,
                "train_indices": train_idx,
                "validation_indices": val_idx,
                "train_size": len(train_idx),
                "validation_size": len(val_idx),
            })
        return splits

    elif strategy == "repeated_k_fold":
        from sklearn.model_selection import RepeatedKFold, RepeatedStratifiedKFold

        n_splits = validation_plan.get("n_splits", 5)
        n_repeats = validation_plan.get("n_repeats", 3)

        stratification_required = validation_plan.get("stratification_required", False)
        if stratification_required:
            if y is None:
                raise ValidationSplitException(
                    "RepeatedStratifiedKFold requires non-null y for stratification."
                )
            splitter = RepeatedStratifiedKFold(
                n_splits=n_splits, n_repeats=n_repeats, random_state=random_state
            )
        else:
            splitter = RepeatedKFold(
                n_splits=n_splits, n_repeats=n_repeats, random_state=random_state
            )

        splits = []
        for fold_idx, (train_idx, val_idx) in enumerate(splitter.split(X, y)):
            splits.append({
                "fold_index": fold_idx,
                "train_indices": train_idx,
                "validation_indices": val_idx,
                "train_size": len(train_idx),
                "validation_size": len(val_idx),
            })
        return splits

    else:
        raise ValidationSplitException(
            f"Unsupported split strategy: {validation_plan.get('split_strategy')}"
        )


def _normalize_strategy(strategy: str) -> str:
    """Map upstream strategy names to the canonical names used internally."""
    if not strategy:
        return "train_test_split"

    s = strategy.lower().strip()

    # k_fold_cross_validation éˆ?k_fold
    if s in ("k_fold_cross_validation", "k_fold_cv", "kfold", "k-fold"):
        return "k_fold"

    if s in ("repeated_cv", "repeated_k_fold", "repeated_kfold"):
        return "repeated_k_fold"

    # canonical names pass through
    if s in ("train_test_split", "k_fold", "stratified_k_fold", "holdout"):
        return s

    return s


def create_external_test_split(X, y, validation_plan: dict) -> dict:
    """Create the one-time external test split used before CV/HPO.

    The returned indices are positions relative to the original full dataset.
    Downstream validation splits must be created only on train_pool data.
    """
    n = len(X)
    if n == 0:
        raise ValidationSplitException("Cannot split empty dataset.")

    test_size = validation_plan.get(
        "external_test_size",
        validation_plan.get("test_size", 0.2),
    )
    random_state = validation_plan.get("random_state", 42)
    shuffle = validation_plan.get("shuffle", True)
    stratify = None
    if validation_plan.get("stratification_required"):
        if y is None:
            raise ValidationSplitException(
                "External stratified test split requires non-null y."
            )
        stratify = y

    try:
        train_pool_idx, test_idx = train_test_split(
            np.arange(n),
            test_size=test_size,
            random_state=random_state,
            shuffle=shuffle,
            stratify=stratify,
        )
    except Exception as e:
        raise ValidationSplitException(f"external train_test_split failed: {e}")

    return {
        "train_pool_indices": train_pool_idx,
        "test_indices": test_idx,
        "train_pool_size": len(train_pool_idx),
        "external_test_size": len(test_idx),
        "test_size": test_size,
    }
