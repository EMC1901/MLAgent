import json
from typing import Dict, Any, List
from app.modules.result_diagnosis.schemas import SystemDiagnosticChecks, EvidenceSummary


def build_llm_diagnostic_context(
    di_input: Dict[str, Any],
    evidence: EvidenceSummary,
    system_checks: SystemDiagnosticChecks,
    optional_contexts: Dict[str, Any],
    diagnosis_profile: str = "standard",
) -> Dict[str, Any]:
    context = {
        "task_summary": _build_task_summary(di_input),
        "metric_evaluation_summary": _build_metric_summary(di_input),
        "model_ranking": _build_model_ranking(di_input),
        "baseline_comparison": di_input.get("baseline_comparison"),
        "fold_stability_summary": di_input.get("stability_summary"),
        "system_diagnostic_checks": {
            "weak_baseline_improvement": system_checks.weak_baseline_improvement,
            "high_fold_variance": system_checks.high_fold_variance,
            "all_models_weak": system_checks.all_models_weak,
            "hpo_budget_limited": system_checks.hpo_budget_limited,
            "small_sample_warning": system_checks.small_sample_warning,
            "feature_count_low": system_checks.feature_count_low,
            "many_features_dropped": system_checks.many_features_dropped,
            "candidate_underperforms_baseline": system_checks.candidate_underperforms_baseline,
            "unstable_best_model": system_checks.unstable_best_model,
            "warnings": system_checks.warnings,
        },
        "evidence_items": {
            "metric_evidence": [e.model_dump() for e in evidence.metric_evidence],
            "baseline_evidence": [e.model_dump() for e in evidence.baseline_evidence],
            "fold_stability_evidence": [e.model_dump() for e in evidence.fold_stability_evidence],
            "dataset_evidence": [e.model_dump() for e in evidence.dataset_evidence],
            "feature_evidence": [e.model_dump() for e in evidence.feature_evidence],
            "pipeline_evidence": [e.model_dump() for e in evidence.pipeline_evidence],
        },
        "evaluation_warnings": di_input.get("evaluation_warnings", []),
        "failed_trials_summary": di_input.get("failed_trials_summary"),
        "known_warnings": system_checks.warnings,
    }

    if diagnosis_profile == "full":
        ds_ctx = optional_contexts.get("dataset_profile") or {}
        fe_ctx = optional_contexts.get("feature_engineering") or {}
        fp_ctx = optional_contexts.get("feature_preprocessing") or {}
        context["dataset_profile"] = ds_ctx.get("profile_json") if isinstance(ds_ctx, dict) else None
        context["feature_engineering_summary"] = fe_ctx.get("feature_json") if isinstance(fe_ctx, dict) else None
        context["feature_preprocessing_summary"] = fp_ctx.get("preprocessing_json") if isinstance(fp_ctx, dict) else None
    elif diagnosis_profile == "standard":
        ds_ctx = optional_contexts.get("dataset_profile") or {}
        fp_ctx = optional_contexts.get("feature_preprocessing") or {}
        if ds_ctx:
            profile = ds_ctx.get("profile_json") or ds_ctx
            context["dataset_profile_summary"] = {
                "n_samples": profile.get("n_samples") or profile.get("row_count"),
                "n_features": profile.get("n_features") or profile.get("n_columns"),
                "target_column": profile.get("target_column") or di_input.get("primary_metric"),
            }
        if fp_ctx:
            fp_json = fp_ctx.get("preprocessing_json") or fp_ctx
            context["feature_summary"] = {
                "n_final_features": fp_json.get("n_final_features"),
                "n_features_dropped": fp_json.get("n_features_dropped"),
            }

    return context


def _build_task_summary(di_input: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "task_id": di_input.get("task_id"),
        "task_type": di_input.get("task_type"),
        "primary_metric": di_input.get("primary_metric"),
        "metric_direction": di_input.get("metric_direction"),
    }


def _build_metric_summary(di_input: Dict[str, Any]) -> Dict[str, Any]:
    ms = di_input.get("metric_summary") or {}
    return {
        "best_metric_value": ms.get("best_metric_value"),
        "worst_metric_value": ms.get("worst_metric_value"),
        "mean_metric_value": ms.get("mean_metric_value"),
        "std_metric_value": ms.get("std_metric_value"),
        "n_trials_contributing": ms.get("n_trials_contributing"),
        "n_models_contributing": ms.get("n_models_contributing"),
    }


def _build_model_ranking(di_input: Dict[str, Any]) -> List[Dict[str, Any]]:
    ranking = di_input.get("model_ranking") or []
    compact = []
    for r in ranking[:10]:
        if isinstance(r, dict):
            compact.append({
                "rank": r.get("rank"),
                "model_id": r.get("model_id"),
                "model_family": r.get("model_family"),
                "primary_metric_value": r.get("primary_metric_value"),
                "improvement_percentage": r.get("improvement_percentage"),
            })
        else:
            compact.append({
                "rank": getattr(r, "rank", None),
                "model_id": getattr(r, "model_id", None),
                "model_family": getattr(r, "model_family", None),
                "primary_metric_value": getattr(r, "primary_metric_value", None),
                "improvement_percentage": getattr(r, "improvement_percentage", None),
            })
    return compact
