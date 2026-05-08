import logging
import os
from typing import List, Optional
from sqlmodel import Session

from app.modules.final_pipeline_selection.schemas import (
    FinalSelectedPipeline,
    FinalArtifactManifest,
    FinalPipelineSelectionCreateRequest,
)
from app.modules.final_pipeline_selection.enums import ArtifactIntegrityStatus
from app.modules.final_pipeline_selection.exceptions import FinalArtifactResolveException

logger = logging.getLogger(__name__)

ALLOWED_BASE_DIR = "/app/artifacts"


def resolve_final_artifacts(
    session: Session,
    final_pipeline: FinalSelectedPipeline,
    request: FinalPipelineSelectionCreateRequest,
) -> FinalArtifactManifest:
    manifest = FinalArtifactManifest(
        artifact_integrity_status=ArtifactIntegrityStatus.COMPLETE,
    )

    # Resolve model artifact from PipelineExecution
    pe_id = final_pipeline.source_pipeline_execution_id
    if pe_id:
        from app.modules.pipeline_execution.model import PipelineExecution
        pe = session.get(PipelineExecution, pe_id)
        if pe:
            exec_json = pe.execution_json or {}
            trial_results = exec_json.get("trial_results", [])
            for trial in trial_results:
                if trial.get("trial_id") == final_pipeline.final_trial_id:
                    manifest.model_artifact_path = _sanitize_path(
                        trial.get("model_artifact_path")
                    )
                    manifest.prediction_artifact_paths = [
                        p for p in [trial.get("prediction_artifact_path")] if p
                    ]
                    break
            # Fallback: training artifact dir
            if not manifest.model_artifact_path and pe.training_artifact_dir:
                manifest.model_artifact_path = _sanitize_path(
                    os.path.join(pe.training_artifact_dir, "model.pkl")
                )
            manifest.metric_results_path = _sanitize_path(
                exec_json.get("metric_results_path")
            )

    # Resolve preprocessor and matrix from PipelineGeneration.execution_input_json
    pg_id = final_pipeline.source_pipeline_generation_id
    if pg_id:
        from app.modules.pipeline_generation.model import PipelineGeneration
        pg = session.get(PipelineGeneration, pg_id)
        if pg:
            exec_input = pg.execution_input_json or {}
            manifest.preprocessor_artifact_path = _sanitize_path(
                exec_input.get("preprocessor_artifact_path")
            )
            manifest.model_ready_matrix_path = _sanitize_path(
                exec_input.get("model_ready_matrix_path")
            )
            manifest.feature_matrix_path = _sanitize_path(
                exec_input.get("feature_matrix_path")
            )
            # Fallback: try pipeline_json if exec_input didn't have them
            if not manifest.preprocessor_artifact_path:
                pipeline_json = pg.pipeline_json or {}
                manifest.preprocessor_artifact_path = _sanitize_path(
                    pipeline_json.get("preprocessor_artifact_path")
                )
            if not manifest.model_ready_matrix_path:
                pipeline_json = pg.pipeline_json or {}
                manifest.model_ready_matrix_path = _sanitize_path(
                    pipeline_json.get("model_ready_matrix_path")
                )

    # Validate artifact integrity
    hard_missing = []
    soft_missing = []
    if not manifest.model_artifact_path:
        hard_missing.append("model_artifact_path")
    if not manifest.preprocessor_artifact_path:
        soft_missing.append("preprocessor_artifact_path")
    if not manifest.model_ready_matrix_path:
        soft_missing.append("model_ready_matrix_path")

    if hard_missing and request.require_model_artifact:
        manifest.artifact_integrity_status = ArtifactIntegrityStatus.MISSING
        raise FinalArtifactResolveException(
            f"Required artifacts missing: {', '.join(hard_missing)}"
        )

    if hard_missing or soft_missing:
        manifest.artifact_integrity_status = ArtifactIntegrityStatus.PARTIAL
        logger.warning("Artifacts missing (non-fatal): %s", hard_missing + soft_missing)

    logger.info("Artifact integrity: %s", manifest.artifact_integrity_status)
    return manifest


def _sanitize_path(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    normalized = os.path.normpath(path)
    if ".." in normalized:
        logger.warning("Rejected path with '..': %s", path)
        return None
    return normalized
