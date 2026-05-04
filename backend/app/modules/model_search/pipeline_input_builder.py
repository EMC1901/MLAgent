import logging
from typing import List
from app.modules.model_search.schemas import PipelineGenerationInput

logger = logging.getLogger(__name__)


def build_pipeline_generation_input(
    model_ready_matrix_path: str = None,
    preprocessing_pipeline_artifact_id: str = None,
    target_column: str = None,
    feature_columns: List[str] = None,
    candidate_model_plan: dict = None,
    hpo_plan: dict = None,
    search_space_plan: dict = None,
    validation_plan: dict = None,
    evaluation_plan: dict = None,
) -> PipelineGenerationInput:
    """Build the input object for downstream Executable Pipeline Generation."""
    return PipelineGenerationInput(
        model_ready_matrix_path=model_ready_matrix_path,
        preprocessing_pipeline_artifact_id=preprocessing_pipeline_artifact_id,
        target_column=target_column,
        feature_columns=feature_columns or [],
        candidate_model_plan=candidate_model_plan or {},
        hpo_plan=hpo_plan or {},
        search_space_plan=search_space_plan or {},
        validation_plan=validation_plan or {},
        evaluation_plan=evaluation_plan or {},
        ready_for_pipeline_generation=True,
    )
