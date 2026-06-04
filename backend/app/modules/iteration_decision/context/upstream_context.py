import logging
from typing import Dict, Any, Optional
from sqlmodel import Session

logger = logging.getLogger(__name__)


def _safe_load(session: Session, task_id: str, module_name: str, repo_class, attr_map: dict) -> Dict[str, Any]:
    """Generic safe loader for upstream module context."""
    try:
        repo = repo_class()
        record = repo.get_latest_by_task_id(session, task_id)
        if record:
            result = {}
            for src_attr, dest_key in attr_map.items():
                if hasattr(record, src_attr):
                    val = getattr(record, src_attr)
                    if val is not None:
                        result[dest_key] = val
            result["id"] = getattr(record, "id", None)
            return result
    except Exception:
        pass
    return {}


def gather_upstream_context(session: Session, task_id: str) -> Dict[str, Any]:
    """Gather all upstream module contexts needed for the decision."""
    context: Dict[str, Any] = {"task_id": task_id}
    loaded: list = []
    skipped: list = []

    def _load(name: str, repo_class, attr_map: dict):
        result = _safe_load(session, task_id, name, repo_class, attr_map)
        if result:
            loaded.append(name)
        else:
            skipped.append(name)
        return result

    # Task Specification
    from app.modules.task_specification.repository import TaskSpecificationRepository
    try:
        ts_repo = TaskSpecificationRepository()
        ts = ts_repo.get_by_id(session, task_id)
        if ts:
            context["task_specification"] = {
                "task_spec_id": ts.id,
                "task_spec_json": ts.task_spec_json,
            }
            loaded.append("task_specification")
        else:
            skipped.append("task_specification")
    except Exception:
        skipped.append("task_specification")

    # Task Interpretation
    context["task_interpretation"] = _load(
        "task_interpretation",
        __import__("app.modules.task_interpretation.repository", fromlist=["TaskInterpretationRepository"]).TaskInterpretationRepository,
        {"interpretation_json": "interpretation_json"},
    )

    # Dataset Profile
    context["dataset_profile"] = _load(
        "dataset_profile",
        __import__("app.modules.dataset_profile.repository", fromlist=["DatasetProfileRepository"]).DatasetProfileRepository,
        {"profile_json": "profile_json", "n_samples": "n_samples", "n_columns": "n_columns"},
    )

    # Workflow Plan
    context["workflow_plan"] = _load(
        "workflow_plan",
        __import__("app.modules.workflow_planning.repository", fromlist=["WorkflowPlanRepository"]).WorkflowPlanRepository,
        {"plan_json": "plan_json"},
    )

    # Feature Engineering
    context["feature_engineering"] = _load(
        "feature_engineering",
        __import__("app.modules.feature_engineering.repository", fromlist=["FeatureEngineeringRepository"]).FeatureEngineeringRepository,
        {
            "feature_json": "feature_json",
            "feature_groups_json": "feature_groups_json",
            "quality_profile_json": "quality_profile_json",
            "execution_report_json": "execution_report_json",
            "n_features": "n_features",
            "input_modality": "input_modality",
            "feature_type": "feature_type",
        },
    )

    # Feature Preprocessing
    context["feature_preprocessing"] = _load(
        "feature_preprocessing",
        __import__("app.modules.feature_preprocessing.repository", fromlist=["FeaturePreprocessingRepository"]).FeaturePreprocessingRepository,
        {
            "preprocessing_json": "preprocessing_json",
            "execution_report_json": "execution_report_json",
            "removed_features_json": "removed_features_json",
            "explainability_report_json": "explainability_report_json",
            "n_raw_features": "n_raw_features",
            "n_valid_features": "n_valid_features",
            "n_final_features": "n_final_features",
            "n_dropped_features": "n_dropped_features",
        },
    )

    # Model Search Context
    context["model_search_context"] = _load(
        "model_search_context",
        __import__("app.modules.model_search_context.repository", fromlist=["ModelSearchContextRepository"]).ModelSearchContextRepository,
        {"context_json": "context_json"},
    )

    # Pipeline Generation
    context["pipeline_generation"] = _load(
        "pipeline_generation",
        __import__("app.modules.pipeline_generation.repository", fromlist=["PipelineGenerationRepository"]).PipelineGenerationRepository,
        {"pipeline_json": "pipeline_json", "pipeline_specs": "pipeline_specs", "trial_plan": "trial_plan"},
    )

    # Pipeline Execution
    pe_repo = __import__("app.modules.pipeline_execution.repository", fromlist=["PipelineExecutionRepository"]).PipelineExecutionRepository
    context["pipeline_execution"] = _load(
        "pipeline_execution", pe_repo,
        {
            "execution_json": "execution_json",
            "runtime_log_json": "runtime_log_json",
            "n_trials_completed": "n_trials_completed",
            "n_trials_failed": "n_trials_failed",
            "n_trials_planned": "n_trials_planned",
        },
    )

    context["_module_count"] = len(loaded)
    if skipped:
        logger.info("Upstream context — %d/%d loaded, skipped: %s",
                     len(loaded), len(loaded) + len(skipped), ", ".join(skipped))
    else:
        logger.info("Upstream context — all %d modules loaded", len(loaded))

    return context
