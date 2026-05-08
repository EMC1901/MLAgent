import logging
from typing import Optional

from app.modules.final_output.schemas import LLMReportOutput

logger = logging.getLogger(__name__)


def normalize_llm_report(report: Optional[LLMReportOutput]) -> Optional[LLMReportOutput]:
    if report is None:
        return None

    report.executive_summary = (report.executive_summary or "").strip()
    report.task_overview = (report.task_overview or "").strip()
    report.dataset_summary = (report.dataset_summary or "").strip()
    report.workflow_summary = (report.workflow_summary or "").strip()
    report.feature_engineering_summary = (report.feature_engineering_summary or "").strip()
    report.model_search_summary = (report.model_search_summary or "").strip()
    report.final_model_summary = (report.final_model_summary or "").strip()
    report.metric_summary = (report.metric_summary or "").strip()
    report.interpretability_summary = (report.interpretability_summary or "").strip()
    report.material_insight_summary = (report.material_insight_summary or "").strip()
    report.limitations_and_risks = (report.limitations_and_risks or "").strip()
    report.reproducibility_notes = (report.reproducibility_notes or "").strip()
    report.artifact_summary = (report.artifact_summary or "").strip()
    report.next_steps = (report.next_steps or "").strip()

    level = (report.confidence_level or "").lower().strip()
    report.confidence_level = level if level in ("low", "medium", "high") else "medium"

    logger.info("Normalized LLM report")
    return report
