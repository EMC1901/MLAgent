"""Controlled Executor — the ONLY entry point for training execution.

No LLM code, no eval, no dynamic imports. Models come from Model Registry only.

Supports two execution modes:
  - sequential:    One trial at a time (original behaviour).
  - limited_parallel: Up to max_parallel_trials trials run concurrently via
    ThreadPoolExecutor.  sklearn models with n_jobs=-1 release the GIL during
    C-level operations, so threads provide meaningful CPU parallelism.
"""

import logging
import time
import traceback
import concurrent.futures
from datetime import datetime
from typing import List
from app.modules.pipeline_execution.trial_runner import run_trial
from app.modules.pipeline_execution.schemas import (
    TrialResultDTO,
    PipelineRunResultDTO,
)
from app.modules.pipeline_execution.exceptions import TrialExecutionException

logger = logging.getLogger(__name__)


def execute_training(
    X,
    y,
    trial_plans: List[dict],
    validation_splits: list,
    task_type: str,
    exec_dir: str,
    execution_mode: str = "sequential",
    max_parallel_trials: int = 2,
    fail_fast: bool = False,
    save_predictions: bool = True,
    save_models: bool = True,
    max_runtime_seconds: int = None,
    fold_timeout_seconds: int = 30,
    fold_pipeline_spec=None,
) -> dict:
    """Execute all trials from the expanded execution plan.

    Args:
        X: Feature matrix.
        y: Target vector.
        trial_plans: List of trial plan dicts from execution_planner.
        validation_splits: List of split dicts.
        task_type: 'regression' or 'classification'.
        exec_dir: Artifact output directory.
        execution_mode: 'sequential' or 'limited_parallel'.
        max_parallel_trials: Max concurrent trials in limited_parallel mode.
        fail_fast: Stop after first trial failure.
        save_predictions: Whether to persist predictions.
        save_models: Whether to persist model files.
        max_runtime_seconds: Maximum total execution time (cooperative check).
        fold_timeout_seconds: Max seconds per fold before timeout (default 30).

    Returns:
        Dict with trial_results, pipeline_run_results, n_completed,
        n_failed, and warnings.
    """
    started = time.time()

    logger.info("starting training: n_trials=%d n_splits=%d mode=%s fail_fast=%s max_runtime=%ss fold_timeout=%ds",
          len(trial_plans), len(validation_splits), execution_mode,
          fail_fast, max_runtime_seconds or "none", fold_timeout_seconds)

    if execution_mode == "limited_parallel" and len(trial_plans) > 1:
        n_workers = min(max_parallel_trials, len(trial_plans), 4)
        return _execute_parallel(
            X=X, y=y, trial_plans=trial_plans,
            validation_splits=validation_splits,
            task_type=task_type, exec_dir=exec_dir,
            n_workers=n_workers, fail_fast=fail_fast,
            save_predictions=save_predictions, save_models=save_models,
            max_runtime_seconds=max_runtime_seconds,
            fold_timeout_seconds=fold_timeout_seconds,
            started=started,
            fold_pipeline_spec=fold_pipeline_spec,
        )

    return _execute_sequential(
        X=X, y=y, trial_plans=trial_plans,
        validation_splits=validation_splits,
        task_type=task_type, exec_dir=exec_dir,
        fail_fast=fail_fast,
        save_predictions=save_predictions, save_models=save_models,
        max_runtime_seconds=max_runtime_seconds,
        fold_timeout_seconds=fold_timeout_seconds,
        started=started,
        fold_pipeline_spec=fold_pipeline_spec,
    )


def _execute_sequential(
    X, y, trial_plans, validation_splits, task_type, exec_dir,
    fail_fast, save_predictions, save_models, max_runtime_seconds,
    fold_timeout_seconds, started,
    fold_pipeline_spec=None,
) -> dict:
    """Original sequential execution path."""
    trial_results: List[TrialResultDTO] = []
    pipeline_runs: dict = {}
    warnings = []

    last_progress_ts = time.time()
    for i, tp in enumerate(trial_plans):
        trial_idx = i + 1

        if max_runtime_seconds and (time.time() - started) > max_runtime_seconds:
            warnings.append(
                f"Execution timeout reached ({max_runtime_seconds}s). "
                f"Remaining trials skipped."
            )
            break

        spec_id = tp["pipeline_spec_id"]

        if spec_id not in pipeline_runs:
            pipeline_runs[spec_id] = PipelineRunResultDTO(
                pipeline_run_id=f"prun_{spec_id}",
                pipeline_spec_id=spec_id,
                pipeline_role=tp["pipeline_role"],
                model_id=tp["model_id"],
                model_family=tp.get("model_family"),
                hpo_enabled=tp.get("hpo_enabled", False),
                status="running",
            )

        pr = pipeline_runs[spec_id]
        pr.n_trials_planned += 1

        try:
            t0_trial = time.time()
            trial_result = run_trial(
                X=X, y=y, trial_plan=tp,
                validation_splits=validation_splits,
                task_type=task_type, exec_dir=exec_dir,
                save_predictions_flag=save_predictions,
                save_model_flag=save_models,
                parallel_folds=True,
                fold_timeout_seconds=fold_timeout_seconds,
                fold_pipeline_spec=fold_pipeline_spec,
            )
            trial_dur = time.time() - t0_trial
            trial_results.append(trial_result)

            if trial_result.status == "completed":
                pr.n_trials_completed += 1
                if trial_result.prediction_artifact_paths:
                    pr.prediction_artifact_paths.extend(trial_result.prediction_artifact_paths)
                if trial_result.model_artifact_paths:
                    pr.model_artifact_paths.extend(trial_result.model_artifact_paths)
            else:
                pr.n_trials_failed += 1
                err_snippet = (trial_result.error_message or "unknown")[:120]
                logger.warning("trial %d/%d — %s FAILED: %s",
                              trial_idx, len(trial_plans), tp["model_id"], err_snippet)
                if fail_fast:
                    warnings.append(f"fail_fast triggered after trial {tp['trial_id']} failed.")
                    break

            # Periodic progress: every 10 trials or 30 seconds
            now = time.time()
            if trial_idx % 10 == 0 or (now - last_progress_ts) > 30:
                n_done = sum(1 for t in trial_results if t.status == "completed")
                n_fail = sum(1 for t in trial_results if t.status == "failed")
                elapsed = now - started
                logger.info("Training progress: %d/%d trials (%d ok, %d fail) — %.0fs elapsed",
                           trial_idx, len(trial_plans), n_done, n_fail, elapsed)
                last_progress_ts = now

        except Exception as e:
            pr.n_trials_failed += 1
            logger.error("trial %d/%d — CRASHED: %s", trial_idx, len(trial_plans), str(e)[:200])
            failed_result = TrialResultDTO(
                trial_id=tp["trial_id"],
                pipeline_spec_id=spec_id,
                pipeline_run_id=f"prun_{spec_id}",
                model_id=tp["model_id"],
                trial_index=tp["trial_index"],
                trial_type=tp["trial_type"],
                params=tp.get("params", {}),
                status="failed",
                error_message=str(e),
            )
            trial_results.append(failed_result)
            warnings.append(f"Trial {tp['trial_id']} error: {e}")
            if fail_fast:
                break

    return _finalize(trial_results, pipeline_runs, started, warnings)


def _execute_parallel(
    X, y, trial_plans, validation_splits, task_type, exec_dir,
    n_workers, fail_fast, save_predictions, save_models,
    max_runtime_seconds, fold_timeout_seconds, started,
    fold_pipeline_spec=None,
) -> dict:
    """Parallel execution via ThreadPoolExecutor.

    Each trial is submitted to a thread pool.  Results are collected via
    as_completed so we can log progress as each trial finishes.
    """
    trial_results: List[TrialResultDTO] = []
    warnings = []

    logger.debug("parallel mode: dispatching %d trials on %d workers ...",
          len(trial_plans), n_workers)

    def _run_one(tp: dict) -> dict:
        """Run a single trial and return {trial_result, tp, error}."""
        t0 = time.time()
        trial_idx = tp.get("_trial_idx", 0)
        logger.debug("worker — trial %d/%d (%s) started",
              trial_idx, len(trial_plans), tp["trial_id"])
        try:
            tr = run_trial(
                X=X, y=y, trial_plan=tp,
                validation_splits=validation_splits,
                task_type=task_type, exec_dir=exec_dir,
                save_predictions_flag=save_predictions,
                save_model_flag=save_models,
                parallel_folds=False,  # don't nest parallelism
                fold_timeout_seconds=fold_timeout_seconds,
                fold_pipeline_spec=fold_pipeline_spec,
            )
            dur = time.time() - t0
            logger.debug("worker — trial %d/%d (%s) %s in %.1fs",
                  trial_idx, len(trial_plans), tp["trial_id"],
                  tr.status, dur)
            return {"trial_result": tr, "tp": tp, "error": None}
        except Exception as e:
            dur = time.time() - t0
            logger.error("worker — trial %d/%d (%s) CRASHED in %.1fs: %s",
                  trial_idx, len(trial_plans), tp["trial_id"], dur, e)
            return {"trial_result": None, "tp": tp, "error": str(e)}

    # Label trials with their index for logging
    for i, tp in enumerate(trial_plans):
        tp["_trial_idx"] = i + 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as pool:
        future_to_tp = {pool.submit(_run_one, tp): tp for tp in trial_plans}

        for future in concurrent.futures.as_completed(future_to_tp):
            tp = future_to_tp[future]
            try:
                result = future.result()
            except Exception as e:
                logger.error("worker — trial %s future.result() crashed: %s", tp["trial_id"], e)
                result = {"trial_result": None, "tp": tp, "error": str(e)}

            if result["trial_result"] is not None:
                trial_results.append(result["trial_result"])
            else:
                trial_results.append(TrialResultDTO(
                    trial_id=tp["trial_id"],
                    pipeline_spec_id=tp["pipeline_spec_id"],
                    pipeline_run_id=f"prun_{tp['pipeline_spec_id']}",
                    model_id=tp["model_id"],
                    trial_index=tp["trial_index"],
                    trial_type=tp["trial_type"],
                    params=tp.get("params", {}),
                    status="failed",
                    error_message=result["error"] or "unknown",
                ))
                warnings.append(f"Trial {tp['trial_id']} error: {result['error']}")

            if fail_fast and result.get("error"):
                warnings.append(f"fail_fast triggered after trial {tp['trial_id']} failed.")
                for f in future_to_tp:
                    f.cancel()
                break

    # Build pipeline_runs from trial results
    pipeline_runs: dict = {}
    for tr in trial_results:
        sid = tr.pipeline_spec_id
        if sid not in pipeline_runs:
            pipeline_runs[sid] = PipelineRunResultDTO(
                pipeline_run_id=f"prun_{sid}",
                pipeline_spec_id=sid,
                pipeline_role="",
                model_id=tr.model_id,
                status="running",
            )
        pr = pipeline_runs[sid]
        pr.n_trials_planned += 1
        if tr.status == "completed":
            pr.n_trials_completed += 1
            if tr.prediction_artifact_paths:
                pr.prediction_artifact_paths.extend(tr.prediction_artifact_paths)
            if tr.model_artifact_paths:
                pr.model_artifact_paths.extend(tr.model_artifact_paths)
        else:
            pr.n_trials_failed += 1

    return _finalize(trial_results, pipeline_runs, started, warnings)


def _finalize(
    trial_results: list, pipeline_runs: dict, started: float, warnings: list,
) -> dict:
    """Finalize pipeline run statuses and build return dict."""
    for spec_id, pr in pipeline_runs.items():
        if pr.n_trials_completed > 0 and pr.n_trials_failed == 0:
            pr.status = "completed"
        elif pr.n_trials_completed > 0 and pr.n_trials_failed > 0:
            pr.status = "partially_failed"
        elif pr.n_trials_failed > 0 and pr.n_trials_completed == 0:
            pr.status = "failed"
        else:
            pr.status = "skipped"

    n_completed = sum(1 for t in trial_results if t.status == "completed")
    n_failed = sum(1 for t in trial_results if t.status == "failed")
    total_dur = time.time() - started

    logger.info("training finished in %.1fs: n_trials=%d n_completed=%d n_failed=%d",
                total_dur, len(trial_results), n_completed, n_failed)

    # Log failure summary for quick diagnosis
    if n_failed > 0:
        failures = [t for t in trial_results if t.status == "failed"]
        unique_errors = {}
        for f in failures:
            msg = (f.error_message or "unknown")[:200]
            key = msg.split("\n")[0][:120]
            if key not in unique_errors:
                unique_errors[key] = {"count": 0, "model_id": f.model_id, "sample": msg}
            unique_errors[key]["count"] += 1
        logger.error("TRIAL FAILURES: %d/%d failed. Unique error types: %d",
                     n_failed, len(trial_results), len(unique_errors))
        for i, (key, info) in enumerate(sorted(unique_errors.items(), key=lambda x: -x[1]["count"])[:5]):
            logger.error("  [%d×] model=%s — %s", info["count"], info["model_id"], info["sample"][:250])

    return {
        "trial_results": trial_results,
        "pipeline_run_results": list(pipeline_runs.values()),
        "n_completed": n_completed,
        "n_failed": n_failed,
        "warnings": warnings,
    }
