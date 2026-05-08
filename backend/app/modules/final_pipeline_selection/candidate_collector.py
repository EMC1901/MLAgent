import logging
from typing import List, Dict, Any, Optional
from sqlmodel import Session

from app.modules.metric_evaluation.model import MetricEvaluation
from app.modules.pipeline_execution.model import PipelineExecution
from app.modules.final_pipeline_selection.schemas import CandidateSelectionItem
from app.modules.final_pipeline_selection.selection_input_loader import FinalPipelineSelectionInput
from app.modules.final_pipeline_selection.exceptions import CandidateCollectionException

logger = logging.getLogger(__name__)


def collect_candidate_experiments(
    session: Session,
    selection_input: FinalPipelineSelectionInput,
) -> tuple:
    # Load MetricEvaluations
    metric_evals: List[MetricEvaluation] = []
    for me_id in selection_input.candidate_metric_evaluation_ids:
        me = session.get(MetricEvaluation, me_id)
        if me:
            metric_evals.append(me)
        else:
            logger.warning("MetricEvaluation %s not found", me_id)

    if not metric_evals:
        raise CandidateCollectionException("No valid MetricEvaluation records found.")

    # Load PipelineExecutions
    pipeline_execs: List[PipelineExecution] = []
    for pe_id in selection_input.candidate_pipeline_execution_ids:
        pe = session.get(PipelineExecution, pe_id)
        if pe:
            pipeline_execs.append(pe)
        else:
            logger.warning("PipelineExecution %s not found", pe_id)

    if not pipeline_execs:
        raise CandidateCollectionException("No valid PipelineExecution records found.")

    # Index pipeline executions by ID + pre-extract trial data for cross-referencing
    pe_index: Dict[str, PipelineExecution] = {pe.id: pe for pe in pipeline_execs if pe.id}
    pe_trials_index: Dict[str, Dict[str, Any]] = {}
    pe_runs_index: Dict[str, Dict[str, Any]] = {}
    for pe in pipeline_execs:
        exec_json = pe.execution_json or {}
        for t in exec_json.get("trial_results", []):
            tid = t.get("trial_id", "")
            if tid:
                pe_trials_index[tid] = t
        for pr in exec_json.get("pipeline_run_results", []):
            rid = pr.get("pipeline_run_id", "")
            if rid:
                pe_runs_index[rid] = pr

    # Build trial-level candidates from metric evaluations
    candidates: List[CandidateSelectionItem] = []
    for me in metric_evals:
        eval_json = me.evaluation_json or {}
        trial_metric_results = eval_json.get("trial_metric_results", [])
        model_ranking = eval_json.get("model_ranking", [])
        baseline_comparison = eval_json.get("baseline_comparison", {})

        if not trial_metric_results:
            # Fallback: build single candidate from best trial info
            candidate = _build_candidate_from_best(me, pipeline_execs, pe_trials_index, pe_runs_index)
            if candidate:
                candidates.append(candidate)
            continue

        for trial in trial_metric_results:
            candidate = _build_candidate_from_trial(
                trial, me, pipeline_execs, pe_index, pe_trials_index,
                pe_runs_index, model_ranking, baseline_comparison,
            )
            if candidate:
                candidates.append(candidate)

    if not candidates:
        raise CandidateCollectionException(
            "No candidates could be built from any MetricEvaluation or PipelineExecution records."
        )

    logger.info("Collected %d trial-level candidates", len(candidates))
    return candidates, metric_evals, pipeline_execs


def _build_candidate_from_trial(
    trial: Dict[str, Any],
    me: MetricEvaluation,
    pipeline_execs: List[PipelineExecution],
    pe_index: Dict[str, PipelineExecution],
    pe_trials_index: Dict[str, Dict[str, Any]],
    pe_runs_index: Dict[str, Dict[str, Any]],
    model_ranking: list,
    baseline_comparison: dict,
) -> Optional[CandidateSelectionItem]:
    # --- Extract from MetricEvaluation.TrialMetricResult ---
    trial_id = trial.get("trial_id") or ""
    model_id = trial.get("model_id") or ""
    model_family = trial.get("model_family") or ""
    pipeline_spec_id = trial.get("pipeline_spec_id") or ""
    pipeline_run_id = trial.get("pipeline_run_id") or ""
    pipeline_role = trial.get("pipeline_role") or ""
    trial_type = trial.get("trial_type") or ""
    params = trial.get("params") or {}
    # TrialMetricResult uses primary_metric_mean as the aggregated metric
    primary_metric_value = trial.get("primary_metric_mean")
    rank = trial.get("rank")
    is_best = trial.get("is_best_trial", False)

    # Fallbacks for missing fields
    if not model_family:
        model_family = model_id
    if not trial_type:
        trial_type = "hpo"
    if not pipeline_role:
        pipeline_role = "candidate"

    if "baseline" in (model_id or "").lower() or trial_type == "baseline":
        pipeline_role = "baseline"

    # --- Cross-reference with PipelineExecution trial_results for artifact paths ---
    pe_trial = pe_trials_index.get(trial_id, {})
    model_artifact_path = pe_trial.get("model_artifact_path")
    prediction_artifact_path = pe_trial.get("prediction_artifact_path")

    # --- Cross-reference with PipelineExecution pipeline_run_results for model_family ---
    if not model_family and pipeline_run_id:
        pe_run = pe_runs_index.get(pipeline_run_id, {})
        model_family = pe_run.get("model_family") or model_id

    # If model_family still empty, derive from model_id
    if not model_family:
        model_family = model_id

    # --- Find matching pipeline execution ---
    pe = _find_matching_pe(me, pipeline_execs, pe_index)

    # --- Check ranking from model_ranking list ---
    metric_rank = rank
    if metric_rank is None and model_ranking:
        for mr in model_ranking:
            if isinstance(mr, dict) and mr.get("model_id") == model_id:
                metric_rank = mr.get("rank")
                break

    return CandidateSelectionItem(
        candidate_id=trial_id,
        metric_evaluation_id=me.id,
        pipeline_execution_id=pe.id if pe else (me.pipeline_execution_id or ""),
        pipeline_generation_id=pe.pipeline_generation_id if pe else None,
        pipeline_spec_id=pipeline_spec_id,
        trial_id=trial_id,
        model_id=model_id,
        model_family=model_family,
        pipeline_role=pipeline_role,
        trial_type=trial_type,
        hyperparameters=params,
        primary_metric_value=float(primary_metric_value) if primary_metric_value is not None else None,
        primary_metric_rank=metric_rank,
        candidate_status="eligible",
    )


def _build_candidate_from_best(
    me: MetricEvaluation,
    pipeline_execs: List[PipelineExecution],
    pe_trials_index: Dict[str, Dict[str, Any]],
    pe_runs_index: Dict[str, Dict[str, Any]],
) -> Optional[CandidateSelectionItem]:
    """Fallback: build a single candidate from the MetricEvaluation best_* fields."""
    if not me.best_trial_id or not me.best_model_id:
        # Try to get from evaluation_json
        eval_json = me.evaluation_json or {}
        model_ranking = eval_json.get("model_ranking", [])
        if model_ranking:
            top = model_ranking[0]
            if isinstance(top, dict):
                me.best_model_id = top.get("model_id") or me.best_model_id
                me.best_trial_id = top.get("best_trial_id") or me.best_trial_id
                me.best_pipeline_spec_id = top.get("pipeline_spec_id") or me.best_pipeline_spec_id
                me.best_primary_metric_value = top.get("primary_metric_value")
        if not me.best_trial_id:
            return None

    # Cross-reference PE
    pe_trial = pe_trials_index.get(me.best_trial_id, {})
    params = pe_trial.get("params") or {}
    model_family = me.best_model_id or ""

    pe = _find_matching_pe(me, pipeline_execs)
    if pe and pe.execution_json:
        prs = pe.execution_json.get("pipeline_run_results", [])
        for pr in prs:
            if isinstance(pr, dict) and pr.get("model_id") == me.best_model_id:
                model_family = pr.get("model_family") or model_family
                break

    return CandidateSelectionItem(
        candidate_id=me.best_trial_id,
        metric_evaluation_id=me.id,
        pipeline_execution_id=pe.id if pe else (me.pipeline_execution_id or ""),
        pipeline_generation_id=pe.pipeline_generation_id if pe else None,
        pipeline_spec_id=me.best_pipeline_spec_id,
        trial_id=me.best_trial_id,
        model_id=me.best_model_id,
        model_family=model_family,
        pipeline_role="candidate",
        trial_type="hpo",
        hyperparameters=params,
        primary_metric_value=me.best_primary_metric_value,
        candidate_status="eligible",
    )


def _find_matching_pe(
    me: MetricEvaluation,
    pipeline_execs: List[PipelineExecution],
    pe_index: Dict[str, PipelineExecution] = None,
) -> Optional[PipelineExecution]:
    # Direct match by ID
    if pe_index and me.pipeline_execution_id:
        pe = pe_index.get(me.pipeline_execution_id)
        if pe:
            return pe
    # Linear fallback
    for pe in pipeline_execs:
        if pe.id == me.pipeline_execution_id:
            return pe
    return pipeline_execs[0] if pipeline_execs else None
