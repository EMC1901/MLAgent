import logging
from app.modules.final_pipeline_selection.model import FinalPipelineSelection
from app.modules.final_pipeline_selection.schemas import InterpretabilityAnalysisInput
from app.modules.interpretability_analysis.exceptions import InterpretabilityInputInvalidException

logger = logging.getLogger(__name__)


def load_interpretability_analysis_input(fps: FinalPipelineSelection) -> InterpretabilityAnalysisInput:
    data = fps.interpretability_analysis_input_json
    if not data:
        raise InterpretabilityInputInvalidException("interpretability_analysis_input_json is empty.")

    try:
        ia_input = InterpretabilityAnalysisInput(**data)
    except Exception as e:
        raise InterpretabilityInputInvalidException(
            f"Failed to parse interpretability_analysis_input_json: {str(e)}"
        )

    # Scalars that must be non-empty strings
    _required_scalars = {
        "final_model_id": ia_input.final_model_id,
        "final_model_family": ia_input.final_model_family,
        "final_trial_id": ia_input.final_trial_id,
        "final_pipeline_spec_id": ia_input.final_pipeline_spec_id,
        "model_artifact_path": ia_input.model_artifact_path,
        "model_ready_matrix_path": ia_input.model_ready_matrix_path,
        "preprocessor_artifact_path": ia_input.preprocessor_artifact_path,
        "primary_metric": ia_input.primary_metric,
    }

    missing = [k for k, v in _required_scalars.items() if not v]

    # feature_columns may legitimately be empty — they get populated from the matrix
    # prediction_artifact_paths may legitimately be empty
    # primary_metric_value may be 0 (valid float)

    if missing:
        raise InterpretabilityInputInvalidException(
            f"Missing required fields in interpretability_analysis_input: {', '.join(missing)}"
        )

    logger.info(
        "Loaded interpretability analysis input for model=%s family=%s trial=%s",
        ia_input.final_model_id, ia_input.final_model_family, ia_input.final_trial_id,
    )
    return ia_input
