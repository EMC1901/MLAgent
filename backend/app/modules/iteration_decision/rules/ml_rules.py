import logging
from typing import Dict, Any, List
from app.modules.iteration_decision.schemas import SystemChecks

logger = logging.getLogger(__name__)

WEAK_IMPROVEMENT_THRESHOLD = 0.05
HIGH_CV_THRESHOLD = 0.15
HIGH_FOLD_STD_THRESHOLD = 0.10
LIMITED_HPO_TRIAL_THRESHOLD = 10


def run_ml_rules(metrics: Dict[str, Any], evidence_ml: List) -> SystemChecks:
    """Run rule-based ML checks. Returns a partial SystemChecks with ML fields filled."""
    checks = SystemChecks()
    di = metrics.get("result_diagnosis_input_json") or {}
    baseline = di.get("baseline_comparison") or {}
    metric_summary = di.get("metric_summary") or {}
    stability = di.get("stability_summary") or {}
    ranking = di.get("model_ranking") or []

    # Candidate underperforms baseline
    if baseline.get("candidate_beats_baseline") is False:
        checks.candidate_underperforms_baseline = True
        checks.warnings.append("Best candidate model does not outperform baseline.")

    # Weak baseline improvement
    abs_imp = baseline.get("absolute_improvement")
    if abs_imp is not None and baseline.get("candidate_beats_baseline"):
        if abs(abs_imp) < WEAK_IMPROVEMENT_THRESHOLD:
            checks.weak_baseline_improvement = True
            checks.warnings.append(f"Weak baseline improvement (abs={abs_imp:.4f}).")

    # High fold variance
    mean_cv = stability.get("mean_cv_std")
    if mean_cv is not None and mean_cv > HIGH_CV_THRESHOLD:
        checks.high_fold_variance = True
        checks.warnings.append(f"High CV fold variance (mean std={mean_cv:.4f}).")

    # Unstable best model
    max_cv = stability.get("max_cv_std")
    if max_cv is not None and max_cv > HIGH_FOLD_STD_THRESHOLD:
        checks.unstable_best_model = True
        checks.warnings.append(f"Best model fold std is high (max={max_cv:.4f}).")

    # All models weak
    if ranking and metric_summary:
        best_val = metric_summary.get("best_metric_value")
        worst_val = metric_summary.get("worst_metric_value")
        if best_val is not None and worst_val is not None and best_val != 0:
            ratio = abs((best_val - worst_val) / best_val)
            if ratio < 0.01:
                checks.all_models_weak = True
                checks.warnings.append("All models perform similarly — no meaningful differentiation.")

    # HPO budget limited
    failed = di.get("failed_trials_summary") or {}
    n_success = failed.get("n_successful_trials", 0)
    if n_success < LIMITED_HPO_TRIAL_THRESHOLD:
        checks.hpo_budget_limited = True
        checks.warnings.append(f"Limited HPO budget ({n_success} successful trials).")

    triggered = [k for k, v in checks.model_dump().items()
                 if v is True and k not in ("warnings", "additional_checks")]
    logger.info("ML rules — %d triggered (%s)",
                 len(triggered), ", ".join(triggered) if triggered else "none")
    return checks
