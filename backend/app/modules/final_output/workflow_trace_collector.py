import logging
import sys
import traceback
from typing import Optional, Dict, Any
from sqlmodel import Session

from app.modules.final_output.schemas import WorkflowTraceSummary

logger = logging.getLogger(__name__)


def _diag(msg, *args):
    formatted = msg % args if args else msg
    print(f"DIAG     [fo-trace] {formatted}", file=sys.stderr, flush=True)


_TOPIC_ORDER = [
    "task_specification",
    "dataset_profile",
    "workflow_plan",
    "model_ready_feature_summary",
    "candidate_model_plan",
    "hpo_plan",
    "pipeline_specs",
    "training_evaluation_results",
    "interpretability_analysis",
    "final_output_package",
]


def collect_workflow_trace(
    session: Session,
    task_id: str,
    interpretability_analysis_id: Optional[str] = None,
) -> WorkflowTraceSummary:
    _diag("=== collect_workflow_trace START for task_id=%s ===", task_id)

    trace = WorkflowTraceSummary(
        interpretability_analysis_id=interpretability_analysis_id,
        iteration_count=0,
        workflow_trace_artifacts={},
    )

    summaries: Dict[str, Any] = {}

    # 1 — Task Specification (how the system understood the task)
    _diag("[1/9] Collecting task_specification ...")
    _collect_task_spec(session, task_id, summaries)
    _diag("[1/9] task_specification: has_data=%s keys=%s",
          bool(summaries.get("task_specification", {}).get("interpretation_id")),
          list(summaries.get("task_specification", {}).keys()))

    # 2 — Dataset Profile
    _diag("[2/9] Collecting dataset_profile ...")
    _collect_dataset_profile(session, task_id, summaries)
    _diag("[2/9] dataset_profile: has_data=%s",
          bool(summaries.get("dataset_profile", {}).get("dataset_profile_id")))

    # 3 — Workflow Plan
    _diag("[3/9] Collecting workflow_plan ...")
    _collect_workflow_plan(session, task_id, summaries)
    _diag("[3/9] workflow_plan: has_data=%s",
          bool(summaries.get("workflow_plan", {}).get("workflow_plan_id")))

    # 4 — Model-Ready Feature Summary
    _diag("[4/9] Collecting model_ready_feature_summary ...")
    _collect_feature_summary(session, task_id, summaries)
    _diag("[4/9] model_ready_feature_summary: has_data=%s n_final_features=%s",
          bool(summaries.get("model_ready_feature_summary", {}).get("feature_preprocessing_id")),
          summaries.get("model_ready_feature_summary", {}).get("n_final_features"))

    # 5 — Candidate Model Plan
    _diag("[5/9] Collecting candidate_model_plan ...")
    _collect_candidate_model_plan(session, task_id, summaries)
    _diag("[5/9] candidate_model_plan: has_data=%s n_candidate=%s",
          bool(summaries.get("candidate_model_plan", {}).get("model_search_context_id")),
          summaries.get("candidate_model_plan", {}).get("n_candidate_models"))

    # 6 — HPO Plan
    _diag("[6/9] Collecting hpo_plan ...")
    _collect_hpo_plan(session, task_id, summaries)
    _diag("[6/9] hpo_plan: has_data=%s hpo_enabled=%s",
          bool(summaries.get("hpo_plan", {}).get("model_search_context_id")),
          summaries.get("hpo_plan", {}).get("hpo_enabled"))

    # 7 — Pipeline Specs
    _diag("[7/9] Collecting pipeline_specs ...")
    _collect_pipeline_specs(session, task_id, summaries)
    _diag("[7/9] pipeline_specs: has_data=%s n_specs=%s",
          bool(summaries.get("pipeline_specs", {}).get("pipeline_generation_id")),
          summaries.get("pipeline_specs", {}).get("n_pipeline_specs"))

    # 8 — Training / Evaluation Results
    _diag("[8/10] Collecting training_evaluation_results ...")
    _collect_training_eval_results(session, task_id, summaries)
    _diag("[8/10] training_evaluation_results: has_data=%s best_model=%s",
          bool(summaries.get("training_evaluation_results", {}).get("metric_evaluation_id")),
          summaries.get("training_evaluation_results", {}).get("best_model_id"))

    # 9 — Interpretability Analysis
    _diag("[9/10] Collecting interpretability_analysis ...")
    _collect_interpretability_analysis(session, task_id, summaries)
    _diag("[9/10] interpretability_analysis: has_data=%s",
          bool(summaries.get("interpretability_analysis", {}).get("interpretability_analysis_id")))

    # 10 — Final Output Package (placeholder)
    _diag("[10/10] Setting final_output_package placeholder ...")
    summaries["final_output_package"] = {
        "status": "pending",
        "note": "Populated after all report files are written.",
    }

    trace.workflow_trace_artifacts = summaries
    _collect_iteration_info(session, trace, task_id)

    # Summary of what was collected
    populated = [k for k in _TOPIC_ORDER if _topic_has_data(summaries.get(k))]
    _diag("=== collect_workflow_trace DONE: %d/%d topics populated: %s ===",
          len(populated), len(_TOPIC_ORDER), populated)
    logger.info("Collected workflow trace for task %s: %d/%d topics populated",
                task_id, len(populated), len(_TOPIC_ORDER))
    return trace


def _to_repo_path(module_path: str) -> str:
    """Replace only the trailing '.model' with '.repository'.

    Using ``str.replace`` is unsafe when 'model' also appears earlier in the
    dotted path (e.g. ``app.modules.model_search_context.model`` would become
    ``app.repository_search_context.repository``).
    """
    return module_path.rsplit(".model", 1)[0] + ".repository"


def _topic_has_data(topic: Optional[dict]) -> bool:
    """Check if a topic dict has any meaningful data beyond placeholders."""
    if not topic:
        return False
    if topic.get("status") == "pending" and topic.get("note"):
        return False  # placeholder
    # Check for at least one non-None, non-empty value
    for k, v in topic.items():
        if v is not None and v != "" and v != [] and v != {}:
            return True
    return False


# ── helpers ────────────────────────────────────────────────────────────

def _safe_collect(session: Session, module_path: str, model_name: str,
                  repo_attr: str, task_id: str) -> Optional[Any]:
    """Import a module's model + repository, fetch the latest record for
    *task_id*, and return the ORM instance (or None)."""
    _diag("  _safe_collect: module=%s repo=%s task_id=%s", module_path, repo_attr, task_id)
    try:
        import importlib
        mod = importlib.import_module(module_path)
        model_cls = getattr(mod, model_name)
        repo_path = _to_repo_path(module_path)
        _diag("  importing repo from: %s", repo_path)
        repo_mod = importlib.import_module(repo_path)
        repo = getattr(repo_mod, repo_attr)()
        _diag("  calling repo.get_latest_by_task_id(session, %s) ...", task_id)
        record = repo.get_latest_by_task_id(session, task_id)
        if record:
            _diag("  -> FOUND record id=%s status=%s", getattr(record, "id", "?"), getattr(record, "status", "?"))
        else:
            _diag("  -> NOT FOUND (no record for this task_id)")
        return record
    except Exception as e:
        _diag("  -> FAILED: %s: %s", type(e).__name__, str(e))
        _diag("  traceback: %s", traceback.format_exc().replace("\n", "\n    "))
        logger.warning("Failed to collect from %s: %s", module_path, str(e))
        return None


def _extract_json(record, field: str) -> Optional[dict]:
    if record is None:
        return None
    val = getattr(record, field, None)
    if isinstance(val, dict):
        return val
    if val is not None:
        _diag("  _extract_json: field=%s is type=%s (not dict), returning None", field, type(val).__name__)
    return None


def _extract_scalar(record, field: str, default=None):
    if record is None:
        return default
    return getattr(record, field, default)


def _aggregate_fold_metrics(fold_results: list) -> dict:
    """Compute mean and std for each metric across folds.

    Derives RMSE from MSE when RMSE is not present in fold raw_metric_values.
    """
    import math
    if not fold_results:
        return {}
    metrics_collect: Dict[str, list] = {}
    for fr in fold_results:
        if not isinstance(fr, dict):
            continue
        raw = fr.get("raw_metric_values") or {}
        for k, v in raw.items():
            if isinstance(v, (int, float)):
                metrics_collect.setdefault(k, []).append(v)
    result: Dict[str, Any] = {}
    for k, values in metrics_collect.items():
        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        std = math.sqrt(variance)
        result[k] = {"mean": round(mean, 6), "std": round(std, 6)}
        result[f"{k}_mean"] = round(mean, 6)
        result[f"{k}_std"] = round(std, 6)
    # Derive RMSE from MSE if RMSE not present
    if "mse" in metrics_collect and "rmse" not in metrics_collect:
        mse_values = metrics_collect["mse"]
        rmse_values = [math.sqrt(v) for v in mse_values]
        n = len(rmse_values)
        mean = sum(rmse_values) / n
        variance = sum((x - mean) ** 2 for x in rmse_values) / n
        std = math.sqrt(variance)
        result["rmse"] = {"mean": round(mean, 6), "std": round(std, 6)}
        result["rmse_mean"] = round(mean, 6)
        result["rmse_std"] = round(std, 6)
    return result


# ── per-topic collectors ───────────────────────────────────────────────

def _collect_task_spec(session: Session, task_id: str, summaries: dict):
    rec = _safe_collect(session,
                        "app.modules.task_interpretation.model", "TaskInterpretation",
                        "TaskInterpretationRepository", task_id)
    interp = _extract_json(rec, "interpretation_json") or {}
    summaries["task_specification"] = {
        "task_id": task_id,
        "interpretation_id": _extract_scalar(rec, "id"),
        "status": _extract_scalar(rec, "status"),
        "interpreted_task_type": _extract_scalar(rec, "interpreted_task_type"),
        "interpreted_input_modality": _extract_scalar(rec, "interpreted_input_modality"),
        "interpreted_material_domain": _extract_scalar(rec, "interpreted_material_domain"),
        "confidence_score": _extract_scalar(rec, "confidence_score"),
        "interpretation_detail": interp,
    }


def _collect_dataset_profile(session: Session, task_id: str, summaries: dict):
    rec = _safe_collect(session,
                        "app.modules.dataset_profile.model", "DatasetProfile",
                        "DatasetProfileRepository", task_id)
    summaries["dataset_profile"] = {
        "dataset_profile_id": _extract_scalar(rec, "id"),
        "status": _extract_scalar(rec, "status"),
        "source_type": _extract_scalar(rec, "source_type"),
        "n_samples": _extract_scalar(rec, "n_samples"),
        "n_columns": _extract_scalar(rec, "n_columns"),
        "target_column": _extract_scalar(rec, "target_column"),
        "quality_level": _extract_scalar(rec, "quality_level"),
        "is_usable_for_ml": _extract_scalar(rec, "is_usable_for_ml"),
        "profile_detail": _extract_json(rec, "profile_json"),
    }


def _collect_workflow_plan(session: Session, task_id: str, summaries: dict):
    rec = _safe_collect(session,
                        "app.modules.workflow_planning.model", "WorkflowPlan",
                        "WorkflowPlanRepository", task_id)
    summaries["workflow_plan"] = {
        "workflow_plan_id": _extract_scalar(rec, "id"),
        "status": _extract_scalar(rec, "status"),
        "task_type": _extract_scalar(rec, "task_type"),
        "primary_metric": _extract_scalar(rec, "primary_metric"),
        "feature_type": _extract_scalar(rec, "feature_type"),
        "validation_strategy": _extract_scalar(rec, "validation_strategy"),
        "hpo_enabled": _extract_scalar(rec, "hpo_enabled"),
        "interpretability_enabled": _extract_scalar(rec, "interpretability_enabled"),
        "feature_strategy": _extract_json(rec, "feature_strategy_json"),
        "model_strategy": _extract_json(rec, "model_strategy_json"),
        "preprocessing_intent": _extract_json(rec, "preprocessing_intent_json"),
        "workflow_rationale": _extract_json(rec, "workflow_rationale_json"),
        "plan_detail": _extract_json(rec, "plan_json"),
    }


def _collect_feature_summary(session: Session, task_id: str, summaries: dict):
    rec = _safe_collect(session,
                        "app.modules.feature_preprocessing.model", "FeaturePreprocessing",
                        "FeaturePreprocessingRepository", task_id)
    summaries["model_ready_feature_summary"] = {
        "feature_preprocessing_id": _extract_scalar(rec, "id"),
        "status": _extract_scalar(rec, "status"),
        "n_raw_features": _extract_scalar(rec, "n_raw_features"),
        "n_valid_features": _extract_scalar(rec, "n_valid_features"),
        "n_final_features": _extract_scalar(rec, "n_final_features"),
        "n_dropped_features": _extract_scalar(rec, "n_dropped_features"),
        "is_ready_for_model_search": _extract_scalar(rec, "is_ready_for_model_search"),
        "removed_features": _extract_json(rec, "removed_features_json"),
        "feature_lineage": _extract_json(rec, "feature_lineage_json"),
        "preprocessing_plan": _extract_json(rec, "preprocessing_plan_json"),
        "execution_report": _extract_json(rec, "execution_report_json"),
    }


def _collect_candidate_model_plan(session: Session, task_id: str, summaries: dict):
    rec = _safe_collect(session,
                        "app.modules.model_search_context.model", "ModelSearchContext",
                        "ModelSearchContextRepository", task_id)
    context = _extract_json(rec, "context_json") or {}
    summaries["candidate_model_plan"] = {
        "model_search_context_id": _extract_scalar(rec, "id"),
        "status": _extract_scalar(rec, "status"),
        "n_candidate_models": _extract_scalar(rec, "n_candidate_models"),
        "ready_for_pipeline_generation": _extract_scalar(rec, "ready_for_pipeline_generation"),
        "model_strategy_adjusted": _extract_scalar(rec, "model_strategy_adjusted"),
        "candidate_models": context.get("candidate_models", []),
        "excluded_models": context.get("excluded_models", []),
        "context_detail": context,
    }


def _collect_hpo_plan(session: Session, task_id: str, summaries: dict):
    rec = _safe_collect(session,
                        "app.modules.model_search_context.model", "ModelSearchContext",
                        "ModelSearchContextRepository", task_id)
    context = _extract_json(rec, "context_json") or {}
    summaries["hpo_plan"] = {
        "model_search_context_id": _extract_scalar(rec, "id"),
        "hpo_enabled": _extract_scalar(rec, "hpo_enabled"),
        "hpo_method": _extract_scalar(rec, "hpo_method"),
        "max_total_trials": _extract_scalar(rec, "max_total_trials"),
        "hpo_strategy_adjusted": _extract_scalar(rec, "hpo_strategy_adjusted"),
        "search_space": context.get("search_space", {}),
        "hpo_config_detail": context.get("hpo_config", {}),
    }


def _collect_pipeline_specs(session: Session, task_id: str, summaries: dict):
    rec = _safe_collect(session,
                        "app.modules.pipeline_generation.model", "PipelineGeneration",
                        "PipelineGenerationRepository", task_id)
    pipeline = _extract_json(rec, "pipeline_json") or {}
    summaries["pipeline_specs"] = {
        "pipeline_generation_id": _extract_scalar(rec, "id"),
        "status": _extract_scalar(rec, "status"),
        "n_pipeline_specs": _extract_scalar(rec, "n_pipeline_specs"),
        "n_baseline_specs": _extract_scalar(rec, "n_baseline_specs"),
        "n_hpo_specs": _extract_scalar(rec, "n_hpo_specs"),
        "ready_for_execution": _extract_scalar(rec, "ready_for_execution"),
        "pipeline_specs_detail": pipeline,
    }


def _collect_training_eval_results(session: Session, task_id: str, summaries: dict):
    """Performance report — best model only, from MetricEvaluation + PipelineExecution."""
    me_rec = _safe_collect(session,
                           "app.modules.metric_evaluation.model", "MetricEvaluation",
                           "MetricEvaluationRepository", task_id)
    pe_rec = _safe_collect(session,
                           "app.modules.pipeline_execution.model", "PipelineExecution",
                           "PipelineExecutionRepository", task_id)

    ranking = _extract_json(me_rec, "model_ranking_json") or []
    best_model = None
    if isinstance(ranking, list):
        for item in ranking:
            if isinstance(item, dict) and item.get("is_best_model"):
                best_model = dict(item)
                break
        if best_model is None and ranking:
            best_model = dict(ranking[0])

    if best_model is None:
        best_model = {
            "model_id": _extract_scalar(me_rec, "best_model_id"),
            "trial_id": _extract_scalar(me_rec, "best_trial_id"),
            "primary_metric_value": _extract_scalar(me_rec, "best_primary_metric_value"),
        }

    # Extract best trial's hyperparameters AND per-fold metrics from PipelineExecution
    best_trial_id = best_model.get("best_trial_id") or best_model.get("trial_id")
    trial_params = None
    if best_trial_id and pe_rec:
        exec_json = _extract_json(pe_rec, "execution_json") or {}
        trial_results = exec_json.get("trial_results") or []
        if isinstance(trial_results, list):
            for tr in trial_results:
                if isinstance(tr, dict) and tr.get("trial_id") == best_trial_id:
                    trial_params = tr.get("params")
                    fold_results = tr.get("fold_results") or []
                    if isinstance(fold_results, list) and fold_results:
                        best_model["metrics"] = _aggregate_fold_metrics(fold_results)
                    break

    if trial_params:
        best_model["hyperparameters"] = trial_params

    summaries["training_evaluation_results"] = {
        "metric_evaluation_id": _extract_scalar(me_rec, "id"),
        "status": _extract_scalar(me_rec, "status"),
        "primary_metric": _extract_scalar(me_rec, "primary_metric"),
        "metric_direction": _extract_scalar(me_rec, "metric_direction"),
        "n_trials_evaluated": _extract_scalar(me_rec, "n_trials_evaluated"),
        "n_models_evaluated": _extract_scalar(me_rec, "n_models_evaluated"),
        "best_model": best_model,
    }


def _collect_interpretability_analysis(session: Session, task_id: str, summaries: dict):
    """Feature importance, SHAP, material insights — from InterpretabilityAnalysis."""
    rec = _safe_collect(session,
                        "app.modules.interpretability_analysis.model", "InterpretabilityAnalysis",
                        "InterpretabilityAnalysisRepository", task_id)
    summaries["interpretability_analysis"] = {
        "interpretability_analysis_id": _extract_scalar(rec, "id"),
        "status": _extract_scalar(rec, "status"),
        "final_model_id": _extract_scalar(rec, "final_model_id"),
        "final_model_family": _extract_scalar(rec, "final_model_family"),
        "methods_used": _extract_json(rec, "methods_used_json"),
        "global_feature_importance": _extract_json(rec, "global_feature_importance_json"),
        "shap_summary": _extract_json(rec, "shap_summary_json"),
        "permutation_importance": _extract_json(rec, "permutation_importance_json"),
        "partial_dependence": _extract_json(rec, "partial_dependence_json"),
        "cross_method_consensus": _extract_json(rec, "cross_method_consensus_json"),
        "material_insight_summary": _extract_json(rec, "material_insight_summary_json"),
        "physics_constraint_check": _extract_json(rec, "physics_constraint_check_json"),
        "llm_summary": _extract_json(rec, "llm_summary_json"),
    }


def _collect_iteration_info(session: Session, trace: WorkflowTraceSummary, task_id: str):
    try:
        from app.modules.iteration_decision.repository import IterationDecisionRepository
        id_repo = IterationDecisionRepository()
        decisions = id_repo.list_by_task_id(session, task_id)
        if decisions:
            iterated = [d for d in decisions if d.decision == "iterate"]
            trace.iteration_count = len(iterated)
            _diag("  iteration_info: %d decisions, %d iterations", len(decisions), len(iterated))
    except Exception as e:
        _diag("  iteration_info FAILED: %s", str(e))
        logger.warning("Failed to collect iteration info: %s", str(e))
