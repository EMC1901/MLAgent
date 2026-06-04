import logging
from typing import List, Optional, Dict, Any

from app.modules.final_output.model import FinalOutput
from app.modules.final_output.schemas import FinalOutputResponse

logger = logging.getLogger(__name__)


def build_response(
    record: FinalOutput,
    warnings: Optional[List[str]] = None,
) -> FinalOutputResponse:
    fo_json = record.final_output_json or {}
    return FinalOutputResponse(
        final_output_id=record.id,
        task_id=record.task_id,
        interpretability_analysis_id=record.interpretability_analysis_id,
        status=record.status or "generating",
        report_profile=record.report_profile or "standard",
        final_model_summary=_extract_model_from_json(record.final_output_json),
        final_metric_summary=_extract_metric_from_json(record.final_output_json),
        interpretability_summary=_extract_interpretability_from_json(record.final_output_json),
        workflow_trace_summary=record.workflow_trace_json,
        reproducibility_summary=record.reproducibility_summary_json,
        final_artifact_manifest=record.artifact_manifest_json,
        final_report=record.final_report_json,
        llm_report_summary=record.llm_report_json,
        output_package_manifest=record.output_package_manifest_json,
        download_links=record.download_links_json,
        topic_files=fo_json.get("topic_files"),
        ready_for_delivery=bool(record.ready_for_delivery),
        warnings=warnings or [],
        error_message=record.error_message,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _extract_model_from_json(data: Optional[Dict]) -> Optional[Dict]:
    if isinstance(data, dict):
        return data.get("final_model_summary")
    return None


def _extract_metric_from_json(data: Optional[Dict]) -> Optional[Dict]:
    if isinstance(data, dict):
        return data.get("final_metric_summary")
    return None



def _extract_interpretability_from_json(data: Optional[Dict]) -> Optional[Dict]:
    if isinstance(data, dict):
        return data.get("interpretability_summary")
    return None
