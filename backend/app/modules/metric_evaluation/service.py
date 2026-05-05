import uuid
import traceback
from datetime import datetime
from typing import Optional
from sqlmodel import Session

from app.modules.metric_evaluation.model import MetricEvaluation
from app.modules.metric_evaluation.repository import MetricEvaluationRepository
from app.modules.metric_evaluation.schemas import (
    MetricEvaluationCreateRequest,
    MetricEvaluationResponse,
    MetricEvaluationSummaryResponse,
)
from app.modules.metric_evaluation.context_builder import build_metric_evaluation_context
from app.modules.metric_evaluation.metric_input_loader import load_metric_evaluation_input
from app.modules.metric_evaluation.prediction_artifact_loader import (
    load_prediction_artifacts,
    build_prediction_frame_map,
)
from app.modules.metric_evaluation.fold_metric_evaluator import evaluate_fold_metrics
from app.modules.metric_evaluation.trial_metric_aggregator import aggregate_trial_metrics
from app.modules.metric_evaluation.pipeline_metric_aggregator import aggregate_pipeline_metrics
from app.modules.metric_evaluation.model_ranker import rank_models_and_trials
from app.modules.metric_evaluation.baseline_comparator import compare_against_baselines
from app.modules.metric_evaluation.metric_validator import validate_metric_results
from app.modules.metric_evaluation.result_diagnosis_input_builder import build_result_diagnosis_input
from app.modules.metric_evaluation.builder import (
    build_response,
    build_metric_summary,
    build_summary_response,
)
from app.modules.metric_evaluation.evaluation_artifact_manager import (
    ensure_evaluation_dir,
    save_metric_results,
    save_fold_metrics,
    save_trial_metrics,
    save_pipeline_metrics,
    save_model_ranking,
    save_baseline_comparison,
    save_result_diagnosis_input,
    save_manifest,
)
from app.modules.metric_evaluation.schemas import EvaluationArtifactManifest
from app.modules.metric_evaluation.exceptions import MetricEvaluationNotFoundException
from app.modules.metric_evaluation.enums import MetricEvaluationStatus


class MetricEvaluationService:

    def __init__(self):
        self.repo = MetricEvaluationRepository()

    def create_metric_evaluation(
        self,
        session: Session,
        task_id: str,
        request: MetricEvaluationCreateRequest,
    ) -> MetricEvaluationResponse:
        started_at = datetime.utcnow()
        warnings = []
        me_id = f"me_{uuid.uuid4().hex[:8]}"

        try:
            # Step 1: Build context — validate upstream PipelineExecution
            pe = build_metric_evaluation_context(
                session, task_id, request.pipeline_execution_id,
            )

            # Step 2: Load and validate metric_evaluation_input
            metric_input = load_metric_evaluation_input(
                pe.metric_evaluation_input_json or {},
            )

            task_type = metric_input["task_type"]
            target_column = metric_input["target_column"]
            primary_metric = metric_input["primary_metric"]
            metric_direction = metric_input["metric_direction"]
            trial_results_raw = metric_input["trial_results"]
            prediction_artifact_paths = metric_input["prediction_artifacts"]

            # Step 3: Load prediction artifacts
            pred_frames = load_prediction_artifacts(prediction_artifact_paths)
            trial_fold_map = build_prediction_frame_map(pred_frames, trial_results_raw)

            # Step 4: Build trial info map enriched from execution_json
            # The metric_evaluation_input_json trial_results are lightweight summaries.
            # We pull pipeline_role, model_family, trial_type, params, etc. from
            # the full execution_json (which has pipeline_run_results + full trial_results).
            exec_json = pe.execution_json or {}

            # Build spec_id -> pipeline_role map from pipeline_run_results
            spec_role_map = {}
            spec_family_map = {}
            for pr in exec_json.get("pipeline_run_results", []):
                sid = pr.get("pipeline_spec_id", "")
                if sid:
                    spec_role_map[sid] = pr.get("pipeline_role")
                    spec_family_map[sid] = pr.get("model_family")

            # Build full trial info from execution_json trial_results
            full_trial_map = {}
            for t in exec_json.get("trial_results", []):
                tid = t.get("trial_id", "")
                if tid:
                    full_trial_map[tid] = t

            trial_info_map = {}
            for t in trial_results_raw:
                tid = t.get("trial_id", "")
                if not tid:
                    continue
                ft = full_trial_map.get(tid, {})
                spec_id = ft.get("pipeline_spec_id", "")
                trial_info_map[tid] = {
                    "model_id": t.get("model_id", ft.get("model_id", "")),
                    "pipeline_spec_id": spec_id,
                    "pipeline_run_id": ft.get("pipeline_run_id", ""),
                    "model_family": spec_family_map.get(spec_id) or ft.get("model_family"),
                    "pipeline_role": spec_role_map.get(spec_id) or ft.get("pipeline_role"),
                    "trial_type": ft.get("trial_type"),
                    "params": ft.get("params", {}),
                }

            # Step 5: Evaluate fold-level metrics
            fold_results = evaluate_fold_metrics(
                trial_fold_map, task_type, primary_metric,
            )

            # Step 6: Aggregate trial-level metrics
            trial_results = aggregate_trial_metrics(
                fold_results, trial_info_map, primary_metric,
            )

            # Step 7: Aggregate pipeline/model-level metrics
            pipeline_results = aggregate_pipeline_metrics(trial_results)

            # Step 8: Rank models and trials
            best_trial, best_model_id, best_trial_id, best_pipeline_spec_id, ranking_items = (
                rank_models_and_trials(
                    trial_results, pipeline_results, primary_metric, metric_direction,
                )
            )

            # Step 9: Compare against baselines
            baseline_comparison = compare_against_baselines(
                trial_results, ranking_items, metric_direction,
            )

            # Compute improvement percentages for ranking items
            if baseline_comparison.baseline_available and baseline_comparison.best_baseline_metric_value is not None:
                bl_val = baseline_comparison.best_baseline_metric_value
                for item in ranking_items:
                    if item.primary_metric_value is not None:
                        if metric_direction == "minimize":
                            item.improvement_over_best_baseline = bl_val - item.primary_metric_value
                        else:
                            item.improvement_over_best_baseline = item.primary_metric_value - bl_val
                        if abs(bl_val) > 1e-12:
                            item.improvement_percentage = (
                                (item.improvement_over_best_baseline / abs(bl_val)) * 100
                            )

            # Build metric summary
            metric_summary = build_metric_summary(trial_results, primary_metric, metric_direction)

            # Count stats
            n_ev = sum(1 for t in trial_results if t.status == "evaluated")
            n_fail = sum(1 for t in trial_results if t.status == "failed")
            model_ids = set(t.model_id for t in trial_results if t.status == "evaluated")
            n_models = len(model_ids)

            # Determine status
            if n_ev == 0:
                status = MetricEvaluationStatus.FAILED
            elif n_fail > 0:
                status = MetricEvaluationStatus.PARTIALLY_EVALUATED
            elif warnings:
                status = MetricEvaluationStatus.EVALUATED_WITH_WARNING
            else:
                status = MetricEvaluationStatus.EVALUATED

            # Step 10: Setup artifact directory
            eval_dir = ensure_evaluation_dir(me_id)

            # Save artifacts
            mr_path = save_metric_results(eval_dir, {
                "metric_evaluation_id": me_id,
                "primary_metric": primary_metric,
                "metric_direction": metric_direction,
                "best_trial_id": best_trial_id,
                "best_model_id": best_model_id,
                "metric_summary": metric_summary.model_dump(),
            })
            fm_path = save_fold_metrics(eval_dir, [f.model_dump() for f in fold_results])
            tm_path = save_trial_metrics(eval_dir, [t.model_dump() for t in trial_results])
            pm_path = save_pipeline_metrics(eval_dir, [p.model_dump() for p in pipeline_results])
            rk_path = save_model_ranking(eval_dir, [r.model_dump() for r in ranking_items])
            bl_path = save_baseline_comparison(eval_dir, baseline_comparison.model_dump())

            # Step 11: Build result diagnosis input
            result_diagnosis_input = build_result_diagnosis_input(
                metric_evaluation_id=me_id,
                pipeline_execution_id=pe.id,
                task_id=task_id,
                task_type=task_type,
                primary_metric=primary_metric,
                metric_direction=metric_direction,
                best_trial=best_trial,
                best_model_id=best_model_id,
                model_ranking=ranking_items,
                baseline_comparison=baseline_comparison,
                metric_summary=metric_summary,
                trial_results=trial_results,
                warnings=warnings,
            )

            rd_path = save_result_diagnosis_input(
                eval_dir, result_diagnosis_input.model_dump(),
            )

            artifact_manifest = EvaluationArtifactManifest(
                metric_evaluation_id=me_id,
                pipeline_execution_id=pe.id,
                artifact_dir=eval_dir,
                manifest_path=None,
                metric_results_path=mr_path,
                fold_metrics_path=fm_path,
                trial_metrics_path=tm_path,
                pipeline_metrics_path=pm_path,
                model_ranking_path=rk_path,
                baseline_comparison_path=bl_path,
                result_diagnosis_input_path=rd_path,
            )

            manifest_path = save_manifest(eval_dir, {
                "metric_evaluation_id": me_id,
                "pipeline_execution_id": pe.id,
                "created_at": started_at.isoformat(),
                "primary_metric": primary_metric,
                "metric_direction": metric_direction,
                "best_trial_id": best_trial_id,
                "best_model_id": best_model_id,
                "artifact_versions": {"metric_results": "1.0", "fold_metrics": "1.0"},
            })
            artifact_manifest.manifest_path = manifest_path

            # Step 12: Build response
            finished_at = datetime.utcnow()

            response = build_response(
                metric_evaluation_id=me_id,
                task_id=task_id,
                pipeline_execution_id=pe.id,
                pipeline_generation_id=pe.pipeline_generation_id or "",
                status=status,
                task_type=task_type,
                primary_metric=primary_metric,
                metric_direction=metric_direction,
                n_trials_evaluated=n_ev,
                n_trials_failed=n_fail,
                n_models_evaluated=n_models,
                best_trial_id=best_trial_id,
                best_model_id=best_model_id,
                best_pipeline_spec_id=best_pipeline_spec_id,
                metric_summary=metric_summary,
                trial_metric_results=trial_results,
                pipeline_metric_results=pipeline_results,
                fold_metric_results=fold_results,
                model_ranking=ranking_items,
                baseline_comparison=baseline_comparison,
                metric_validation_result=validate_metric_results(
                    trial_results, ranking_items, baseline_comparison,
                    metric_direction, best_trial_id,
                    result_diagnosis_input.model_dump(),
                ),
                evaluation_artifact_manifest=artifact_manifest,
                result_diagnosis_input=result_diagnosis_input,
                warnings=warnings,
                error_message=None,
                created_at=started_at,
                updated_at=finished_at,
            )

            # Step 13: Persist to database
            db_record = MetricEvaluation(
                id=me_id,
                task_id=task_id,
                pipeline_execution_id=pe.id,
                pipeline_generation_id=pe.pipeline_generation_id,
                status=status,
                task_type=task_type,
                target_column=target_column,
                primary_metric=primary_metric,
                metric_direction=metric_direction,
                n_trials_evaluated=n_ev,
                n_trials_failed=n_fail,
                n_models_evaluated=n_models,
                best_trial_id=best_trial_id,
                best_model_id=best_model_id,
                best_pipeline_spec_id=best_pipeline_spec_id,
                best_primary_metric_value=(
                    best_trial.primary_metric_mean if best_trial else None
                ),
                ready_for_result_diagnosis=result_diagnosis_input.ready_for_result_diagnosis,
                evaluation_artifact_dir=eval_dir,
                evaluation_json=response.model_dump(mode="json"),
                result_diagnosis_input_json=result_diagnosis_input.model_dump(mode="json"),
                metric_summary_json=metric_summary.model_dump(mode="json"),
                model_ranking_json=[r.model_dump() for r in ranking_items],
                error_message=None,
                created_at=started_at,
                updated_at=finished_at,
            )
            self.repo.create(session, db_record)

            return response

        except Exception as e:
            finished_at = datetime.utcnow()
            error_msg = str(e)
            traceback_str = traceback.format_exc()

            try:
                fail_record = MetricEvaluation(
                    id=me_id,
                    task_id=task_id,
                    pipeline_execution_id=request.pipeline_execution_id or "",
                    pipeline_generation_id="",
                    status=MetricEvaluationStatus.FAILED,
                    error_message=error_msg,
                    created_at=started_at,
                    updated_at=finished_at,
                )
                self.repo.create(session, fail_record)
            except Exception:
                pass

            raise

    def get_metric_evaluation(
        self, session: Session, me_id: str,
    ) -> MetricEvaluationResponse:
        record = self.repo.get_by_id(session, me_id)
        if not record:
            raise MetricEvaluationNotFoundException(
                f"MetricEvaluation '{me_id}' not found."
            )
        if record.evaluation_json:
            return MetricEvaluationResponse(**record.evaluation_json)
        return self._record_to_response(record)

    def get_latest_by_task_id(
        self, session: Session, task_id: str,
    ) -> MetricEvaluationResponse:
        record = self.repo.get_latest_by_task_id(session, task_id)
        if not record:
            raise MetricEvaluationNotFoundException(
                f"No MetricEvaluation found for task '{task_id}'."
            )
        if record.evaluation_json:
            return MetricEvaluationResponse(**record.evaluation_json)
        return self._record_to_response(record)

    def rerun_metric_evaluation(
        self, session: Session, task_id: str,
    ) -> MetricEvaluationResponse:
        return self.create_metric_evaluation(
            session, task_id,
            MetricEvaluationCreateRequest(force_rerun=True),
        )

    def get_summary(
        self, session: Session, me_id: str,
    ) -> MetricEvaluationSummaryResponse:
        record = self.repo.get_by_id(session, me_id)
        if not record:
            raise MetricEvaluationNotFoundException(
                f"MetricEvaluation '{me_id}' not found."
            )
        return build_summary_response(record)

    def get_ranking(self, session: Session, me_id: str) -> list:
        record = self.repo.get_by_id(session, me_id)
        if not record:
            raise MetricEvaluationNotFoundException(
                f"MetricEvaluation '{me_id}' not found."
            )
        if record.evaluation_json:
            return record.evaluation_json.get("model_ranking", [])
        return []

    def get_trials(self, session: Session, me_id: str) -> list:
        record = self.repo.get_by_id(session, me_id)
        if not record:
            raise MetricEvaluationNotFoundException(
                f"MetricEvaluation '{me_id}' not found."
            )
        if record.evaluation_json:
            return record.evaluation_json.get("trial_metric_results", [])
        return []

    def get_folds(self, session: Session, me_id: str) -> list:
        record = self.repo.get_by_id(session, me_id)
        if not record:
            raise MetricEvaluationNotFoundException(
                f"MetricEvaluation '{me_id}' not found."
            )
        if record.evaluation_json:
            return record.evaluation_json.get("fold_metric_results", [])
        return []

    def get_result_diagnosis_input(self, session: Session, me_id: str) -> dict:
        record = self.repo.get_by_id(session, me_id)
        if not record:
            raise MetricEvaluationNotFoundException(
                f"MetricEvaluation '{me_id}' not found."
            )
        if record.result_diagnosis_input_json:
            return record.result_diagnosis_input_json
        return {}

    def _record_to_response(self, record: MetricEvaluation) -> MetricEvaluationResponse:
        return MetricEvaluationResponse(
            metric_evaluation_id=record.id,
            task_id=record.task_id,
            pipeline_execution_id=record.pipeline_execution_id,
            pipeline_generation_id=record.pipeline_generation_id,
            status=record.status or "unknown",
            task_type=record.task_type,
            primary_metric=record.primary_metric,
            metric_direction=record.metric_direction or "minimize",
            n_trials_evaluated=record.n_trials_evaluated or 0,
            n_trials_failed=record.n_trials_failed or 0,
            n_models_evaluated=record.n_models_evaluated or 0,
            best_trial_id=record.best_trial_id,
            best_model_id=record.best_model_id,
            best_pipeline_spec_id=record.best_pipeline_spec_id,
            ready_for_result_diagnosis=record.ready_for_result_diagnosis or False,
            error_message=record.error_message,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
