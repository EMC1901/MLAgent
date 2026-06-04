"""Build a compact (~40K chars) decision context for the LLM iteration decision.

Replaces the previous approach of dumping entire upstream JSONB blobs
(which produced ~400K-character prompts that exceeded API limits).
"""

import logging
import sys
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

_MAX_STR_LEN = 200
_MAX_FAILED_TRIALS = 5
_MAX_TOP_TRIALS = 5
_MAX_HYPERPARAMS = 8
_MAX_DROPPED_FEATURES = 10
_MAX_FEATURIZERS = 10
_MAX_FEATURE_GROUPS = 10
_MAX_PREPROCESSING_STEPS = 10
_MAX_WARNINGS = 5


def _diag(msg, *args):
    formatted = msg % args if args else msg
    print(f"DIAG     [id-ctx] {formatted}", file=sys.stderr, flush=True)


def build_decision_context(
    upstream: Dict[str, Any],
    metrics: Dict[str, Any],
    system_checks: Any,
    history: Dict[str, Any],
    evidence_ml: list,
    evidence_materials: list,
    evidence_workflow: list,
    evidence_history: list,
    task_id: str,
    iteration_index: int,
) -> Dict[str, Any]:
    """Build a compact context dict for the LLM."""
    _diag("build_decision_context: task_id=%s iteration=%d", task_id, iteration_index)

    ctx: Dict[str, Any] = {}

    # ① Task Overview
    _diag("  [1/8] task_overview")
    ctx["task_overview"] = _build_task_overview(upstream, metrics)

    # ② Feature Engineering Summary
    _diag("  [2/8] feature_engineering")
    ctx["feature_engineering"] = _build_feature_engineering(upstream)

    # ③ Feature Preprocessing Summary
    _diag("  [3/8] feature_preprocessing")
    ctx["feature_preprocessing"] = _build_feature_preprocessing(upstream)

    # ④ Best Model
    _diag("  [4/8] best_model")
    ctx["best_model"] = _build_best_model(metrics, upstream)

    # ⑤ Trial Summary
    _diag("  [5/8] trial_summary")
    ctx["trial_summary"] = _build_trial_summary(metrics, upstream)

    # ⑥ Model Comparison
    _diag("  [6/8] model_comparison")
    ctx["model_comparison"] = _build_model_comparison(metrics)

    # ⑦ Key Warnings
    _diag("  [7/8] key_warnings")
    ctx["key_warnings"] = _build_key_warnings(system_checks)

    # ⑧ Next Actions & History
    _diag("  [8/8] next_actions_and_history")
    ctx["next_actions_and_history"] = _build_next_actions(history, system_checks, iteration_index)

    # Size check
    import json
    total = len(json.dumps(ctx, default=str, ensure_ascii=False))
    _diag("build_decision_context DONE: %d chars (8 sections)", total)
    if total > 80000:
        logger.warning("Decision context is %d chars — may still be too large", total)

    return ctx


# ── ① Task Overview ─────────────────────────────────────────────────

def _build_task_overview(upstream: dict, metrics: dict) -> dict:
    ti = upstream.get("task_interpretation", {})
    interp = ti.get("interpretation_json") or {}
    ds = upstream.get("dataset_profile", {})
    fmp = upstream.get("feature_preprocessing", {})

    return {
        "task_type": interp.get("interpreted_task_type") or "unknown",
        "input_modality": interp.get("interpreted_input_modality") or "unknown",
        "target_column": _safe_str(interp.get("target_column")),
        "primary_metric": _safe_str(metrics.get("primary_metric")),
        "metric_direction": _safe_str(metrics.get("metric_direction", "minimize")),
        "n_samples": _safe_int(ds.get("n_samples")),
        "n_final_features": _safe_int(fmp.get("n_final_features")),
    }


# ── ② Feature Engineering ───────────────────────────────────────────

def _build_feature_engineering(upstream: dict) -> dict:
    fe = upstream.get("feature_engineering", {})
    feature_json = fe.get("feature_json") or {}
    groups_json = fe.get("feature_groups_json") or {}
    quality_json = fe.get("quality_profile_json") or {}

    # Featurizers used
    featurizers_raw = feature_json.get("featurizers") or feature_json.get("featurizer_summary") or []
    featurizers = _summarize_list(featurizers_raw, _MAX_FEATURIZERS)

    # Feature groups
    groups_raw = groups_json if isinstance(groups_json, list) else groups_json.get("groups", [])
    groups = []
    for g in _summarize_list(groups_raw, _MAX_FEATURE_GROUPS):
        groups.append({
            "name": _safe_str(g.get("name") or g.get("group_name")),
            "n_features": _safe_int(g.get("n_features") or g.get("count")),
            "status": _safe_str(g.get("status", "unknown")),
        })

    # Quality warnings
    quality_warnings = []
    qw_raw = quality_json.get("warnings") or quality_json.get("issues") or []
    for w in _summarize_list(qw_raw, _MAX_WARNINGS):
        if isinstance(w, dict) and w.get("is_warning", True):
            quality_warnings.append(_safe_str(w.get("message") or w.get("description") or str(w)))

    return {
        "n_features_generated": _safe_int(fe.get("n_features")),
        "input_modality": _safe_str(fe.get("input_modality")),
        "feature_type": _safe_str(fe.get("feature_type")),
        "featurizers_used": featurizers,
        "feature_groups": groups,
        "quality_warnings": quality_warnings,
    }


# ── ③ Feature Preprocessing ─────────────────────────────────────────

def _build_feature_preprocessing(upstream: dict) -> dict:
    fmp = upstream.get("feature_preprocessing", {})
    exec_json = fmp.get("execution_report_json") or {}
    removed_json = fmp.get("removed_features_json") or {}
    explain_json = fmp.get("explainability_report_json") or {}

    # Preprocessing steps from execution report
    steps_raw = exec_json.get("steps") or exec_json.get("operations") or []
    steps = []
    for s in _summarize_list(steps_raw, _MAX_PREPROCESSING_STEPS):
        steps.append({
            "name": _safe_str(s.get("name") or s.get("operation") or s.get("capability_id")),
            "status": _safe_str(s.get("status", "unknown")),
        })

    # Dropped features
    dropped_raw = removed_json if isinstance(removed_json, list) else removed_json.get("features", [])
    dropped = []
    for d in _summarize_list(dropped_raw, _MAX_DROPPED_FEATURES):
        dropped.append({
            "feature": _safe_str(d.get("feature_name") or d.get("name")),
            "reason": _safe_str(d.get("reason") or d.get("drop_reason")),
            "missing_rate": _safe_float(d.get("missing_rate")),
        })

    # Warnings
    fp_warnings = []
    ew_raw = explain_json.get("warnings") or explain_json.get("issues") or []
    for w in _summarize_list(ew_raw, _MAX_WARNINGS):
        fp_warnings.append(_safe_str(w.get("message") or w.get("description") or str(w)))

    return {
        "n_raw_features": _safe_int(fmp.get("n_raw_features")),
        "n_valid_features": _safe_int(fmp.get("n_valid_features")),
        "n_final_features": _safe_int(fmp.get("n_final_features")),
        "n_dropped_features": _safe_int(fmp.get("n_dropped_features")),
        "preprocessing_steps": steps,
        "dropped_features_top": dropped,
        "warnings": fp_warnings,
    }


# ── ④ Best Model ────────────────────────────────────────────────────

def _build_best_model(metrics: dict, upstream: dict) -> dict:
    di = metrics.get("result_diagnosis_input_json") or {}
    best_trial = di.get("best_trial") or {}
    best_model = di.get("best_model") or {}
    ranking = di.get("model_ranking") or []

    # Find the best entry from ranking
    best_entry = None
    for r in ranking:
        if isinstance(r, dict) and r.get("is_best_model"):
            best_entry = r
            break
    if best_entry is None and ranking:
        best_entry = ranking[0]

    result: dict = {
        "model_id": _safe_str(best_entry.get("model_id") if best_entry else metrics.get("best_model_id")),
        "trial_id": _safe_str(
            best_entry.get("best_trial_id") if best_entry else metrics.get("best_trial_id")
        ),
        "pipeline_spec_id": _safe_str(
            best_entry.get("pipeline_spec_id") if best_entry else metrics.get("best_pipeline_spec_id")
        ),
        "primary_metric_value": _safe_float(
            best_entry.get("primary_metric_value") if best_entry else metrics.get("best_primary_metric_value")
        ),
    }

    # Metrics from diagnosis input
    if best_trial:
        result["trial_metrics"] = {
            "primary_metric_mean": _safe_float(best_trial.get("primary_metric_mean")),
            "primary_metric_std": _safe_float(best_trial.get("primary_metric_std")),
        }

    # Hyperparameters from PipelineExecution
    pe = upstream.get("pipeline_execution", {})
    exec_json = pe.get("execution_json") or {}
    trial_results = exec_json.get("trial_results") or []
    best_trial_id = result.get("trial_id")
    if best_trial_id and trial_results:
        for tr in trial_results:
            if isinstance(tr, dict) and tr.get("trial_id") == best_trial_id:
                params = tr.get("params") or {}
                top_params = {}
                for i, (k, v) in enumerate(params.items()):
                    if i >= _MAX_HYPERPARAMS:
                        break
                    s = str(v)
                    top_params[k] = s[:_MAX_STR_LEN]
                result["top_hyperparameters"] = top_params
                break

    return result


# ── ⑤ Trial Summary ─────────────────────────────────────────────────

def _build_trial_summary(metrics: dict, upstream: dict) -> dict:
    di = metrics.get("result_diagnosis_input_json") or {}
    ranking = di.get("model_ranking") or []
    failed_summary = di.get("failed_trials_summary") or {}

    # Top trials
    top_trials = []
    for r in _summarize_list(ranking, _MAX_TOP_TRIALS):
        top_trials.append({
            "model_id": _safe_str(r.get("model_id")),
            "trial_id": _safe_str(r.get("best_trial_id") or r.get("trial_id")),
            "metric_value": _safe_float(r.get("primary_metric_value")),
            "rank": _safe_int(r.get("rank")),
        })

    # Failed trials
    failed_list = failed_summary.get("failed_trials") or failed_summary.get("details") or []
    failed_trials = []
    for f in _summarize_list(failed_list, _MAX_FAILED_TRIALS):
        failed_trials.append({
            "trial_id": _safe_str(f.get("trial_id")),
            "model_id": _safe_str(f.get("model_id")),
            "error": _truncate(_safe_str(f.get("error_message") or f.get("error")), _MAX_STR_LEN),
        })

    # Totals from PipelineExecution
    pe = upstream.get("pipeline_execution", {})
    n_total = _safe_int(pe.get("n_trials_completed", 0)) + _safe_int(pe.get("n_trials_failed", 0))
    n_succeeded = _safe_int(pe.get("n_trials_completed", 0))
    n_failed = _safe_int(pe.get("n_trials_failed", 0))

    return {
        "n_total": n_total if n_total > 0 else len(ranking) + len(failed_trials),
        "n_succeeded": n_succeeded if n_succeeded > 0 else len(ranking),
        "n_failed": n_failed if n_failed > 0 else len(failed_trials),
        "top_trials": top_trials,
        "failed_trials": failed_trials,
    }


# ── ⑥ Model Comparison ──────────────────────────────────────────────

def _build_model_comparison(metrics: dict) -> dict:
    di = metrics.get("result_diagnosis_input_json") or {}
    ranking = di.get("model_ranking") or []
    baseline_comparison = di.get("baseline_comparison") or {}

    models = []
    for r in ranking:
        if not isinstance(r, dict):
            continue
        entry = {
            "model_id": _safe_str(r.get("model_id")),
            "best_metric": _safe_float(r.get("primary_metric_value")),
            "rank": _safe_int(r.get("rank")),
        }
        if r.get("is_best_model"):
            entry["marker"] = "[best]"
        if r.get("pipeline_role") == "baseline":
            entry["marker"] = "[baseline]"
        models.append(entry)

    return {
        "models": models,
        "baseline": {
            "model_id": _safe_str(baseline_comparison.get("baseline_model_id")),
            "best_metric": _safe_float(baseline_comparison.get("baseline_metric_value")),
            "improvement_pct": _safe_float(baseline_comparison.get("improvement_percentage")),
        } if baseline_comparison else None,
    }


# ── ⑦ Key Warnings ──────────────────────────────────────────────────

def _build_key_warnings(system_checks: Any) -> dict:
    sc = system_checks.model_dump() if hasattr(system_checks, "model_dump") else {}
    warnings_list = sc.get("warnings") or []

    critical = []
    warnings = []
    # Extract boolean flags that are True (excluding meta fields)
    for k, v in sc.items():
        if v is True and k not in ("warnings", "additional_checks"):
            critical.append(k)
        elif v is True:
            pass  # already in the list above

    return {
        "critical_flags": critical,
        "warning_messages": _summarize_list(
            [w for w in warnings_list if w], _MAX_WARNINGS
        ),
    }


# ── ⑧ Next Actions & History ────────────────────────────────────────

def _build_next_actions(history: dict, system_checks: Any, iteration_index: int) -> dict:
    sc = system_checks.model_dump() if hasattr(system_checks, "model_dump") else {}

    candidate_actions = []
    if sc.get("max_iterations_reached"):
        candidate_actions.append({"action": "STOP", "reason": "Max iterations reached"})
    if sc.get("no_improvement_trend"):
        candidate_actions.append({"action": "STOP", "reason": "Metric not improving"})
    if sc.get("many_trials_failed"):
        candidate_actions.append({"action": "ITERATE:retry_failed", "reason": "Many trials failed, consider retry with fixes"})
    if sc.get("metric_stagnating"):
        candidate_actions.append({"action": "ITERATE:refine_hpo", "reason": "HPO may need more trials or adjusted search space"})
    if sc.get("feature_count_low") or sc.get("many_features_dropped"):
        candidate_actions.append({"action": "ITERATE:add_features", "reason": "Feature count is low or many were dropped"})
    if sc.get("all_models_underperform"):
        candidate_actions.append({"action": "ITERATE:switch_models", "reason": "All models underperforming, switch model families"})
    if sc.get("feature_materials_relevance_low"):
        candidate_actions.append({"action": "ITERATE:add_features", "reason": "Features have low materials relevance"})

    if not candidate_actions:
        candidate_actions.append({"action": "STOP", "reason": "No issues detected — results are satisfactory"})

    return {
        "iteration_index": iteration_index,
        "best_so_far": _safe_float(history.get("best_metric_so_far")),
        "metric_trend": _safe_str(history.get("metric_trend", "unknown")),
        "n_iterations_completed": _safe_int(history.get("n_iterations_completed")),
        "tried_models": history.get("tried_model_families") or [],
        "candidate_actions": candidate_actions,
    }


# ── helpers ──────────────────────────────────────────────────────────

def _safe_str(val) -> str:
    return str(val) if val is not None else ""


def _safe_int(val) -> Optional[int]:
    try:
        return int(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def _safe_float(val) -> Optional[float]:
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def _first_non_none(*vals):
    for v in vals:
        if v is not None:
            return v
    return None


def _truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    return s[:max_len - 3] + "..."


def _summarize_list(lst: list, max_items: int) -> list:
    if not isinstance(lst, list):
        return []
    if len(lst) <= max_items:
        return lst
    return lst[:max_items]
