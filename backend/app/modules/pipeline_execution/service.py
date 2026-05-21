"""Pipeline Execution Service — main orchestrator."""

import uuid
import traceback
from datetime import datetime
from typing import Optional
from sqlmodel import Session

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
from app.modules.pipeline_execution.data_matrix_loader import load_model_ready_matrix
from app.modules.pipeline_execution.validation_splitter import create_validation_splits
from app.modules.pipeline_execution.execution_planner import expand_execution_plan
from app.modules.pipeline_execution.controlled_executor import execute_training
from app.modules.pipeline_execution.metric_input_builder import build_metric_evaluation_input
from app.modules.pipeline_execution.training_artifact_manager import (
    ensure_execution_dir,
    save_manifest,
    save_trial_results,
    save_split_metadata,
    save_execution_result,
    save_metric_evaluation_input,
)
from app.modules.pipeline_execution.builder import build_response
from app.modules.pipeline_execution.runtime_monitor import build_runtime_log
from app.modules.pipeline_execution.exceptions import (
    PipelineExecutionNotFoundException,
)


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
        warnings = []
        pe_id = f"pe_{uuid.uuid4().hex[:8]}"

        try:
            # Step 1: Build execution context (validate PG readiness)
            pg = build_execution_context(
                session, task_id, request.pipeline_generation_id,
            )

            # Step 2: Load and validate execution_input
            ei = load_execution_input(pg.execution_input_json)

            # Step 3: Load model-ready matrix
            matrix_path = ei.model_ready_matrix_path
            if not matrix_path:
                raise ValueError("model_ready_matrix_path is empty in execution_input.")
            X, y = load_model_ready_matrix(
                matrix_path=matrix_path,
                feature_columns=ei.feature_columns,
                target_column=ei.target_column,
            )

            # Step 4: Create validation splits
            validation_splits = create_validation_splits(X, y, ei.validation_plan)

            # Step 5: Expand execution plan (pipeline_specs + trial_plan → trial plans)
            trial_plans = expand_execution_plan(
                pipeline_specs=ei.pipeline_specs,
                trial_plan=ei.trial_plan,
                max_trials_override=request.max_trials_override,
            )

            # Step 6: Setup artifact directory
            exec_dir = ensure_execution_dir(pe_id)

            # Step 7: Execute training (controlled executor)
            execution_output = execute_training(
                X=X,
                y=y,
                trial_plans=trial_plans,
                validation_splits=validation_splits,
                task_type=ei.task_type or "regression",
                exec_dir=exec_dir,
                execution_mode=request.execution_mode,
                fail_fast=request.fail_fast,
                save_predictions=request.save_predictions,
                save_models=request.save_trained_models,
                max_runtime_seconds=request.max_runtime_seconds,
            )

            trial_results = execution_output["trial_results"]
            pipeline_run_results = execution_output["pipeline_run_results"]
            warnings.extend(execution_output.get("warnings", []))

            # Step 8: Collect prediction and model artifacts
            pred_artifacts = []
            model_artifacts = []
            for t in trial_results:
                if t.prediction_artifact_paths:
                    pred_artifacts.extend(t.prediction_artifact_paths)
                if t.model_artifact_paths:
                    model_artifacts.extend(t.model_artifact_paths)

            # Step 9: Build metric_evaluation_input
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

            artifact_manifest = {
                "exec_dir": exec_dir,
                "manifest_path": manifest_path,
                "execution_result_path": exec_result_path,
                "trial_results_path": f"{exec_dir}/trial_results.json",
                "prediction_paths": pred_artifacts,
                "model_paths": model_artifacts,
                "log_path": f"{exec_dir}/logs/execution.log",
                "split_metadata_path": f"{exec_dir}/splits/split_metadata.json",
                "metric_evaluation_input_path": metric_input_path,
            }

            finished_at = datetime.utcnow()

            # Step 11: Build response
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
            runtime_log = build_runtime_log(
                started_at=started_at,
                finished_at=finished_at,
                status=response.status,
                warnings=warnings,
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

            return response

        except Exception as e:
            finished_at = datetime.utcnow()
            error_msg = str(e)
            traceback_str = traceback.format_exc()

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
            except Exception:
                pass

            raise

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
