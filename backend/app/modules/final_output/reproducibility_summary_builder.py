import logging
import sys
import platform
from typing import Dict, Any
from datetime import datetime, timezone

from app.modules.final_output.schemas import ReproducibilitySummary
from app.modules.final_output.final_output_input_loader import FinalOutputInput
from app.modules.final_output.exceptions import ReproducibilitySummaryBuildException

logger = logging.getLogger(__name__)


def build_reproducibility_summary(
    fo_input: FinalOutputInput,
    dataset_source: str = "",
    target_column: str = "",
    feature_count: int = 0,
    feature_artifact_path: str = "",
    preprocessor_artifact_path: str = "",
    model_ready_matrix_path: str = "",
    validation_strategy: Dict[str, Any] = None,
    hpo_summary: Dict[str, Any] = None,
    random_state: int = None,
) -> ReproducibilitySummary:
    try:
        summary = ReproducibilitySummary(
            dataset_source=dataset_source or "Uploaded dataset",
            target_column=target_column or "unknown",
            feature_columns_count=feature_count or None,
            feature_artifact_path=feature_artifact_path,
            preprocessor_artifact_path=preprocessor_artifact_path,
            model_ready_matrix_path=model_ready_matrix_path,
            model_artifact_path=fo_input.model_artifact_path,
            prediction_artifact_paths=fo_input.prediction_artifact_paths,
            random_state=random_state,
            validation_strategy=validation_strategy or {},
            hpo_summary=hpo_summary or {},
            environment_summary=_build_environment_summary(),
            registry_versions={},
            created_at=datetime.now(timezone.utc),
        )

        logger.info("Built reproducibility summary")
        return summary

    except Exception as e:
        logger.error("Failed to build reproducibility summary: %s", str(e))
        raise ReproducibilitySummaryBuildException(str(e))


def _build_environment_summary() -> Dict[str, Any]:
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_machine": platform.machine(),
    }
