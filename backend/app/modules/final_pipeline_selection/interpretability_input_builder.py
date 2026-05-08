import logging
from typing import List, Optional
from sqlmodel import Session

from app.modules.final_pipeline_selection.schemas import (
    FinalSelectedPipeline,
    FinalArtifactManifest,
    InterpretabilityAnalysisInput,
    SystemSelectionReason,
)
from app.modules.final_pipeline_selection.exceptions import InterpretabilityInputBuildException

logger = logging.getLogger(__name__)


def build_interpretability_analysis_input(
    session: Session,
    final_pipeline: FinalSelectedPipeline,
    artifact_manifest: FinalArtifactManifest,
    system_reason: SystemSelectionReason,
    task_id: str,
    final_selection_id: str,
    task_type: str = "",
    target_column: str = "",
    primary_metric: str = "",
    primary_metric_value: Optional[float] = None,
    secondary_metrics: dict = None,
) -> InterpretabilityAnalysisInput:
    ready = bool(
        artifact_manifest.model_artifact_path
        and artifact_manifest.model_ready_matrix_path
        and artifact_manifest.preprocessor_artifact_path
        and final_pipeline.final_trial_id
    )

    if not ready:
        missing = []
        if not artifact_manifest.model_artifact_path:
            missing.append("model_artifact_path")
        if not artifact_manifest.model_ready_matrix_path:
            missing.append("model_ready_matrix_path")
        if not artifact_manifest.preprocessor_artifact_path:
            missing.append("preprocessor_artifact_path")
        raise InterpretabilityInputBuildException(
            f"Cannot build interpretability input: missing {', '.join(missing)}"
        )

    input_obj = InterpretabilityAnalysisInput(
        final_pipeline_selection_id=final_selection_id,
        task_id=task_id,
        task_type=task_type,
        target_column=target_column,
        final_model_id=final_pipeline.final_model_id,
        final_model_family=final_pipeline.final_model_family,
        final_trial_id=final_pipeline.final_trial_id,
        final_pipeline_spec_id=final_pipeline.final_pipeline_spec_id,
        model_artifact_path=artifact_manifest.model_artifact_path,
        model_ready_matrix_path=artifact_manifest.model_ready_matrix_path,
        feature_columns=[],  # Will be populated from matrix metadata
        prediction_artifact_paths=artifact_manifest.prediction_artifact_paths,
        preprocessor_artifact_path=artifact_manifest.preprocessor_artifact_path,
        primary_metric=primary_metric,
        primary_metric_value=primary_metric_value,
        secondary_metrics=secondary_metrics or {},
        interpretability_methods_recommended=_recommend_interpretability_methods(
            final_pipeline.final_model_family
        ),
        selection_reason_summary=system_reason.main_reason,
        ready_for_interpretability_analysis=ready,
    )

    logger.info("Built interpretability analysis input for %s", final_pipeline.final_model_id)
    return input_obj


def _recommend_interpretability_methods(model_family: Optional[str]) -> List[str]:
    family = (model_family or "").lower()
    if family in ("linear", "ridge", "lasso", "elastic_net", "elasticnet"):
        return ["coefficients", "permutation_importance"]
    if family in ("random_forest", "randomforest", "gradient_boosting", "gradientboosting", "xgboost", "xgb"):
        return ["shap", "permutation_importance", "feature_importance"]
    if family in ("knn", "kneighbors", "svr", "svm"):
        return ["permutation_importance", "shap"]
    return ["permutation_importance"]
