"""Pipeline Execution Service — main orchestrator."""

import logging
import os
import sys
import time
import uuid
import traceback
from datetime import datetime
from typing import Optional
from sqlmodel import Session

logger = logging.getLogger(__name__)


from app.modules.pipeline_execution.model import PipelineExecution
from app.modules.pipeline_execution.repository import PipelineExecutionRepository
from app.modules.pipeline_execution.schemas import (
    PipelineExecutionCreateRequest,
    PipelineExecutionResponse,
    PipelineExecutionSummaryResponse,
    LogsResponse,
)
from app.modules.pipeline_execution.context_builder import build_execution_context
from app.modules.pipeline_execution.execution_input_loader import load_execution_input
from app.modules.pipeline_execution.data_matrix_loader import (
    load_model_ready_matrix,
    resolve_fold_pipeline_spec_path,
)
from app.modules.feature_preprocessing.artifact_manager import load_fold_pipeline_spec
from app.modules.pipeline_execution.validation_splitter import create_validation_splits
from app.modules.pipeline_execution.execution_planner import expand_execution_plan
from app.modules.pipeline_execution.controlled_executor import execute_training
from app.modules.pipeline_execution.metric_input_builder import build_metric_evaluation_input
from app.modules.pipeline_execution.training_artifact_manager import (
    TRAINING_ARTIFACT_ROOT,
    ensure_execution_dir,
    save_manifest,
    save_trial_results,
    save_split_metadata,
    save_execution_result,
    save_metric_evaluation_input,
    get_execution_log_path,
    ExecutionLogHandler,
)
from app.modules.pipeline_execution.builder import build_response
from app.modules.pipeline_execution.runtime_monitor import build_runtime_log, capture_runtime_environment
from app.modules.pipeline_execution.exceptions import (
    PipelineExecutionNotFoundException,
)

_PE_PKG = "app.modules.pipeline_execution"


def _setup_execution_logging(exec_dir: str):
    """Attach an ExecutionLogHandler to every pipeline_execution logger.

    Uses sys.modules to reliably discover all module-level loggers under the
    pipeline_execution package.  Returns (handler, cleanup_callable).
    """
    log_path = get_execution_log_path(exec_dir)
    handler = ExecutionLogHandler(log_path)
    _prev_levels: dict = {}
    _pe_logger_names = {_PE_PKG}

    # Discover all imported pipeline_execution modules
    for mod_name in sys.modules:
        if mod_name == _PE_PKG or mod_name.startswith(_PE_PKG + "."):
            _pe_logger_names.add(mod_name)

    for name in sorted(_pe_logger_names):
        lg = logging.getLogger(name)
        _prev_levels[name] = lg.level
        lg.setLevel(logging.DEBUG)
        for h in lg.handlers:
            if isinstance(h, logging.StreamHandler):
                h.setLevel(logging.INFO)
        lg.addHandler(handler)

    def _cleanup():
        handler.close()
        for name, prev_level in _prev_levels.items():
            lg = logging.getLogger(name)
            try:
                lg.removeHandler(handler)
            except Exception:
                pass
            try:
                lg.setLevel(prev_level)
            except Exception:
                pass

    return handler, _cleanup


class PipelineExecutionService:

    def __init__(self):
        self.repo = PipelineExecutionRepository()

    def create_pipeline_execution(
        self,
        session: Session,
        task_id: str,
        request: PipelineExecutionCreateRequest,
    ) -> PipelineExecutionResponse:
        """Main entry point: create and execute a pipeline execution."""
        started_at = datetime.utcnow()
        start_ts = time.time()
        warnings = []
        pe_id = f"pe_{uuid.uuid4().hex[:8]}"

        # ── Set up per-execution logging before any step runs ──
        exec_dir = os.path.join(TRAINING_ARTIFACT_ROOT, pe_id)
        log_handler, _cleanup_logging = _setup_execution_logging(exec_dir)

        try:
            logger.info("=== Pipeline Execution — task=%s pe=%s mode=%s ===",
                         task_id, pe_id, request.execution_mode)
            logger.info("[1/12] Building execution context ...")
            t0 = time.time()
            pg = build_execution_context(
                session, task_id, request.pipeline_generation_id,
            )
            logger.info("[1/12] Done — pg_id=%s status=%s (%.1fs)", pg.id, pg.status, time.time() - t0)

            # Step 2: Load and validate execution_input
            logger.info("[2/12] Loading execution input ...")
            t0 = time.time()
            ei = load_execution_input(pg.execution_input_json)
            logger.info("[2/12] Done — task_type=%s target=%s n_specs=%d (%.1fs)",
                  ei.task_type, ei.target_column, len(ei.pipeline_specs or []), time.time() - t0)

            # Step 3: Load model-ready matrix
            matrix_path = ei.model_ready_matrix_path
            if not matrix_path:
                raise ValueError("model_ready_matrix_path is empty in execution_input.")
            logger.info("[3/12] Loading feature matrix from %s ...", matrix_path)
            t0 = time.time()
            X, y = load_model_ready_matrix(
                matrix_path=matrix_path,
                feature_columns=ei.feature_columns,
                target_column=ei.target_column,
            )
            logger.info("[3/12] Done — n_samples=%d n_features=%d (%.1fs)", len(X), len(X.columns), time.time() - t0)

            # Step 3b: Check for fold pipeline spec (fold-safe preprocessing)
            fold_spec_path = getattr(ei, "fold_pipeline_spec_path", None) or resolve_fold_pipeline_spec_path(matrix_path)
            fold_pipeline_spec = None
            if fold_spec_path:
                logger.info("[3b/12] Loading fold pipeline spec — %d ops",
                           len(load_fold_pipeline_spec(fold_spec_path).operations) if (fold_pipeline_spec := load_fold_pipeline_spec(fold_spec_path)) else 0)
            else:
                logger.info("[3b/12] No fold_pipeline_spec — proceeding without fold preprocessing")

            # Step 4: Create validation splits
            logger.info("[4/12] Creating validation splits ...")
            t0 = time.time()
            validation_splits = create_validation_splits(X, y, ei.validation_plan)
            logger.info("[4/12] Done — n_splits=%d (%.1fs)", len(validation_splits), time.time() - t0)

            # Step 5: Expand execution plan (pipeline_specs + trial_plan → trial plans)
            logger.info("[5/12] Expanding execution plan ...")
            t0 = time.time()
            trial_plans = expand_execution_plan(
                pipeline_specs=ei.pipeline_specs,
                trial_plan=ei.trial_plan,
                max_trials_override=request.max_trials_override,
            )
            logger.info("[5/12] Done — n_trials=%d (%.1fs)", len(trial_plans), time.time() - t0)

            # Step 6: Setup artifact directory
            logger.info("[6/12] Setting up artifact directory ...")
            t0 = time.time()
            exec_dir = ensure_execution_dir(pe_id)
            logger.info("[6/12] Done — %s (%.1fs)", exec_dir, time.time() - t0)

            # Step 7: Execute training (controlled executor)
            logger.info("[7/12] Executing training — %d trials, %d folds, %d samples ...",
                  len(trial_plans), len(validation_splits), len(X))
            t0_train = datetime.utcnow()
            execution_output = execute_training(
                X=X, y=y,
                trial_plans=trial_plans,
                validation_splits=validation_splits,
                task_type=ei.task_type or "regression",
                exec_dir=exec_dir,
                execution_mode=request.execution_mode,
                max_parallel_trials=request.max_parallel_trials,
                fail_fast=request.fail_fast,
                save_predictions=request.save_predictions,
                save_models=request.save_trained_models,
                max_runtime_seconds=request.max_runtime_seconds,
                fold_pipeline_spec=fold_pipeline_spec,
            )

            train_dur = (datetime.utcnow() - t0_train).total_seconds()
            trial_results = execution_output["trial_results"]
            pipeline_run_results = execution_output["pipeline_run_results"]
            warnings.extend(execution_output.get("warnings", []))
            logger.info("[7/12] Done — %d completed / %d failed in %.1fs",
                  execution_output["n_completed"], execution_output["n_failed"], train_dur)

            # Step 8: Collect prediction and model artifacts
            pred_artifacts = []
            model_artifacts = []
            for t in trial_results:
                if t.prediction_artifact_paths:
                    pred_artifacts.extend(t.prediction_artifact_paths)
                if t.model_artifact_paths:
                    model_artifacts.extend(t.model_artifact_paths)

            # Step 8-9: Build metric_evaluation_input
            logger.info("[8-9/12] Building metric evaluation input ...")
            t0 = time.time()
            metric_input = build_metric_evaluation_input(
                pipeline_execution_id=pe_id,
                pipeline_generation_id=pg.id,
                task_id=task_id,
                task_type=ei.task_type or "regression",
                target_column=ei.target_column,
                evaluation_plan=ei.evaluation_plan,
                validation_plan=ei.validation_plan,
                trial_results=trial_results,
                prediction_artifacts=pred_artifacts,
                model_artifacts=model_artifacts,
                primary_metric=ei.evaluation_plan.get("primary_metric"),
                metric_direction=ei.evaluation_plan.get("metric_direction", "minimize"),
            )

            # Step 10: Save artifacts
            logger.info("[10/12] Saving artifacts ...")
            t0 = time.time()
            save_split_metadata(exec_dir, validation_splits)
            save_trial_results(exec_dir, trial_results)

            manifest = {
                "pipeline_execution_id": pe_id,
                "task_id": task_id,
                "pipeline_generation_id": pg.id,
                "created_at": started_at.isoformat(),
            }
            manifest_path = save_manifest(exec_dir, manifest)

            exec_result = {
                "pipeline_execution_id": pe_id,
                "task_id": task_id,
                "pipeline_generation_id": pg.id,
                "n_trials": len(trial_results),
                "n_completed": sum(1 for t in trial_results if t.status == "completed"),
                "n_failed": sum(1 for t in trial_results if t.status == "failed"),
            }
            exec_result_path = save_execution_result(exec_dir, exec_result)

            metric_input_path = save_metric_evaluation_input(
                exec_dir,
                metric_input.model_dump() if hasattr(metric_input, "model_dump") else metric_input,
            )
            logger.info("[10/12] Done (%.1fs)", time.time() - t0)

            artifact_manifest = {
                "exec_dir": exec_dir,
                "manifest_path": manifest_path,
                "execution_result_path": exec_result_path,
                "trial_results_path": f"{exec_dir}/trial_results.json",
                "prediction_paths": pred_artifacts,
                "model_paths": model_artifacts,
                "log_path": get_execution_log_path(exec_dir),
                "split_metadata_path": f"{exec_dir}/splits/split_metadata.json",
                "metric_evaluation_input_path": metric_input_path,
            }

            finished_at = datetime.utcnow()

            # Step 11: Build response
            logger.info("[11/12] Building response ...")
            t0 = time.time()
            response = build_response(
                pipeline_execution_id=pe_id,
                task_id=task_id,
                pipeline_generation_id=pg.id,
                execution_mode=request.execution_mode,
                trial_results=[t.model_dump() for t in trial_results],
                pipeline_run_results=[p.model_dump() for p in pipeline_run_results],
                execution_result=exec_result,
                metric_evaluation_input=metric_input,
                artifact_manifest=artifact_manifest,
                started_at=started_at,
                finished_at=finished_at,
                warnings=warnings,
                error_message=None,
                created_at=started_at,
                updated_at=finished_at,
            )

            # Step 12: Persist to database
            logger.info("[12/12] Persisting to DB ...")
            runtime_env = capture_runtime_environment()
            runtime_log = build_runtime_log(
                started_at=started_at,
                finished_at=finished_at,
                status=response.status,
                warnings=warnings,
                events=log_handler.events,
                env_info=runtime_env.model_dump() if hasattr(runtime_env, "model_dump") else {},
                n_trials_planned=response.n_trials_planned,
                n_trials_completed=response.n_trials_completed,
                n_trials_failed=response.n_trials_failed,
            )

            db_record = PipelineExecution(
                id=pe_id,
                task_id=task_id,
                pipeline_generation_id=pg.id,
                status=response.status,
                execution_mode=request.execution_mode,
                task_type=ei.task_type,
                target_column=ei.target_column,
                primary_metric=ei.evaluation_plan.get("primary_metric"),
                n_pipeline_specs=response.n_pipeline_specs,
                n_trials_planned=response.n_trials_planned,
                n_trials_completed=response.n_trials_completed,
                n_trials_failed=response.n_trials_failed,
                n_models_trained=response.n_models_trained,
                ready_for_metric_evaluation=response.ready_for_metric_evaluation,
                training_artifact_dir=exec_dir,
                execution_json=response.model_dump(mode="json"),
                metric_evaluation_input_json=(
                    metric_input.model_dump(mode="json") if hasattr(metric_input, "model_dump") else metric_input
                ),
                runtime_log_json=runtime_log,
                error_message=None,
                started_at=started_at,
                finished_at=finished_at,
                created_at=started_at,
                updated_at=finished_at,
            )
            self.repo.create(session, db_record)
            total_dur = time.time() - start_ts
            logger.info("[12/12] Done — status=%s n_models=%d | TOTAL %.1fs",
                       response.status, response.n_models_trained, total_dur)

            return response

        except Exception as e:
            finished_at = datetime.utcnow()
            error_msg = str(e)
            traceback_str = traceback.format_exc()
            logger.error("Pipeline Execution FAILED: %s\n%s", error_msg, traceback_str)

            # Persist failure
            try:
                fail_record = PipelineExecution(
                    id=pe_id,
                    task_id=task_id,
                    pipeline_generation_id=request.pipeline_generation_id or "",
                    status="failed",
                    execution_mode=request.execution_mode,
                    error_message=error_msg,
                    started_at=started_at,
                    finished_at=finished_at,
                    created_at=started_at,
                    updated_at=finished_at,
                    runtime_log_json={"error": error_msg, "traceback": traceback_str},
                )
                self.repo.create(session, fail_record)
                logger.debug("failure record persisted: pe_id=%s", pe_id)
            except Exception as persist_err:
                logger.debug("failed to persist failure record: %s", persist_err)

            raise
        finally:
            _cleanup_logging()

    def get_pipeline_execution(
        self, session: Session, pe_id: str,
    ) -> PipelineExecutionResponse:
        record = self.repo.get_by_id(session, pe_id)
        if not record:
            raise PipelineExecutionNotFoundException(
                f"PipelineExecution '{pe_id}' not found."
            )
        if record.execution_json:
            return PipelineExecutionResponse(**record.execution_json)
        return self._record_to_response(record)

    def get_latest_by_task_id(
        self, session: Session, task_id: str,
    ) -> PipelineExecutionResponse:
        record = self.repo.get_latest_by_task_id(session, task_id)
        if not record:
            raise PipelineExecutionNotFoundException(
                f"No PipelineExecution found for task '{task_id}'."
            )
        if record.execution_json:
            return PipelineExecutionResponse(**record.execution_json)
        return self._record_to_response(record)

    def rerun_pipeline_execution(
        self, session: Session, task_id: str,
    ) -> PipelineExecutionResponse:
        return self.create_pipeline_execution(
            session, task_id,
            PipelineExecutionCreateRequest(force_rerun=True),
        )

    def get_summary(
        self, session: Session, pe_id: str,
    ) -> PipelineExecutionSummaryResponse:
        record = self.repo.get_by_id(session, pe_id)
        if not record:
            raise PipelineExecutionNotFoundException(
                f"PipelineExecution '{pe_id}' not found."
            )
        return PipelineExecutionSummaryResponse(
            pipeline_execution_id=record.id,
            task_id=record.task_id,
            status=record.status or "unknown",
            n_pipeline_specs=record.n_pipeline_specs or 0,
            n_trials_planned=record.n_trials_planned or 0,
            n_trials_completed=record.n_trials_completed or 0,
            n_trials_failed=record.n_trials_failed or 0,
            n_models_trained=record.n_models_trained or 0,
            ready_for_metric_evaluation=record.ready_for_metric_evaluation or False,
            duration_seconds=(
                (record.finished_at - record.started_at).total_seconds()
                if record.started_at and record.finished_at
                else 0.0
            ),
            warnings=record.runtime_log_json.get("warnings", []) if record.runtime_log_json else [],
            created_at=record.created_at,
        )

    def get_trials(self, session: Session, pe_id: str) -> list:
        record = self.repo.get_by_id(session, pe_id)
        if not record:
            raise PipelineExecutionNotFoundException(
                f"PipelineExecution '{pe_id}' not found."
            )
        if record.execution_json:
            return record.execution_json.get("trial_results", [])
        return []

    def get_metric_evaluation_input(self, session: Session, pe_id: str) -> dict:
        record = self.repo.get_by_id(session, pe_id)
        if not record:
            raise PipelineExecutionNotFoundException(
                f"PipelineExecution '{pe_id}' not found."
            )
        if record.metric_evaluation_input_json:
            return record.metric_evaluation_input_json
        return {}

    def get_logs(self, session: Session, pe_id: str) -> LogsResponse:
        record = self.repo.get_by_id(session, pe_id)
        if not record:
            raise PipelineExecutionNotFoundException(
                f"PipelineExecution '{pe_id}' not found."
            )
        event_log = []
        if record.runtime_log_json:
            event_log = record.runtime_log_json.get("events", [])
        return LogsResponse(
            pipeline_execution_id=record.id,
            status=record.status or "unknown",
            started_at=record.started_at,
            finished_at=record.finished_at,
            duration_seconds=(
                (record.finished_at - record.started_at).total_seconds()
                if record.started_at and record.finished_at
                else 0.0
            ),
            event_log=event_log,
            error_message=record.error_message,
            warnings=record.runtime_log_json.get("warnings", []) if record.runtime_log_json else [],
        )

    def _record_to_response(self, record: PipelineExecution) -> PipelineExecutionResponse:
        return PipelineExecutionResponse(
            pipeline_execution_id=record.id,
            task_id=record.task_id,
            pipeline_generation_id=record.pipeline_generation_id,
            status=record.status or "unknown",
            execution_mode=record.execution_mode or "sequential",
            n_pipeline_specs=record.n_pipeline_specs or 0,
            n_trials_planned=record.n_trials_planned or 0,
            n_trials_completed=record.n_trials_completed or 0,
            n_trials_failed=record.n_trials_failed or 0,
            n_models_trained=record.n_models_trained or 0,
            started_at=record.started_at,
            finished_at=record.finished_at,
            duration_seconds=(
                (record.finished_at - record.started_at).total_seconds()
                if record.started_at and record.finished_at
                else 0.0
            ),
            ready_for_metric_evaluation=record.ready_for_metric_evaluation or False,
            error_message=record.error_message,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
