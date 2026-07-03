import logging
from typing import Dict, Any, List
from sqlmodel import Session
from collections import Counter

logger = logging.getLogger(__name__)


def gather_history_context(session: Session, task_id: str) -> Dict[str, Any]:
    """Collect historical iteration data for multi-round decision support."""
    history: Dict[str, Any] = {
        "n_iterations_completed": 0,
        "previous_decisions": [],
        "best_metric_so_far": None,
        "best_model_so_far": None,
        "metric_trend": "unknown",
        "repeated_root_causes": [],
        "tried_model_families": [],
        "tried_feature_strategies": [],
        "total_failed_trials": 0,
        "total_trials": 0,
        "runtime_cost_summary": None,
        "failed_trial_summary": None,
    }

    # Previous iteration decisions
    try:
        from app.modules.iteration_decision.repository import IterationDecisionRepository
        id_repo = IterationDecisionRepository()
        prev = id_repo.list_completed_by_task_id(session, task_id)
        history["n_iterations_completed"] = len(prev)
        history["previous_decisions"] = [d.decision for d in prev if d.decision]

        # Repeated root causes
        root_causes = []
        for d in prev:
            if d.reasoning_json and isinstance(d.reasoning_json, dict):
                rc = d.reasoning_json.get("root_cause", {})
                if isinstance(rc, dict):
                    primary = rc.get("primary_root_cause", "")
                    if primary:
                        root_causes.append(primary)
        cause_counts = Counter(root_causes)
        history["repeated_root_causes"] = [c for c, n in cause_counts.items() if n > 1]
    except Exception:
        pass

    # Metric trend across evaluations
    try:
        from app.modules.metric_evaluation.repository import MetricEvaluationRepository
        me_repo = MetricEvaluationRepository()
        me_list = me_repo.list_by_task_id(session, task_id)
        best_val = None
        for me in me_list:
            val = getattr(me, "best_primary_metric_value", None)
            if val is not None:
                if best_val is None:
                    best_val = val
                elif getattr(me, "metric_direction", "minimize") == "minimize":
                    if val < best_val:
                        best_val = val
                        if getattr(me, "best_model_id", None):
                            history["best_model_so_far"] = me.best_model_id
                else:
                    if val > best_val:
                        best_val = val
                        if getattr(me, "best_model_id", None):
                            history["best_model_so_far"] = me.best_model_id
        history["best_metric_so_far"] = best_val

        if len(me_list) >= 2:
            sorted_me = sorted(me_list, key=lambda m: m.created_at or "")
            direction = getattr(sorted_me[-1], "metric_direction", "minimize")
            first_val = getattr(sorted_me[0], "best_primary_metric_value", None)
            last_val = getattr(sorted_me[-1], "best_primary_metric_value", None)
            if first_val is not None and last_val is not None:
                if direction == "minimize":
                    if last_val < first_val:
                        history["metric_trend"] = "improving"
                    elif last_val > first_val:
                        history["metric_trend"] = "degrading"
                    else:
                        history["metric_trend"] = "stable"
                else:
                    if last_val > first_val:
                        history["metric_trend"] = "improving"
                    elif last_val < first_val:
                        history["metric_trend"] = "degrading"
                    else:
                        history["metric_trend"] = "stable"
    except Exception:
        pass

    # Model families tried
    try:
        from app.modules.model_search_context.repository import ModelSearchContextRepository
        msc_repo = ModelSearchContextRepository()
        msc_list = msc_repo.list_by_task_id(session, task_id)
        families: List[str] = []
        for msc in msc_list:
            if msc.context_json:
                plan = msc.context_json.get("candidate_model_plan", {})
                if isinstance(plan, dict):
                    f_list = plan.get("candidate_model_families", [])
                    if isinstance(f_list, list):
                        for f in f_list:
                            if f not in families:
                                families.append(f)
        history["tried_model_families"] = families
    except Exception:
        pass

    # Pipeline execution stats
    try:
        from app.modules.pipeline_execution.repository import PipelineExecutionRepository
        pe_repo = PipelineExecutionRepository()
        pe_list = pe_repo.list_by_task_id(session, task_id)
        total_failures = 0
        total_trials = 0
        total_runtime = 0.0
        for pe in pe_list:
            if pe.execution_json:
                trials = pe.execution_json.get("trial_results") or []
                for t in trials:
                    total_trials += 1
                    if isinstance(t, dict) and t.get("status") == "failed":
                        total_failures += 1
                total_runtime += pe.execution_json.get("total_runtime_seconds", 0) or 0
        history["total_failed_trials"] = total_failures
        history["total_trials"] = total_trials
        if total_trials > 0:
            history["failed_trial_summary"] = f"{total_failures}/{total_trials} trials failed"
        if total_runtime > 0:
            history["runtime_cost_summary"] = f"{total_runtime:.0f}s total across {len(pe_list)} executions"
    except Exception:
        pass

    logger.info("History context — %d iterations, trend=%s, best=%.4f, models=%d, failures=%d/%d",
                 history["n_iterations_completed"], history["metric_trend"],
                 history["best_metric_so_far"] if history["best_metric_so_far"] is not None else float("nan"),
                 len(history["tried_model_families"]),
                 history["total_failed_trials"], history["total_trials"])

    return history
