from typing import Dict, Any, List
from app.modules.result_diagnosis.schemas import SystemDiagnosticChecks

# Default thresholds
WEAK_IMPROVEMENT_THRESHOLD = 0.05
HIGH_CV_THRESHOLD = 0.15
SMALL_SAMPLE_THRESHOLD = 200
LOW_FEATURE_THRESHOLD = 10
HIGH_DROPPED_FEATURE_RATIO = 0.5
LIMITED_HPO_TRIAL_THRESHOLD = 10
HIGH_FOLD_STD_THRESHOLD = 0.1


def run_system_diagnostic_checks(
    di_input: Dict[str, Any],
    evidence_summary: Any,
    optional_contexts: Dict[str, Any] = None,
) -> SystemDiagnosticChecks:
    checks = SystemDiagnosticChecks()
    warnings: List[str] = []

    baseline = di_input.get("baseline_comparison") or {}
    metric_summary = di_input.get("metric_summary") or {}
    stability = di_input.get("stability_summary") or {}
    model_ranking = di_input.get("model_ranking") or []
    metric_direction = di_input.get("metric_direction", "minimize")

    # Check: candidate underperforms baseline
    if baseline.get("candidate_beats_baseline") is False:
        checks.candidate_underperforms_baseline = True
        warnings.append("Best candidate model does not outperform baseline.")

    # Check: weak baseline improvement
    abs_improvement = baseline.get("absolute_improvement")
    if abs_improvement is not None and baseline.get("candidate_beats_baseline"):
        if abs(abs_improvement) < WEAK_IMPROVEMENT_THRESHOLD:
            checks.weak_baseline_improvement = True
            warnings.append(f"Baseline improvement is weak (absolute={abs_improvement:.4f}).")

    # Check: high fold variance
    mean_cv = stability.get("mean_cv_std")
    if mean_cv is not None and mean_cv > HIGH_CV_THRESHOLD:
        checks.high_fold_variance = True
        warnings.append(f"High cross-validation fold variance detected (mean CV std={mean_cv:.4f}).")

    # Check: unstable best model
    max_cv = stability.get("max_cv_std")
    if max_cv is not None and max_cv > HIGH_FOLD_STD_THRESHOLD:
        checks.unstable_best_model = True
        warnings.append(f"Best model fold standard deviation is high (max={max_cv:.4f}).")

    # Check: all models weak
    if model_ranking and metric_summary:
        best_val = metric_summary.get("best_metric_value")
        worst_val = metric_summary.get("worst_metric_value")
        if best_val is not None and worst_val is not None and best_val != 0:
            improvement_ratio = abs((best_val - worst_val) / best_val)
            if improvement_ratio < 0.01:
                checks.all_models_weak = True
                warnings.append("All models perform similarly with minimal variation.")

    # Check: HPO budget limited
    failed_trials = di_input.get("failed_trials_summary") or {}
    n_trials = failed_trials.get("n_successful_trials", 0)
    if n_trials < LIMITED_HPO_TRIAL_THRESHOLD:
        checks.hpo_budget_limited = True
        warnings.append(f"HPO trial count is limited ({n_trials} successful trials).")

    # Check: small sample
    ds_ctx = optional_contexts.get("dataset_profile") or {}
    if ds_ctx:
        profile = ds_ctx.get("profile_json") or ds_ctx
        n_samples = profile.get("n_samples") or profile.get("row_count")
        if n_samples is not None and n_samples < SMALL_SAMPLE_THRESHOLD:
            checks.small_sample_warning = True
            warnings.append(f"Small sample size detected (n={n_samples}).")

    # Check: feature count low
    fp_ctx = optional_contexts.get("feature_preprocessing") or {}
    if fp_ctx:
        fp_json = fp_ctx.get("preprocessing_json") or fp_ctx
        n_final = fp_json.get("n_final_features")
        if n_final is not None:
            if n_final < LOW_FEATURE_THRESHOLD:
                checks.feature_count_low = True
                warnings.append(f"Low final feature count (n={n_final}).")
            n_initial = fp_json.get("n_initial_features")
            n_dropped = fp_json.get("n_features_dropped")
            if n_initial and n_dropped and n_initial > 0:
                dropped_ratio = n_dropped / n_initial
                if dropped_ratio > HIGH_DROPPED_FEATURE_RATIO:
                    checks.many_features_dropped = True
                    warnings.append(f"High feature drop ratio ({dropped_ratio:.1%}).")

    checks.warnings = warnings
    return checks
