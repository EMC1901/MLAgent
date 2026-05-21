import uuid
import logging
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any
from sqlmodel import Session

from app.modules.final_output.model import FinalOutput
from app.modules.final_output.repository import FinalOutputRepository
from app.modules.final_output.schemas import (
    FinalOutputCreateRequest,
    FinalOutputResponse,
)
from app.modules.final_output.enums import FinalOutputStatus

from app.modules.final_output.context_builder import build_final_output_context
from app.modules.final_output.final_output_input_loader import load_final_output_input
from app.modules.final_output.workflow_trace_collector import collect_workflow_trace
from app.modules.final_output.final_artifact_resolver import resolve_final_artifacts
from app.modules.final_output.reproducibility_summary_builder import build_reproducibility_summary
from app.modules.final_output.final_summary_builder import (
    build_final_summaries,
    build_summary_dicts,
)
from app.modules.final_output.llm_report_prompt_builder import build_llm_report_context
from app.modules.final_output.llm_report_writer import LLMReportWriter
from app.modules.final_output.llm_report_parser import parse_llm_report
from app.modules.final_output.llm_report_validator import validate_llm_report
from app.modules.final_output.llm_report_normalizer import normalize_llm_report
from app.modules.final_output.report_renderer import (
    build_final_report_from_llm,
    build_fallback_report,
    render_json_report,
    render_markdown_report,
)
from app.modules.final_output.output_package_builder import (
    build_output_package,
    build_download_links,
)
from app.modules.final_output.final_output_artifact_manager import save_final_output_artifacts
from app.modules.final_output.builder import build_response

from app.modules.final_output.exceptions import (
    FinalOutputNotFoundException,
)

logger = logging.getLogger(__name__)


class FinalOutputService:

    def __init__(self):
        self.repo = FinalOutputRepository()
        self.llm_report_writer = LLMReportWriter()

    def create_final_output(
        self,
        session: Session,
        task_id: str,
        request: FinalOutputCreateRequest,
    ) -> FinalOutputResponse:
        warnings_list: list = []

        # Step 1: Build context - validate upstream InterpretabilityAnalysis
        ia = build_final_output_context(
            session, task_id, request.interpretability_analysis_id
        )

        # Early return if not force_rerun and existing output is available
        if not request.force_rerun:
            existing = self.repo.get_latest_by_task_id(session, task_id)
            if (
                existing
                and existing.interpretability_analysis_id == ia.id
                and existing.status
                in (FinalOutputStatus.GENERATED, FinalOutputStatus.GENERATED_WITH_WARNING)
            ):
                return self.get_final_output(session, existing.id)

        # Step 2: Load final output input
        fo_input = load_final_output_input(ia)

        # Step 3: Collect workflow trace
        try:
            workflow_trace = collect_workflow_trace(
                session,
                task_id,
                task_spec_id=_safe_get_id(ia.task_id, "task_specification"),
                task_interp_id=None,
                dataset_profile_id=None,
                workflow_plan_id=None,
                feature_engineering_id=None,
                feature_preprocessing_id=None,
                model_search_context_id=None,
                pipeline_generation_id=None,
                pipeline_execution_id=None,
                metric_evaluation_id=None,
                result_diagnosis_id=None,
                workflow_refinement_id=None,
                final_pipeline_selection_id=fo_input.final_pipeline_selection_id,
                interpretability_analysis_id=ia.id,
            )
        except Exception as e:
            logger.warning("Workflow trace collection failed: %s", str(e))
            warnings_list.append(f"Workflow trace: {str(e)}")
            from app.modules.final_output.schemas import WorkflowTraceSummary
            workflow_trace = WorkflowTraceSummary(
                final_pipeline_selection_id=fo_input.final_pipeline_selection_id,
                interpretability_analysis_id=ia.id,
            )

        # Step 4: Resolve final artifacts
        try:
            artifact_manifest = resolve_final_artifacts(session, fo_input)
        except Exception as e:
            logger.warning("Artifact resolution failed: %s", str(e))
            warnings_list.append(f"Artifact resolution: {str(e)}")
            from app.modules.final_output.schemas import FinalArtifactManifest
            artifact_manifest = FinalArtifactManifest(
                artifact_integrity_status="partial",
                warnings=[str(e)],
            )

        # Step 5: Build reproducibility summary
        try:
            reproducibility_summary = build_reproducibility_summary(
                fo_input,
                model_ready_matrix_path=artifact_manifest.model_artifact_path,
            )
        except Exception as e:
            logger.warning("Reproducibility summary build failed: %s", str(e))
            warnings_list.append(f"Reproducibility summary: {str(e)}")
            from app.modules.final_output.schemas import ReproducibilitySummary
            reproducibility_summary = ReproducibilitySummary(
                model_artifact_path=fo_input.model_artifact_path,
            )

        # Step 6: Build system fact summaries
        summaries = build_final_summaries(fo_input, interpretability_analysis_id=ia.id)
        summary_dicts = build_summary_dicts(summaries)

        # Step 7: Build LLM report context
        llm_context = build_llm_report_context(
            task_summary={"task_type": "", "target_column": "", "primary_metric": fo_input.metric_summary.get("primary_metric", "")},
            dataset_summary={"source": "", "target_column": "", "feature_count": len(fo_input.global_feature_importance)},
            workflow_summary={"steps_completed": 15, "iterations": workflow_trace.iteration_count, "refinement_performed": workflow_trace.iteration_count > 0},
            feature_summary={"strategies": [], "feature_count": len(fo_input.global_feature_importance)},
            model_search_summary={"search_method": "auto", "models_evaluated": 0, "hpo_method": "auto"},
            final_model={
                "model_id": fo_input.final_model_id,
                "trial_id": fo_input.final_trial_id,
                "model_family": fo_input.final_model_id,
            },
            final_metrics={
                "primary_metric": fo_input.metric_summary.get("primary_metric", ""),
                "primary_metric_value": fo_input.metric_summary.get("primary_metric_value"),
            },
            selection_summary=fo_input.selection_summary,
            interpretability={"top_features": summaries.interpretability_summary.top_features if summaries.interpretability_summary else []},
            shap_summary=fo_input.shap_summary,
            material_insight=fo_input.material_insight_summary,
            reproducibility=reproducibility_summary.model_dump(),
            artifact_list=artifact_manifest.model_dump(),
            warnings_list=warnings_list,
        )

        # Step 8-12: LLM Report Writer
        llm_used = False
        llm_report = None
        final_report = None
        llm_confidence = None
        llm_raw_request = None
        llm_raw_response = None

        if request.use_llm_report_writer:
            try:
                llm_raw_request = llm_context
                llm_result = self.llm_report_writer.write_report(
                    llm_context["system_prompt"], llm_context["user_message"]
                )
                raw_response = llm_result.get("raw_response", "")
                llm_raw_response = raw_response

                llm_report = parse_llm_report(raw_response)
                validation = validate_llm_report(llm_report, raw_response)

                if validation.is_valid:
                    llm_report = normalize_llm_report(llm_report)
                    final_report = build_final_report_from_llm(llm_report)
                    llm_used = True
                    llm_confidence = llm_report.confidence_level if llm_report else None
                else:
                    logger.warning("LLM report validation failed: %s", validation.issues)
                    warnings_list.append(
                        f"LLM report validation failed: {'; '.join(validation.issues)}"
                    )
                    final_report = build_fallback_report(
                        final_model_id=fo_input.final_model_id,
                        primary_metric=fo_input.metric_summary.get("primary_metric", ""),
                        primary_metric_value=fo_input.metric_summary.get("primary_metric_value"),
                    )
                    llm_report = None

            except Exception as e:
                logger.error("LLM report writer failed: %s", str(e))
                warnings_list.append(f"LLM report writer: {str(e)}")
                final_report = build_fallback_report(
                    final_model_id=fo_input.final_model_id,
                    primary_metric=fo_input.metric_summary.get("primary_metric", ""),
                    primary_metric_value=fo_input.metric_summary.get("primary_metric_value"),
                )
        else:
            final_report = build_fallback_report(
                final_model_id=fo_input.final_model_id,
                primary_metric=fo_input.metric_summary.get("primary_metric", ""),
                primary_metric_value=fo_input.metric_summary.get("primary_metric_value"),
            )

        # Step 13: Determine status
        status = FinalOutputStatus.GENERATED
        if warnings_list:
            status = FinalOutputStatus.GENERATED_WITH_WARNING

        # Step 14: Generate IDs and directory
        fo_id = f"fo_{uuid.uuid4().hex[:8]}"
        artifact_dir = f"/app/artifacts/final_output/{fo_id}"

        # Step 15: Render reports
        json_report_path = f"{artifact_dir}/final_report.json"
        markdown_report_path = f"{artifact_dir}/final_report.md"
        workflow_trace_path = f"{artifact_dir}/workflow_trace.json"
        reproducibility_path = f"{artifact_dir}/reproducibility_summary.json"

        try:
            render_json_report(final_report, json_report_path)
        except Exception as e:
            logger.warning("JSON report render failed: %s", str(e))
            warnings_list.append(f"JSON report render: {str(e)}")

        try:
            render_markdown_report(final_report, markdown_report_path)
        except Exception as e:
            logger.warning("Markdown report render failed: %s", str(e))
            warnings_list.append(f"Markdown report render: {str(e)}")

        # Step 16: Build output package
        try:
            package_manifest = build_output_package(
                final_output_id=fo_id,
                artifact_dir=artifact_dir,
                artifact_manifest=artifact_manifest,
                json_report_path=json_report_path,
                markdown_report_path=markdown_report_path,
                workflow_trace_path=workflow_trace_path,
                reproducibility_summary_path=reproducibility_path,
            )
        except Exception as e:
            logger.warning("Output package build failed: %s", str(e))
            warnings_list.append(f"Output package: {str(e)}")
            from app.modules.final_output.schemas import OutputPackageManifest
            package_manifest = OutputPackageManifest(
                output_package_id=fo_id,
                package_root_dir=artifact_dir,
                package_status="partial",
            )

        # Step 17: Build download links
        download_links = build_download_links(
            final_output_id=fo_id,
            artifact_dir=artifact_dir,
            artifact_manifest=artifact_manifest,
            package_manifest=package_manifest,
        )

        # Step 18: Determine ready_for_delivery
        ready_for_delivery = bool(
            final_report
            and json_report_path
            and artifact_manifest.model_artifact_path
        )

        # Step 19: Build final output JSON
        final_output_json = {
            **summary_dicts,
            "workflow_trace_summary": workflow_trace.model_dump(),
            "reproducibility_summary": reproducibility_summary.model_dump(),
            "artifact_manifest": artifact_manifest.model_dump(),
            "output_package_manifest": package_manifest.model_dump(),
            "download_links": download_links.model_dump(),
            "ready_for_delivery": ready_for_delivery,
        }

        # Step 20: Persist
        now = datetime.now(timezone.utc)

        record = FinalOutput(
            id=fo_id,
            task_id=task_id,
            interpretability_analysis_id=ia.id,
            final_pipeline_selection_id=fo_input.final_pipeline_selection_id,
            status=status,
            report_profile=request.report_profile,
            final_model_id=fo_input.final_model_id,
            final_trial_id=fo_input.final_trial_id,
            primary_metric=fo_input.metric_summary.get("primary_metric", ""),
            primary_metric_value=fo_input.metric_summary.get("primary_metric_value"),
            ready_for_delivery=ready_for_delivery,
            final_output_json=_make_json_safe(final_output_json),
            final_report_json=_make_json_safe(final_report.model_dump()) if final_report else None,
            llm_report_json=_make_json_safe(llm_report.model_dump()) if llm_report else None,
            workflow_trace_json=_make_json_safe(workflow_trace.model_dump()),
            reproducibility_summary_json=_make_json_safe(reproducibility_summary.model_dump()),
            artifact_manifest_json=_make_json_safe(artifact_manifest.model_dump()),
            output_package_manifest_json=_make_json_safe(package_manifest.model_dump()),
            download_links_json=_make_json_safe(download_links.model_dump()),
            llm_used=llm_used,
            llm_confidence_level=llm_confidence,
            llm_request_json=_make_json_safe(llm_raw_request),
            llm_response_json=_make_json_safe({"raw_response": llm_raw_response}) if llm_raw_response else None,
            artifact_dir=artifact_dir,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        record = self.repo.create(session, record)

        # Step 21: Save final output artifacts
        try:
            save_final_output_artifacts(
                final_output_id=fo_id,
                final_output_result=_safe_dump(record),
                final_report=final_report.model_dump() if final_report else {},
                llm_report=llm_report.model_dump() if llm_report else None,
                workflow_trace=workflow_trace.model_dump(),
                reproducibility_summary=reproducibility_summary.model_dump(),
                artifact_manifest=artifact_manifest.model_dump(),
                output_package_manifest=package_manifest.model_dump(),
            )
        except Exception as e:
            logger.warning("Artifact save failed: %s", str(e))
            warnings_list.append(f"Artifact save: {str(e)}")

        return build_response(record=record, warnings=warnings_list)

    def get_final_output(
        self, session: Session, fo_id: str
    ) -> FinalOutputResponse:
        record = self.repo.get_by_id(session, fo_id)
        if not record:
            raise FinalOutputNotFoundException(
                f"FinalOutput {fo_id} not found."
            )
        return self._record_to_response(record)

    def get_latest_by_task_id(
        self, session: Session, task_id: str
    ) -> FinalOutputResponse:
        record = self.repo.get_latest_by_task_id(session, task_id)
        if not record:
            raise FinalOutputNotFoundException(
                f"No FinalOutput found for task {task_id}."
            )
        return self._record_to_response(record)

    def rerun_final_output(
        self, session: Session, task_id: str
    ) -> FinalOutputResponse:
        request = FinalOutputCreateRequest(force_rerun=True)
        return self.create_final_output(session, task_id, request)

    def get_report(self, session: Session, fo_id: str) -> dict:
        record = self.repo.get_by_id(session, fo_id)
        if not record:
            raise FinalOutputNotFoundException(f"FinalOutput {fo_id} not found.")
        return record.final_report_json or {}

    def get_workflow_trace(self, session: Session, fo_id: str) -> dict:
        record = self.repo.get_by_id(session, fo_id)
        if not record:
            raise FinalOutputNotFoundException(f"FinalOutput {fo_id} not found.")
        return record.workflow_trace_json or {}

    def get_artifact_manifest(self, session: Session, fo_id: str) -> dict:
        record = self.repo.get_by_id(session, fo_id)
        if not record:
            raise FinalOutputNotFoundException(f"FinalOutput {fo_id} not found.")
        return record.artifact_manifest_json or {}

    def get_download_links(self, session: Session, fo_id: str) -> dict:
        record = self.repo.get_by_id(session, fo_id)
        if not record:
            raise FinalOutputNotFoundException(f"FinalOutput {fo_id} not found.")
        return record.download_links_json or {}

    def _record_to_response(self, record: FinalOutput) -> FinalOutputResponse:
        return build_response(record=record)


def _safe_get_id(source_id: str, module_name: str) -> Optional[str]:
    return source_id


def _make_json_safe(obj: Any) -> Any:
    """Recursively convert non-JSON-serializable objects (datetime, etc.) to safe types."""
    if obj is None:
        return None
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if hasattr(obj, "model_dump"):
        return _make_json_safe(obj.model_dump())
    if isinstance(obj, dict):
        return {k: _make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_json_safe(item) for item in obj]
    if isinstance(obj, (int, float, str, bool)):
        return obj
    return str(obj)


def _safe_dump(obj) -> Optional[dict]:
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return _make_json_safe(obj.model_dump())
    if isinstance(obj, list):
        return [_safe_dump(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _safe_dump(v) for k, v in obj.items()}
    return obj
