import logging
from typing import Optional
from sqlmodel import Session

from app.modules.workflow_refinement.schemas import ExperimentHistorySummary

logger = logging.getLogger(__name__)


def collect_experiment_history(session: Session, task_id: str) -> ExperimentHistorySummary:
    """Collect historical experiment data for multi-iteration decision support."""
    summary = ExperimentHistorySummary()

    try:
        from app.modules.workflow_refinement.repository import WorkflowRefinementRepository
        wr_repo = WorkflowRefinementRepository()
        prev_refinements = wr_repo.list_by_task_id(session, task_id)
        summary.n_iterations_completed = len(prev_refinements)
        summary.previous_decisions = [
            wr.decision for wr in prev_refinements if wr.decision
        ]
    except Exception as e:
        logger.debug("Could not load previous refinement history: %s", str(e))

    try:
        from app.modules.metric_evaluation.repository import MetricEvaluationRepository
        me_repo = MetricEvaluationRepository()
        me_list = me_repo.list_by_task_id(session, task_id)
        if me_list:
            best_val = None
            for me in me_list:
                primary = me.best_primary_metric_value
                if primary is None and me.evaluation_json:
                    primary = me.evaluation_json.get("primary_metric_value")
                if primary is not None:
                    if best_val is None or primary < best_val:
                        best_val = primary
                        if me.best_model_id:
                            summary.best_model_so_far = me.best_model_id
            summary.best_metric_so_far = best_val
            if len(me_list) >= 2:
                prev = me_list[-1].best_primary_metric_value
                if prev is None and me_list[-1].evaluation_json:
                    prev = me_list[-1].evaluation_json.get("primary_metric_value")
                curr = me_list[0].best_primary_metric_value
                if curr is None and me_list[0].evaluation_json:
                    curr = me_list[0].evaluation_json.get("primary_metric_value")
                if prev is not None and curr is not None:
                    if curr < prev:
                        summary.metric_trend = "improving"
                    elif curr > prev:
                        summary.metric_trend = "degrading"
                    else:
                        summary.metric_trend = "stable"
    except Exception as e:
        logger.debug("Could not collect metric evaluation history: %s", str(e))

    try:
        from app.modules.result_diagnosis.repository import ResultDiagnosisRepository
        rd_repo = ResultDiagnosisRepository()
        rd_list = rd_repo.list_by_task_id(session, task_id)
        diag_types = []
        for rd in rd_list:
            if rd.diagnosis_json:
                findings = rd.diagnosis_json.get("diagnostic_findings") or []
                for f in findings:
                    if isinstance(f, dict):
                        diag_types.append(f.get("diagnosis_type", ""))
        from collections import Counter
        type_counts = Counter(dt for dt in diag_types if dt)
        summary.repeated_diagnosis_types = [
            dt for dt, count in type_counts.items() if count > 1
        ]
    except Exception as e:
        logger.debug("Could not collect diagnosis history: %s", str(e))

    try:
        from app.modules.model_search_context.repository import ModelSearchContextRepository
        msc_repo = ModelSearchContextRepository()
        msc_list = msc_repo.list_by_task_id(session, task_id)
        for msc in msc_list:
            if msc.context_json:
                models = msc.context_json.get("candidate_model_plan", {})
                if isinstance(models, dict):
                    families = models.get("candidate_model_families", [])
                    if isinstance(families, list):
                        for f in families:
                            if f not in summary.tried_model_families:
                                summary.tried_model_families.append(f)
    except Exception as e:
        logger.debug("Could not collect model search history: %s", str(e))

    try:
        from app.modules.pipeline_execution.repository import PipelineExecutionRepository
        pe_repo = PipelineExecutionRepository()
        pe_list = pe_repo.list_by_task_id(session, task_id)
        total_failures = 0
        total_trials = 0
        for pe in pe_list:
            if pe.execution_json:
                trial_results = pe.execution_json.get("trial_results") or []
                for t in trial_results:
                    total_trials += 1
                    if isinstance(t, dict) and t.get("status") == "failed":
                        total_failures += 1
        if total_trials > 0:
            summary.failed_trial_summary = f"{total_failures}/{total_trials} trials failed"
        total_runtime = sum(
            (pe.execution_json or {}).get("total_runtime_seconds", 0) or 0
            for pe in pe_list
        )
        if total_runtime > 0:
            summary.runtime_cost_summary = f"{total_runtime:.0f}s total runtime across {len(pe_list)} executions"
    except Exception as e:
        logger.debug("Could not collect pipeline execution history: %s", str(e))

    return summary
