import json
import logging
import os
from typing import List, Dict, Any
from datetime import datetime, timezone

from app.modules.final_pipeline_selection.schemas import (
    CandidateSelectionItem,
    SelectionPolicy,
    SystemSelectionReason,
    LLMSelectionExplanation,
    FinalArtifactManifest,
    InterpretabilityAnalysisInput,
    ConstraintCheckResult,
    ArtifactManifest,
)
from app.modules.final_pipeline_selection.exceptions import FinalSelectionArtifactSaveException

logger = logging.getLogger(__name__)

ARTIFACT_BASE_DIR = "/app/artifacts/final_selection"


def save_selection_artifacts(
    final_selection_id: str,
    final_selection_result: Dict[str, Any],
    candidate_ranking: List[CandidateSelectionItem],
    selection_policy: SelectionPolicy,
    constraint_check_result: ConstraintCheckResult,
    system_selection_reason: SystemSelectionReason,
    llm_explanation: LLMSelectionExplanation = None,
    final_artifact_manifest: FinalArtifactManifest = None,
    interpretability_input: InterpretabilityAnalysisInput = None,
) -> ArtifactManifest:
    artifact_dir = os.path.join(ARTIFACT_BASE_DIR, final_selection_id)

    try:
        os.makedirs(artifact_dir, exist_ok=True)
    except OSError as e:
        raise FinalSelectionArtifactSaveException(
            f"Failed to create artifact directory: {str(e)}"
        )

    manifest = ArtifactManifest(manifest_path=os.path.join(artifact_dir, "manifest.json"))

    def _write_json(filename: str, data: Any) -> str:
        path = os.path.join(artifact_dir, filename)
        with open(path, "w") as f:
            json.dump(
                data if isinstance(data, dict) else _serialize(data),
                f,
                indent=2,
                default=str,
            )
        return path

    manifest.final_pipeline_selection_result_path = _write_json(
        "final_pipeline_selection_result.json", final_selection_result
    )
    manifest.candidate_ranking_path = _write_json(
        "candidate_ranking.json",
        [_serialize(c) for c in candidate_ranking],
    )
    manifest.selection_policy_path = _write_json(
        "selection_policy.json", selection_policy.model_dump()
    )
    manifest.constraint_check_result_path = _write_json(
        "constraint_check_result.json", constraint_check_result.model_dump()
    )
    manifest.system_selection_reason_path = _write_json(
        "system_selection_reason.json", system_selection_reason.model_dump()
    )

    if llm_explanation:
        manifest.llm_selection_explanation_path = _write_json(
            "llm_selection_explanation.json", llm_explanation.model_dump()
        )

    if final_artifact_manifest:
        manifest.final_artifact_manifest_path = _write_json(
            "final_artifact_manifest.json", final_artifact_manifest.model_dump()
        )

    if interpretability_input:
        manifest.interpretability_analysis_input_path = _write_json(
            "interpretability_analysis_input.json", interpretability_input.model_dump()
        )

    logger.info("Saved selection artifacts to %s", artifact_dir)
    return manifest


def _serialize(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return str(obj)
