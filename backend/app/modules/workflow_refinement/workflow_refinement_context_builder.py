import logging
from typing import Dict, Any, Optional, List
from sqlmodel import Session
from app.modules.result_diagnosis.model import ResultDiagnosis
from app.modules.workflow_refinement.schemas import ExperimentHistorySummary

logger = logging.getLogger(__name__)


def build_llm_workflow_refinement_context(
    session: Session,
    task_id: str,
    rd: ResultDiagnosis,
    cl_input: Dict[str, Any],
    history: ExperimentHistorySummary,
    decision_profile: str = "balanced",
) -> Dict[str, Any]:
    """Build the full context for the LLM workflow refinement decision."""

    context: Dict[str, Any] = {
        "decision_profile": decision_profile,
        "task_id": task_id,
        "result_diagnosis": _load_result_diagnosis_context(rd),
        "closed_loop_refinement_input": cl_input,
        "experiment_history": history.model_dump(),
    }

    _load_upstream_modules(session, task_id, context)

    return context


def _load_result_diagnosis_context(rd: ResultDiagnosis) -> Dict[str, Any]:
    return {
        "result_diagnosis_id": rd.id,
        "status": rd.status,
        "diagnosis_mode": rd.diagnosis_mode,
        "main_issue_category": rd.main_issue_category,
        "performance_level": rd.performance_level,
        "should_refine": rd.should_refine,
        "ready_for_closed_loop_refinement": rd.ready_for_closed_loop_refinement,
        "llm_confidence_level": rd.llm_confidence_level,
        "diagnosis_json": rd.diagnosis_json,
        "system_checks_json": rd.system_checks_json,
    }


def _load_upstream_modules(session: Session, task_id: str, context: Dict[str, Any]) -> None:
    try:
        from app.modules.metric_evaluation.repository import MetricEvaluationRepository
        me_repo = MetricEvaluationRepository()
        me = me_repo.get_latest_by_task_id(session, task_id)
        if me:
            context["metric_evaluation"] = {
                "metric_evaluation_id": me.id,
                "evaluation_json": me.evaluation_json,
                "metric_summary_json": me.metric_summary_json,
                "model_ranking_json": me.model_ranking_json,
                "best_model_id": me.best_model_id,
                "best_trial_id": me.best_trial_id,
                "best_pipeline_spec_id": me.best_pipeline_spec_id,
            }
    except Exception as e:
        logger.debug("Could not load metric evaluation: %s", str(e))

    try:
        from app.modules.pipeline_execution.repository import PipelineExecutionRepository
        pe_repo = PipelineExecutionRepository()
        pe = pe_repo.get_latest_by_task_id(session, task_id)
        if pe:
            context["pipeline_execution"] = {
                "pipeline_execution_id": pe.id,
                "execution_json": pe.execution_json,
                "runtime_log_json": pe.runtime_log_json,
            }
    except Exception as e:
        logger.debug("Could not load pipeline execution: %s", str(e))

    try:
        from app.modules.pipeline_generation.repository import PipelineGenerationRepository
        pg_repo = PipelineGenerationRepository()
        pg = pg_repo.get_latest_by_task_id(session, task_id)
        if pg:
            context["pipeline_generation"] = {
                "pipeline_generation_id": pg.id,
                "pipeline_json": pg.pipeline_json,
                "pipeline_specs": pg.pipeline_specs,
                "trial_plan": pg.trial_plan,
            }
    except Exception as e:
        logger.debug("Could not load pipeline generation: %s", str(e))

    try:
        from app.modules.model_search.repository import ModelSearchRepository
        ms_repo = ModelSearchRepository()
        ms = ms_repo.get_latest_by_task_id(session, task_id)
        if ms:
            context["model_search_plan"] = {
                "model_search_plan_id": ms.id,
                "plan_json": ms.plan_json,
            }
    except Exception as e:
        logger.debug("Could not load model search plan: %s", str(e))

    try:
        from app.modules.workflow_planning.repository import WorkflowPlanRepository
        wp_repo = WorkflowPlanRepository()
        wp = wp_repo.get_latest_by_task_id(session, task_id)
        if wp:
            context["workflow_plan"] = {
                "workflow_plan_id": wp.id,
                "plan_json": wp.plan_json,
            }
    except Exception as e:
        logger.debug("Could not load workflow plan: %s", str(e))

    try:
        from app.modules.feature_engineering.repository import FeatureEngineeringRepository
        fe_repo = FeatureEngineeringRepository()
        fe = fe_repo.get_latest_by_task_id(session, task_id)
        if fe:
            context["feature_engineering"] = {
                "feature_engineering_id": fe.id,
                "feature_json": fe.feature_json,
            }
    except Exception as e:
        logger.debug("Could not load feature engineering: %s", str(e))

    try:
        from app.modules.feature_preprocessing.repository import FeaturePreprocessingRepository
        fp_repo = FeaturePreprocessingRepository()
        fp = fp_repo.get_latest_by_task_id(session, task_id)
        if fp:
            context["feature_preprocessing"] = {
                "feature_preprocessing_id": fp.id,
                "preprocessing_json": fp.preprocessing_json,
            }
    except Exception as e:
        logger.debug("Could not load feature preprocessing: %s", str(e))

    try:
        from app.modules.dataset_profile.repository import DatasetProfileRepository
        dp_repo = DatasetProfileRepository()
        dp = dp_repo.get_latest_by_task_id(session, task_id)
        if dp:
            context["dataset_profile"] = {
                "dataset_profile_id": dp.id,
                "profile_json": dp.profile_json,
            }
    except Exception as e:
        logger.debug("Could not load dataset profile: %s", str(e))

    try:
        from app.modules.task_specification.repository import TaskSpecificationRepository
        ts_repo = TaskSpecificationRepository()
        ts = ts_repo.get_by_id(session, task_id)
        if ts:
            context["task_specification"] = {
                "task_spec_id": ts.id,
                "task_spec_json": ts.task_spec_json,
            }
    except Exception as e:
        logger.debug("Could not load task specification: %s", str(e))

    try:
        from app.modules.task_interpretation.repository import TaskInterpretationRepository
        ti_repo = TaskInterpretationRepository()
        ti = ti_repo.get_latest_by_task_id(session, task_id)
        if ti:
            context["task_interpretation"] = {
                "interpretation_id": ti.id,
                "interpretation_json": ti.interpretation_json,
            }
    except Exception as e:
        logger.debug("Could not load task interpretation: %s", str(e))
