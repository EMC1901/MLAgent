import json
import os
import sys
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


def _diag(msg, *args):
    formatted = msg % args if args else msg
    print(f"DIAG     [fo-svc] {formatted}", file=sys.stderr, flush=True)

from app.modules.final_output.context_builder import build_final_output_context
from app.modules.final_output.final_output_input_loader import load_final_output_input
from app.modules.final_output.workflow_trace_collector import collect_workflow_trace
from app.modules.final_output.final_artifact_resolver import resolve_final_artifacts
from app.modules.final_output.reproducibility_summary_builder import build_reproducibility_summary
from app.modules.final_output.final_summary_builder import (
    build_final_summaries,
    build_summary_dicts,
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

_TOPIC_FILES = [
    ("01_task_specification", "task_specification"),
    ("02_dataset_profile", "dataset_profile"),
    ("03_workflow_plan", "workflow_plan"),
    ("04_model_ready_feature_summary", "model_ready_feature_summary"),
    ("05_candidate_model_plan", "candidate_model_plan"),
    ("06_hpo_plan", "hpo_plan"),
    ("07_pipeline_specs", "pipeline_specs"),
    ("08_training_evaluation_results", "training_evaluation_results"),
    ("09_interpretability_analysis", "interpretability_analysis"),
    ("10_final_output_package", "final_output_package"),
]


class FinalOutputService:

    def __init__(self):
        self.repo = FinalOutputRepository()

    def create_final_output(
        self,
        session: Session,
        task_id: str,
        request: FinalOutputCreateRequest,
    ) -> FinalOutputResponse:
        _diag("=== create_final_output START task_id=%s force_rerun=%s ===", task_id, request.force_rerun)
        warnings_list: list = []

        # Step 1: Validate upstream InterpretabilityAnalysis
        _diag("Step 1: Building context / validating InterpretabilityAnalysis ...")
        ia = build_final_output_context(
            session, task_id, request.interpretability_analysis_id
        )
        _diag("Step 1: OK — ia.id=%s ia.status=%s", ia.id, ia.status)

        # Early return if not force_rerun and existing output is available
        if not request.force_rerun:
            existing = self.repo.get_latest_by_task_id(session, task_id)
            if (
                existing
                and existing.interpretability_analysis_id == ia.id
                and existing.status
                in (FinalOutputStatus.GENERATED, FinalOutputStatus.GENERATED_WITH_WARNING)
            ):
                existing_topics = (existing.final_output_json or {}).get("topic_files")
                if existing_topics and len(existing_topics) >= 9:
                    _diag("Step 1b: Early return — existing output id=%s (has %d topic files)",
                          existing.id, len(existing_topics))
                    return self.get_final_output(session, existing.id)
                else:
                    _diag("Step 1b: Existing output id=%s is old format (no topic_files), regenerating ...",
                          existing.id)

        # Step 2: Load final output input
        _diag("Step 2: Loading final output input ...")
        fo_input = load_final_output_input(ia)
        _diag("Step 2: OK — model_id=%s trial_id=%s", fo_input.final_model_id, fo_input.final_trial_id)

        # Step 3: Collect full workflow trace from all upstream modules
        _diag("Step 3: Collecting workflow trace from upstream modules ...")
        try:
            workflow_trace = collect_workflow_trace(
                session, task_id, interpretability_analysis_id=ia.id,
            )
        except Exception as e:
            logger.warning("Workflow trace collection failed: %s", str(e))
            warnings_list.append(f"Workflow trace: {str(e)}")
            from app.modules.final_output.schemas import WorkflowTraceSummary
            workflow_trace = WorkflowTraceSummary(
                interpretability_analysis_id=ia.id,
            )
        _diag("Step 3: Done — trace has %d topics in workflow_trace_artifacts",
              len(workflow_trace.workflow_trace_artifacts or {}))

        # Step 4: Resolve final artifacts
        _diag("Step 4: Resolving final artifacts (model, predictions, etc.) ...")
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

        # Step 6: Build system fact summaries (model / metric / interpretability)
        summaries = build_final_summaries(fo_input, interpretability_analysis_id=ia.id)
        summary_dicts = build_summary_dicts(summaries)

        # Step 7: Generate IDs and directory
        fo_id = f"fo_{uuid.uuid4().hex[:8]}"
        artifact_dir = f"/app/artifacts/final_output/{fo_id}"
        _diag("Step 7: Generated fo_id=%s artifact_dir=%s", fo_id, artifact_dir)

        # Step 8: Write topic report files
        _diag("Step 8: Writing topic report files ...")
        topic_file_paths: Dict[str, str] = {}
        topic_file_list: List[Dict[str, str]] = []
        try:
            os.makedirs(artifact_dir, exist_ok=True)
            _diag("Step 8: artifact_dir created: %s", artifact_dir)
            for filename, topic_key in _TOPIC_FILES:
                data = (workflow_trace.workflow_trace_artifacts or {}).get(topic_key)
                if data is None:
                    data = {}
                file_path = os.path.join(artifact_dir, f"{filename}.json")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                topic_file_paths[topic_key] = file_path
                topic_file_list.append({
                    "file": f"{filename}.json",
                    "topic": topic_key,
                })
                data_keys = list(data.keys()) if isinstance(data, dict) else "not-a-dict"
                _diag("Step 8: wrote %s  keys=%s", f"{filename}.json", data_keys)
                logger.info("Wrote topic file: %s", file_path)

            # Patch the final_output_package topic to list all generated files
            final_pkg = (workflow_trace.workflow_trace_artifacts or {}).get("final_output_package") or {}
            final_pkg["status"] = "generated"
            final_pkg["generated_files"] = topic_file_list
            final_pkg["artifact_dir"] = artifact_dir
            final_pkg["final_output_id"] = fo_id
            workflow_trace.workflow_trace_artifacts["final_output_package"] = final_pkg

            # Re-write the final_output_package file with updated content
            pkg_path = topic_file_paths.get("final_output_package")
            if pkg_path:
                with open(pkg_path, "w", encoding="utf-8") as f:
                    json.dump(final_pkg, f, indent=2, ensure_ascii=False, default=str)

            # Update artifact manifest with topic files
            artifact_manifest.final_report_json_path = topic_file_paths.get("task_specification", "")
            artifact_manifest.final_report_md_path = ""
            artifact_manifest.workflow_trace_path = os.path.join(artifact_dir, "workflow_trace.json")
            artifact_manifest.reproducibility_summary_path = os.path.join(artifact_dir, "reproducibility_summary.json")
            artifact_manifest.manifest_path = os.path.join(artifact_dir, "manifest.json")

        except Exception as e:
            logger.warning("Topic file writing failed: %s", str(e))
            warnings_list.append(f"Topic file writing: {str(e)}")
        _diag("Step 8: Done — wrote %d topic files to %s", len(topic_file_list), artifact_dir)

        # Step 9: Write workflow trace & reproducibility summary files
        _diag("Step 9: Writing workflow trace & reproducibility summary ...")
        workflow_trace_path = os.path.join(artifact_dir, "workflow_trace.json")
        reproducibility_path = os.path.join(artifact_dir, "reproducibility_summary.json")
        try:
            with open(workflow_trace_path, "w", encoding="utf-8") as f:
                json.dump(_make_json_safe(workflow_trace.model_dump()), f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.warning("Workflow trace write failed: %s", str(e))
        try:
            with open(reproducibility_path, "w", encoding="utf-8") as f:
                json.dump(_make_json_safe(reproducibility_summary.model_dump()), f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.warning("Reproducibility summary write failed: %s", str(e))

        # Step 10: Determine status
        status = FinalOutputStatus.GENERATED
        if warnings_list:
            status = FinalOutputStatus.GENERATED_WITH_WARNING
        _diag("Step 10: status=%s warnings=%d", status, len(warnings_list))

        # Step 11: Build output package
        _diag("Step 11: Building output package ...")
        try:
            package_manifest = build_output_package(
                final_output_id=fo_id,
                artifact_dir=artifact_dir,
                artifact_manifest=artifact_manifest,
                json_report_path=topic_file_paths.get("task_specification", ""),
                markdown_report_path="",
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

        # Step 12: Build download links
        download_links = build_download_links(
            final_output_id=fo_id,
            artifact_dir=artifact_dir,
            artifact_manifest=artifact_manifest,
            package_manifest=package_manifest,
        )

        # Step 13: Determine ready_for_delivery
        ready_for_delivery = bool(
            len(topic_file_list) >= 9
            and artifact_manifest.model_artifact_path
        )
        _diag("Step 13: ready_for_delivery=%s topic_files=%d model_artifact=%s",
              ready_for_delivery, len(topic_file_list), bool(artifact_manifest.model_artifact_path))

        # Step 14: Build final output JSON
        _diag("Step 14: Building final output JSON ...")
        final_output_json = {
            **summary_dicts,
            "workflow_trace_summary": workflow_trace.model_dump(),
            "reproducibility_summary": reproducibility_summary.model_dump(),
            "artifact_manifest": artifact_manifest.model_dump(),
            "output_package_manifest": package_manifest.model_dump(),
            "download_links": download_links.model_dump(),
            "topic_files": topic_file_list,
            "ready_for_delivery": ready_for_delivery,
        }

        # Step 15: Persist
        _diag("Step 15: Persisting to database ...")
        now = datetime.now(timezone.utc)

        record = FinalOutput(
            id=fo_id,
            task_id=task_id,
            interpretability_analysis_id=ia.id,
            status=status,
            report_profile=request.report_profile,
            final_model_id=fo_input.final_model_id,
            final_trial_id=fo_input.final_trial_id,
            primary_metric=fo_input.metric_summary.get("primary_metric", ""),
            primary_metric_value=fo_input.metric_summary.get("primary_metric_value"),
            ready_for_delivery=ready_for_delivery,
            final_output_json=_make_json_safe(final_output_json),
            final_report_json=None,
            llm_report_json=None,
            workflow_trace_json=_make_json_safe(workflow_trace.model_dump()),
            reproducibility_summary_json=_make_json_safe(reproducibility_summary.model_dump()),
            artifact_manifest_json=_make_json_safe(artifact_manifest.model_dump()),
            output_package_manifest_json=_make_json_safe(package_manifest.model_dump()),
            download_links_json=_make_json_safe(download_links.model_dump()),
            llm_used=False,
            llm_confidence_level=None,
            llm_request_json=None,
            llm_response_json=None,
            artifact_dir=artifact_dir,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        record = self.repo.create(session, record)
        _diag("Step 15: Persisted — record.id=%s", record.id)

        # Step 16: Save final output artifacts (manifest, etc.)
        _diag("Step 16: Saving final output artifacts ...")
        try:
            save_final_output_artifacts(
                final_output_id=fo_id,
                final_output_result=_safe_dump(record),
                final_report={},
                llm_report=None,
                workflow_trace=workflow_trace.model_dump(),
                reproducibility_summary=reproducibility_summary.model_dump(),
                artifact_manifest=artifact_manifest.model_dump(),
                output_package_manifest=package_manifest.model_dump(),
            )
        except Exception as e:
            logger.warning("Artifact save failed: %s", str(e))
            warnings_list.append(f"Artifact save: {str(e)}")

        _diag("=== create_final_output DONE: fo_id=%s status=%s topic_files=%d warnings=%d ===",
              fo_id, status, len(topic_file_list), len(warnings_list))
        return build_response(record=record, warnings=warnings_list)

    # ── Read methods ────────────────────────────────────────────────

    def get_final_output(
        self, session: Session, fo_id: str
    ) -> FinalOutputResponse:
        record = self.repo.get_by_id(session, fo_id)
        if not record:
            raise FinalOutputNotFoundException(f"FinalOutput {fo_id} not found.")
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

    def download_artifact_zip(self, session: Session, fo_id: str) -> str:
        import zipfile

        _diag("download_artifact_zip: fo_id=%s", fo_id)
        record = self.repo.get_by_id(session, fo_id)
        if not record:
            _diag("download_artifact_zip: record NOT FOUND for %s", fo_id)
            raise FinalOutputNotFoundException(f"FinalOutput {fo_id} not found.")

        artifact_dir = record.artifact_dir
        _diag("download_artifact_zip: artifact_dir=%s", artifact_dir)
        if not artifact_dir or not os.path.isdir(artifact_dir):
            _diag("download_artifact_zip: artifact_dir NOT FOUND or not a directory")
            raise FinalOutputNotFoundException(
                f"Artifact directory not found for FinalOutput {fo_id}."
            )

        # Only include: topic files, workflow_trace, reproducibility_summary, package/ refs
        _keep_patterns = [
            "01_task_specification.json", "02_dataset_profile.json",
            "03_workflow_plan.json", "04_model_ready_feature_summary.json",
            "05_candidate_model_plan.json", "06_hpo_plan.json",
            "07_pipeline_specs.json", "08_training_evaluation_results.json",
            "09_interpretability_analysis.json", "10_final_output_package.json",
            "workflow_trace.json", "reproducibility_summary.json",
        ]
        _keep_dirs = ["package"]

        zip_path = os.path.join(artifact_dir, f"{fo_id}_package.zip")
        file_count = 0
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(artifact_dir):
                for fname in files:
                    if fname.endswith(".zip"):
                        continue
                    file_path = os.path.join(root, fname)
                    arcname = os.path.relpath(file_path, artifact_dir).replace("\\", "/")
                    # Include only whitelisted files and package/ subdirectory
                    include = fname in _keep_patterns
                    if not include:
                        for keep_dir in _keep_dirs:
                            if arcname.startswith(keep_dir + "/"):
                                include = True
                                break
                    if not include:
                        _diag("download_artifact_zip: skipped %s", arcname)
                        continue
                    zf.write(file_path, arcname)
                    _diag("download_artifact_zip: added %s", arcname)
                    file_count += 1

        _diag("download_artifact_zip: created %s (%d files)", zip_path, file_count)
        logger.info("Created download zip: %s (%d files)", zip_path, file_count)
        return zip_path

    def _record_to_response(self, record: FinalOutput) -> FinalOutputResponse:
        return build_response(record=record)


# ── JSON-safe helpers ─────────────────────────────────────────────

def _make_json_safe(obj: Any) -> Any:
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
