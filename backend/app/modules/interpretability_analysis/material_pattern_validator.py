"""Phase 3a: Material Pattern Validation.

Validates MaterialPatternCandidates produced by Phase 2 mining against
the actual data (X, y_true, y_pred, model) using four validation strategies:
  - subgroup_contrast: compare in-scope vs out-scope predictions
  - bootstrap_effect_ci: bootstrap confidence interval for effect delta
  - ice_consistency: individual conditional expectation direction check
  - boundary_error_check: verify boundary patterns have elevated errors

Each validation produces a PatternValidationResult attached to the pattern.
"""

import uuid
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from app.modules.interpretability_analysis.schemas import (
    MaterialPatternCandidate,
    PatternSampleSupport,
    PatternValidationResult,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Condition-to-Mask Engine
# ============================================================================


def build_condition_mask(
    X,
    conditions: List[Any],
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Build a boolean mask from a list of PatternCondition objects.

    Returns (mask, stats_dict) where mask is True for rows that satisfy ALL
    conditions (AND semantics), and stats_dict contains per-condition
    diagnostic info.

    Raises:
        ValueError: if a condition references a feature not in X.columns.
    """
    if X is None or len(X) == 0:
        return np.array([], dtype=bool), {}
    if not conditions:
        # No conditions → cannot form a meaningful subgroup mask.
        return np.zeros(len(X), dtype=bool), {"_n_total": len(X), "_conditions": [], "_combined_count": 0, "_warning": "empty_conditions"}

    n = len(X)
    combined = np.ones(n, dtype=bool)
    stats: Dict[str, Any] = {"_n_total": n, "_conditions": []}

    for cond in conditions:
        feat = cond.feature_name
        if feat not in X.columns:
            raise ValueError(
                f"Condition feature '{feat}' not found in X.columns"
            )
        col = X[feat].values.astype(float)
        op = cond.operator
        qrange = cond.quantile_range
        vrange = cond.value_range

        if op == "low":
            if qrange and len(qrange) >= 2:
                lo, hi = np.quantile(col, qrange[0]), np.quantile(col, qrange[1])
            else:
                lo, hi = col.min(), np.quantile(col, 0.25)
            row_mask = (col >= lo) & (col <= hi)
            stats["_conditions"].append({
                "feature": feat, "operator": op,
                "bounds": [float(lo), float(hi)], "count": int(row_mask.sum()),
            })

        elif op == "high":
            if qrange and len(qrange) >= 2:
                lo, hi = np.quantile(col, qrange[0]), np.quantile(col, qrange[1])
            else:
                lo, hi = np.quantile(col, 0.75), col.max()
            row_mask = (col >= lo) & (col <= hi)
            stats["_conditions"].append({
                "feature": feat, "operator": op,
                "bounds": [float(lo), float(hi)], "count": int(row_mask.sum()),
            })

        elif op == "between":
            vmin = vrange.get("min") if vrange else None
            vmax = vrange.get("max") if vrange else None
            if vmin is None or vmax is None:
                if qrange and len(qrange) >= 2:
                    vmin = float(np.quantile(col, qrange[0]))
                    vmax = float(np.quantile(col, qrange[1]))
                else:
                    vmin = float(np.quantile(col, 0.25))
                    vmax = float(np.quantile(col, 0.75))
            row_mask = (col >= float(vmin)) & (col <= float(vmax))
            stats["_conditions"].append({
                "feature": feat, "operator": op,
                "bounds": [float(vmin), float(vmax)], "count": int(row_mask.sum()),
            })

        elif op == "outside":
            vmin = vrange.get("min") if vrange else None
            vmax = vrange.get("max") if vrange else None
            if vmin is None or vmax is None:
                if qrange and len(qrange) >= 2:
                    vmin = float(np.quantile(col, qrange[0]))
                    vmax = float(np.quantile(col, qrange[1]))
                else:
                    vmin = float(np.quantile(col, 0.05))
                    vmax = float(np.quantile(col, 0.95))
            row_mask = (col < float(vmin)) | (col > float(vmax))
            stats["_conditions"].append({
                "feature": feat, "operator": op,
                "bounds": [float(vmin), float(vmax)], "count": int(row_mask.sum()),
            })

        elif op in ("increasing", "decreasing"):
            # Split at median for contrast group.
            # For both directions the in-scope is the high-value group:
            #   increasing: high group → higher target → positive delta
            #   decreasing: high group → lower target → negative delta
            median = float(np.median(col))
            row_mask = col >= median
            stats["_conditions"].append({
                "feature": feat, "operator": op,
                "split_value": median, "count": int(row_mask.sum()),
            })

        else:
            # Unknown or empty operator — reject all rows so the pattern
            # is flagged as unactionable downstream rather than silently
            # producing a full-population mask with spurious metrics.
            if not op or op.strip() == "":
                row_mask = np.zeros(n, dtype=bool)
                stats["_conditions"].append({
                    "feature": feat, "operator": op or "(empty)",
                    "count": 0, "warning": "empty_operator",
                })
            else:
                row_mask = np.zeros(n, dtype=bool)
                stats["_conditions"].append({
                    "feature": feat, "operator": op,
                    "count": 0, "warning": "unknown_operator",
                })

        combined = combined & row_mask

    stats["_combined_count"] = int(combined.sum())
    return combined, stats


# ============================================================================
# Validation Functions
# ============================================================================


def _validate_subgroup_contrast(
    pattern: MaterialPatternCandidate,
    X,
    y_true,
    y_pred,
) -> PatternValidationResult:
    """Compare in-scope vs out-scope predictions and ground truth."""
    result = PatternValidationResult(
        validation_id=f"val_{uuid.uuid4().hex[:8]}",
        pattern_id=pattern.pattern_id,
        validation_type="subgroup_contrast",
    )

    try:
        mask, mask_stats = build_condition_mask(X, pattern.conditions)
    except ValueError as e:
        result.status = "fail"
        result.interpretation = str(e)
        result.limitations = [str(e)]
        return result

    in_count = int(mask.sum())
    out_count = int((~mask).sum())

    if in_count < 3:
        result.status = "weak"
        result.interpretation = (
            f"In-scope sample too small ({in_count} samples); "
            "subgroup contrast is unreliable."
        )
        result.metrics = {
            "in_scope_count": in_count,
            "out_scope_count": out_count,
        }
        result.limitations = ["Insufficient in-scope samples for reliable contrast."]
        return result

    if out_count < 3:
        result.status = "not_applicable"
        result.interpretation = (
            f"Out-scope sample too small ({out_count} samples); "
            "cannot form a meaningful contrast group. The condition mask "
            "may cover nearly the entire population."
        )
        result.metrics = {
            "in_scope_count": in_count,
            "out_scope_count": out_count,
        }
        result.limitations = [
            "Condition mask covers nearly all samples; no meaningful contrast group."
        ]
        return result

    yp = np.asarray(y_pred, dtype=float)
    in_pred_mean = float(np.mean(yp[mask]))
    out_pred_mean = float(np.mean(yp[~mask]))
    predicted_delta = in_pred_mean - out_pred_mean

    metrics: Dict[str, Any] = {
        "in_scope_count": in_count,
        "out_scope_count": out_count,
        "predicted_delta": round(predicted_delta, 6),
        "in_scope_pred_mean": round(in_pred_mean, 6),
        "out_scope_pred_mean": round(out_pred_mean, 6),
    }

    direction_matches = True
    effect_dir = pattern.predicted_effect.target_direction
    if effect_dir == "increases" and predicted_delta <= 0:
        direction_matches = False
    elif effect_dir == "decreases" and predicted_delta >= 0:
        direction_matches = False
    elif effect_dir == "peaks" and abs(predicted_delta) < 1e-8:
        direction_matches = False  # No peak evidence in mean difference
    metrics["direction_matches_candidate"] = direction_matches

    if y_true is not None:
        yt = np.asarray(y_true, dtype=float)
        in_true_mean = float(np.mean(yt[mask]))
        out_true_mean = float(np.mean(yt[~mask]))
        observed_delta = in_true_mean - out_true_mean
        metrics["observed_delta"] = round(observed_delta, 6)
        metrics["in_scope_true_mean"] = round(in_true_mean, 6)
        metrics["out_scope_true_mean"] = round(out_true_mean, 6)

        abs_err = np.abs(yp - yt)
        in_err = float(np.mean(abs_err[mask]))
        out_err = float(np.mean(abs_err[~mask]))
        metrics["in_scope_mean_abs_error"] = round(in_err, 6)
        metrics["out_scope_mean_abs_error"] = round(out_err, 6)
        error_ratio = in_err / max(out_err, 1e-12)
        metrics["error_ratio"] = round(error_ratio, 4)

    # Determine status
    if not direction_matches:
        result.status = "fail"
        result.interpretation = (
            f"Predicted delta ({predicted_delta:.4f}) contradicts candidate "
            f"direction '{effect_dir}'."
        )
    elif in_count < 10:
        result.status = "weak"
        result.interpretation = (
            f"Direction matches but in-scope count ({in_count}) is low."
        )
    elif "error_ratio" in metrics and metrics["error_ratio"] > 2.0:
        result.status = "weak"
        result.interpretation = (
            f"Direction matches but in-scope error is {metrics['error_ratio']:.1f}x "
            "out-scope error, suggesting noise dominates signal."
        )
    else:
        result.status = "pass"
        result.interpretation = (
            f"Subgroup contrast passes: predicted delta={predicted_delta:.4f}, "
            f"in_scope={in_count}, out_scope={out_count}."
        )

    # Observed direction check: if y_true is available and its delta
    # contradicts the candidate direction, the model's prediction trend is
    # NOT backed by ground truth.  This runs unconditionally (not gated on
    # status==pass) so that a large observed conflict can escalate a
    # small-sample "weak" to "fail".
    if y_true is not None and "observed_delta" in metrics:
        obs_delta = metrics["observed_delta"]
        obs_dir_conflict = (
            (effect_dir == "increases" and obs_delta < 0)
            or (effect_dir == "decreases" and obs_delta > 0)
        )
        if obs_dir_conflict:
            if abs(obs_delta) > abs(predicted_delta) * 0.5:
                result.status = "fail"
                result.interpretation += (
                    f" GROUND-TRUTH CONFLICT: observed delta ({obs_delta:.4f}) "
                    f"has opposite sign to predicted delta ({predicted_delta:.4f}) — "
                    "model trend is not backed by measured data."
                )
                result.limitations.append(
                    "Model prediction trend contradicts ground-truth observations; "
                    "this pattern may reflect a model artifact rather than a real effect."
                )
            elif result.status == "pass":
                result.status = "weak"
                result.interpretation += (
                    f" NOTE: observed delta ({obs_delta:.4f}) weakly contradicts "
                    f"predicted delta ({predicted_delta:.4f})."
                )
                result.limitations.append(
                    "Observed delta weakly conflicts with predicted direction; "
                    "treat this pattern as model-supported only."
                )

    result.metrics = metrics
    return result


def _validate_bootstrap_effect_ci(
    pattern: MaterialPatternCandidate,
    X,
    y_pred,
    random_state: int = 42,
    n_bootstrap: int = 1000,
) -> PatternValidationResult:
    """Bootstrap confidence interval for the in/out-scope prediction delta."""
    result = PatternValidationResult(
        validation_id=f"val_{uuid.uuid4().hex[:8]}",
        pattern_id=pattern.pattern_id,
        validation_type="bootstrap",
    )

    try:
        mask, _mask_stats = build_condition_mask(X, pattern.conditions)
    except ValueError as e:
        result.status = "not_applicable"
        result.interpretation = str(e)
        result.limitations = [str(e)]
        return result

    in_count = int(mask.sum())
    out_count = int((~mask).sum())

    if in_count < 5:
        result.status = "not_applicable"
        result.interpretation = (
            f"In-scope count ({in_count}) too small for bootstrap (need >= 5)."
        )
        result.limitations = ["Insufficient samples for bootstrap."]
        result.metrics = {"in_scope_count": in_count, "bootstrap_n": 0}
        return result

    if out_count < 5:
        result.status = "not_applicable"
        result.interpretation = (
            f"Out-scope count ({out_count}) too small for bootstrap (need >= 5)."
        )
        result.limitations = ["Insufficient out-scope samples for bootstrap."]
        result.metrics = {"in_scope_count": in_count, "out_scope_count": out_count, "bootstrap_n": 0}
        return result

    yp = np.asarray(y_pred, dtype=float)
    rng = np.random.RandomState(random_state)
    in_idx = np.where(mask)[0]
    out_idx = np.where(~mask)[0]

    deltas = np.empty(n_bootstrap, dtype=float)
    for i in range(n_bootstrap):
        bs_in = rng.choice(in_idx, size=len(in_idx), replace=True)
        bs_out = rng.choice(out_idx, size=len(out_idx), replace=True)
        deltas[i] = float(np.mean(yp[bs_in]) - np.mean(yp[bs_out]))

    ci_low = float(np.percentile(deltas, 2.5))
    ci_high = float(np.percentile(deltas, 97.5))
    ci_excludes_zero = bool(ci_low > 0 or ci_high < 0)
    delta_mean = float(np.mean(deltas))

    metrics = {
        "in_scope_count": in_count,
        "out_scope_count": out_count,
        "bootstrap_n": n_bootstrap,
        "delta_mean": round(delta_mean, 6),
        "delta_ci_low": round(ci_low, 6),
        "delta_ci_high": round(ci_high, 6),
        "ci_excludes_zero": ci_excludes_zero,
    }
    result.metrics = metrics

    if in_count < 20:
        result.status = "weak"
        result.interpretation = (
            f"Bootstrap CI [{ci_low:.4f}, {ci_high:.4f}] but in-scope "
            f"count ({in_count}) is small — CI may be unreliable."
        )
        result.limitations = [
            f"Only {in_count} in-scope samples; bootstrap CI width may be inflated."
        ]
    elif not ci_excludes_zero:
        result.status = "weak"
        result.interpretation = (
            f"Bootstrap CI [{ci_low:.4f}, {ci_high:.4f}] includes zero "
            "— effect may not be statistically distinguishable from noise."
        )
        result.limitations = ["CI includes zero; effect may not be reliable."]
    else:
        result.status = "pass"
        result.interpretation = (
            f"Bootstrap CI [{ci_low:.4f}, {ci_high:.4f}] excludes zero "
            f"with {in_count} in-scope, {out_count} out-scope samples."
        )

    return result


def _validate_ice_consistency(
    pattern: MaterialPatternCandidate,
    X,
    model,
    random_state: int = 42,
    max_samples: int = 200,
    n_grid: int = 20,
) -> PatternValidationResult:
    """Check if individual conditional expectation (ICE) curves agree with pattern direction.

    Only applies to monotonic/threshold/window patterns with single-feature conditions.
    Works by varying the condition feature across its range for sampled rows
    and checking whether the prediction moves in the expected direction.
    """
    result = PatternValidationResult(
        validation_id=f"val_{uuid.uuid4().hex[:8]}",
        pattern_id=pattern.pattern_id,
        validation_type="ice_consistency",
    )

    if model is None:
        result.status = "not_applicable"
        result.interpretation = "No model available for ICE computation."
        result.limitations = ["Model not provided."]
        return result

    ptype = pattern.pattern_type
    if ptype not in ("monotonic", "threshold", "window"):
        result.status = "not_applicable"
        result.interpretation = (
            f"ICE consistency not applicable to pattern_type='{ptype}'."
        )
        return result

    if not pattern.conditions:
        result.status = "not_applicable"
        result.interpretation = "No conditions defined; cannot build ICE grid."
        return result

    effect_dir = pattern.predicted_effect.target_direction
    if effect_dir in ("uncertain", ""):
        result.status = "not_applicable"
        result.interpretation = f"No clear effect direction ('{effect_dir}')."
        return result

    # Use the first condition feature as the varying feature for ICE
    target_feat = pattern.conditions[0].feature_name
    if target_feat not in X.columns:
        result.status = "not_applicable"
        result.interpretation = (
            f"Condition feature '{target_feat}' not in X.columns."
        )
        return result

    col = X[target_feat].values.astype(float)
    feat_min, feat_max = float(col.min()), float(col.max())
    grid = np.linspace(feat_min, feat_max, n_grid)

    # Sample rows for ICE
    rng = np.random.RandomState(random_state)
    n_sample = min(len(X), max_samples)
    sample_idx = rng.choice(len(X), size=n_sample, replace=False)

    X_np = X.values.astype(float)
    feat_col_idx = list(X.columns).index(target_feat)

    # For each sampled row, vary target feature across grid
    row_predictions = np.zeros((n_sample, n_grid))
    for i, row_i in enumerate(sample_idx):
        row = X_np[row_i:row_i + 1].copy()
        for j, gv in enumerate(grid):
            row[0, feat_col_idx] = gv
            try:
                pred = model.predict(row)
                row_predictions[i, j] = float(pred[0] if hasattr(pred, '__len__') else pred)
            except Exception:
                row_predictions[i, j] = np.nan

    # Mask rows with NaN predictions
    valid = ~np.isnan(row_predictions).any(axis=1)
    if valid.sum() < 10:
        result.status = "weak"
        result.interpretation = (
            f"Only {valid.sum()} valid ICE rows; cannot assess consistency."
        )
        result.limitations = ["Too few valid ICE rows."]
        result.metrics = {"valid_rows": int(valid.sum()), "total_rows": n_sample}
        return result

    row_predictions = row_predictions[valid]

    # Compute per-row trend: correlation between grid position and prediction
    expected_sign = 1 if effect_dir == "increases" else -1
    n_agree = 0
    for k in range(row_predictions.shape[0]):
        preds = row_predictions[k]
        # Simple rank correlation proxy: last vs first
        n_half = n_grid // 2
        first_half_mean = np.mean(preds[:n_half])
        second_half_mean = np.mean(preds[n_half:])
        row_sign = 1 if second_half_mean > first_half_mean else -1
        if row_sign == expected_sign:
            n_agree += 1

    agreement_ratio = n_agree / row_predictions.shape[0]
    metrics = {
        "n_ice_rows": row_predictions.shape[0],
        "n_grid_points": n_grid,
        "agreement_ratio": round(agreement_ratio, 4),
        "target_feature": target_feat,
        "effect_direction": effect_dir,
    }
    result.metrics = metrics

    if agreement_ratio >= 0.7:
        result.status = "pass"
        result.interpretation = (
            f"ICE consistency passes: {agreement_ratio:.1%} of rows show "
            f"the expected '{effect_dir}' trend for '{target_feat}'."
        )
    elif agreement_ratio >= 0.5:
        result.status = "weak"
        result.interpretation = (
            f"ICE consistency is marginal: only {agreement_ratio:.1%} of rows "
            f"agree with the '{effect_dir}' trend."
        )
        result.limitations = ["Marginal ICE agreement; pattern may be noisy."]
    else:
        result.status = "fail"
        result.interpretation = (
            f"ICE consistency fails: only {agreement_ratio:.1%} of rows "
            f"agree with '{effect_dir}'. Pattern may not hold at the individual level."
        )
        result.limitations = ["ICE disagreement suggests pattern may be an artifact of averaging."]

    return result


def _validate_boundary_error_check(
    pattern: MaterialPatternCandidate,
    X,
    y_true,
    y_pred,
) -> PatternValidationResult:
    """For boundary patterns, verify error is elevated in the boundary region."""
    result = PatternValidationResult(
        validation_id=f"val_{uuid.uuid4().hex[:8]}",
        pattern_id=pattern.pattern_id,
        validation_type="boundary_error_check",
    )

    if pattern.pattern_type != "boundary":
        result.status = "not_applicable"
        result.interpretation = "Not a boundary pattern."
        return result

    if y_true is None or y_pred is None:
        result.status = "not_applicable"
        result.interpretation = "y_true required for error computation."
        result.limitations = ["Ground truth not available."]
        return result

    try:
        mask, _mask_stats = build_condition_mask(X, pattern.conditions)
    except ValueError as e:
        result.status = "fail"
        result.interpretation = str(e)
        return result

    in_count = int(mask.sum())
    out_count = int((~mask).sum())

    if in_count < 3:
        result.status = "weak"
        result.interpretation = (
            f"Boundary region has only {in_count} samples; "
            "cannot reliably assess error elevation."
        )
        result.metrics = {"in_scope_count": in_count, "out_scope_count": out_count}
        result.limitations = ["Insufficient boundary samples."]
        return result

    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    abs_err = np.abs(yp - yt)

    in_err = float(np.mean(abs_err[mask]))
    out_err = float(np.mean(abs_err[~mask]))
    overall_err = float(np.mean(abs_err))
    error_ratio = in_err / max(out_err, 1e-12)

    metrics = {
        "in_scope_count": in_count,
        "out_scope_count": out_count,
        "boundary_mean_abs_error": round(in_err, 6),
        "non_boundary_mean_abs_error": round(out_err, 6),
        "overall_mean_abs_error": round(overall_err, 6),
        "error_ratio": round(error_ratio, 4),
    }
    result.metrics = metrics

    if error_ratio >= 1.5:
        result.status = "pass"
        result.interpretation = (
            f"Boundary region error ({in_err:.4f}) is {error_ratio:.1f}x "
            f"non-boundary error ({out_err:.4f}) — confirming elevated error."
        )
    elif error_ratio >= 1.2:
        result.status = "weak"
        result.interpretation = (
            f"Boundary error ({in_err:.4f}) is only {error_ratio:.1f}x "
            f"non-boundary error — marginal elevation."
        )
        result.limitations = ["Error elevation is marginal; boundary may be weak."]
    else:
        result.status = "fail"
        result.interpretation = (
            f"Boundary region error ({in_err:.4f}) is NOT elevated vs "
            f"non-boundary ({out_err:.4f}); pattern may be spurious."
        )
        result.limitations = ["No error elevation in boundary region."]

    return result


# ============================================================================
# Main Entry Point
# ============================================================================


def validate_material_patterns(
    patterns: List[MaterialPatternCandidate],
    X,
    y_true,
    y_pred,
    model=None,
    evidence_units=None,
    feature_profiles=None,
    partial_dependence=None,
    shap_dependence=None,
    max_patterns_for_ice: int = 5,
    random_state: int = 42,
) -> List[MaterialPatternCandidate]:
    """Validate and enrich material pattern candidates with empirical checks.

    Applies up to four validations per pattern:
      1. subgroup_contrast — always applied
      2. bootstrap_effect_ci — always applied
      3. ice_consistency — only for monotonic/threshold/window, top-N by confidence
      4. boundary_error_check — only for boundary patterns

    Each validation result is appended to pattern.validation_results.
    Pattern.sample_support is set from the subgroup_contrast mask.
    Pattern.validation_status is set to the worst status across validations
    (fail > weak > pass).

    Args:
        patterns: Mined MaterialPatternCandidates from Phase 2.
        X: Feature DataFrame.
        y_true: Ground-truth target values (may be None).
        y_pred: Model predictions (may be None).
        model: Trained model with a .predict() method (may be None).
        evidence_units: Unused; reserved for future evidence-driven validation.
        feature_profiles: Unused; reserved for cross-referencing.
        partial_dependence: Unused; reserved for PDP-anchored validation.
        shap_dependence: Unused; reserved for SHAP-anchored validation.
        max_patterns_for_ice: Cap on ICE validation to control cost.
        random_state: Seed for reproducibility.

    Returns:
        The same list of patterns with validation fields populated.
    """
    if not patterns:
        return patterns

    if X is None or y_pred is None:
        logger.warning("validate_material_patterns: X or y_pred is None; skipping.")
        for p in patterns:
            p.validation_status = "unvalidated"
        return patterns

    if len(y_pred) != len(X):
        logger.warning(
            "validate_material_patterns: X has %d rows but y_pred has %d rows; "
            "skipping empirical validation to avoid mask/prediction misalignment.",
            len(X),
            len(y_pred),
        )
        for p in patterns:
            p.validation_status = "unvalidated"
            p.limitations.append(
                "Pattern validation skipped because feature rows and predictions are not row-aligned."
            )
        return patterns

    if y_true is not None and len(y_true) != len(X):
        logger.warning(
            "validate_material_patterns: X has %d rows but y_true has %d rows; "
            "continuing with prediction-only validation.",
            len(X),
            len(y_true),
        )
        y_true = None

    # Determine which patterns get ICE (expensive — only top-N non-boundary)
    non_boundary = [p for p in patterns if p.pattern_type != "boundary"]
    non_boundary_sorted = sorted(non_boundary, key=lambda p: p.confidence_score, reverse=True)
    ice_eligible_ids = {p.pattern_id for p in non_boundary_sorted[:max_patterns_for_ice]}

    for pattern in patterns:
        validations: List[PatternValidationResult] = []

        # 1. Subgroup contrast — always
        if y_pred is not None:
            v_sc = _validate_subgroup_contrast(pattern, X, y_true, y_pred)
            validations.append(v_sc)

        # 2. Bootstrap CI — always
        if y_pred is not None:
            v_bs = _validate_bootstrap_effect_ci(pattern, X, y_pred, random_state=random_state)
            validations.append(v_bs)

        # 3. ICE consistency — selective
        if pattern.pattern_id in ice_eligible_ids:
            v_ice = _validate_ice_consistency(pattern, X, model, random_state=random_state)
            validations.append(v_ice)

        # 4. Boundary error check — boundary only
        if pattern.pattern_type == "boundary":
            v_be = _validate_boundary_error_check(pattern, X, y_true, y_pred)
            validations.append(v_be)

        pattern.validation_results = validations

        # Derive sample_support from subgroup_contrast mask
        if y_pred is not None:
            try:
                mask, _ = build_condition_mask(X, pattern.conditions)
                in_count = int(mask.sum())
                out_count = int((~mask).sum())
                total = max(in_count + out_count, 1)
                pattern.sample_support = PatternSampleSupport(
                    in_scope_count=in_count,
                    out_scope_count=out_count,
                    coverage=round(in_count / total, 4),
                    in_scope_fraction=round(in_count / total, 4),
                )
            except ValueError:
                pattern.sample_support = PatternSampleSupport()

        # Determine overall validation_status (worst status wins)
        status_priority = {"fail": 0, "weak": 1, "pass": 2, "not_applicable": 3}
        worst = "pass"
        for v in validations:
            if status_priority.get(v.status, 3) < status_priority.get(worst, 3):
                worst = v.status
        if not validations:
            worst = "unvalidated"
        # "not_applicable" with no other results means nothing was checked
        if worst == "not_applicable" and all(v.status == "not_applicable" for v in validations):
            worst = "unvalidated"
        pattern.validation_status = worst

    passed = sum(1 for p in patterns if p.validation_status == "pass")
    weak = sum(1 for p in patterns if p.validation_status == "weak")
    failed = sum(1 for p in patterns if p.validation_status == "fail")
    logger.info(
        "Validation complete: %d pass, %d weak, %d fail, %d unvalidated",
        passed, weak, failed,
        sum(1 for p in patterns if p.validation_status == "unvalidated"),
    )

    return patterns
