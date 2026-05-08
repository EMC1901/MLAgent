import os
import json
import logging
from typing import Dict, Any, List

from app.modules.final_output.schemas import (
    OutputPackageManifest,
    DownloadLinks,
    FinalArtifactManifest,
)
from app.modules.final_output.exceptions import OutputPackageBuildException

logger = logging.getLogger(__name__)

PACKAGE_BASE_DIR = "/app/artifacts/final_output"


def build_output_package(
    final_output_id: str,
    artifact_dir: str,
    artifact_manifest: FinalArtifactManifest,
    json_report_path: str,
    markdown_report_path: str,
    workflow_trace_path: str,
    reproducibility_summary_path: str,
) -> OutputPackageManifest:
    try:
        package_dir = os.path.join(artifact_dir, "package")
        reports_dir = os.path.join(package_dir, "reports")
        model_dir = os.path.join(package_dir, "model")
        predictions_dir = os.path.join(package_dir, "predictions")
        interpretability_dir = os.path.join(package_dir, "interpretability")

        for d in [package_dir, reports_dir, model_dir, predictions_dir, interpretability_dir]:
            os.makedirs(d, exist_ok=True)

        manifest = OutputPackageManifest(
            output_package_id=final_output_id,
            package_root_dir=artifact_dir,
            json_report_path=json_report_path,
            markdown_report_path=markdown_report_path,
            model_artifact_path=artifact_manifest.model_artifact_path,
            prediction_artifact_paths=artifact_manifest.prediction_artifact_paths,
            interpretability_artifact_paths=artifact_manifest.interpretability_artifact_paths,
            workflow_trace_path=workflow_trace_path,
            manifest_path=os.path.join(artifact_dir, "manifest.json"),
            package_zip_path=None,
            package_status="complete",
        )

        # Write artifact references in package subdirs
        _write_ref_file(
            os.path.join(model_dir, "model_artifact_ref.json"),
            {"model_artifact_path": artifact_manifest.model_artifact_path},
        )
        _write_ref_file(
            os.path.join(predictions_dir, "prediction_artifacts_ref.json"),
            {"prediction_artifact_paths": artifact_manifest.prediction_artifact_paths},
        )
        _write_ref_file(
            os.path.join(interpretability_dir, "interpretability_artifacts_ref.json"),
            artifact_manifest.interpretability_artifact_paths,
        )

        logger.info("Output package built at %s", artifact_dir)
        return manifest

    except Exception as e:
        logger.error("Failed to build output package: %s", str(e))
        raise OutputPackageBuildException(str(e))


def build_download_links(
    final_output_id: str,
    artifact_dir: str,
    artifact_manifest: FinalArtifactManifest,
    package_manifest: OutputPackageManifest,
) -> DownloadLinks:
    return DownloadLinks(
        json_report=package_manifest.json_report_path,
        markdown_report=package_manifest.markdown_report_path,
        manifest=package_manifest.manifest_path,
        workflow_trace=package_manifest.workflow_trace_path,
        reproducibility_summary=os.path.join(artifact_dir, "reproducibility_summary.json"),
        output_package_dir=artifact_dir,
        model_artifact_ref=artifact_manifest.model_artifact_path,
        prediction_artifact_refs=artifact_manifest.prediction_artifact_paths,
    )


def _write_ref_file(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
