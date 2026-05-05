from typing import Dict, Any, Optional
from datetime import datetime
from app.modules.result_diagnosis.model import ResultDiagnosis
from app.modules.result_diagnosis.schemas import (
    ResultDiagnosisResponse,
    LLMDiagnosisResult,
    SystemDiagnosticChecks,
    EvidenceSummary,
    ClosedLoopRefinementInput,
    DiagnosisArtifactManifest,
)
from app.modules.result_diagnosis.enums import ResultDiagnosisStatus, DiagnosisMode


def build_response(
    record: ResultDiagnosis,
    llm_diagnosis: Optional[LLMDiagnosisResult] = None,
    system_checks: Optional[SystemDiagnosticChecks] = None,
    evidence_summary: Optional[EvidenceSummary] = None,
    refinement_input: Optional[ClosedLoopRefinementInput] = None,
    artifact_manifest: Optional[DiagnosisArtifactManifest] = None,
    warnings: Optional[list] = None,
) -> ResultDiagnosisResponse:
    oa = llm_diagnosis.overall_assessment if llm_diagnosis else None
    return ResultDiagnosisResponse(
        result_diagnosis_id=record.id,
        task_id=record.task_id,
        metric_evaluation_id=record.metric_evaluation_id,
        pipeline_execution_id=record.pipeline_execution_id,
        status=record.status or ResultDiagnosisStatus.DIAGNOSING,
        diagnosis_mode=record.diagnosis_mode or DiagnosisMode.HYBRID,
        overall_assessment=oa,
        diagnostic_findings=llm_diagnosis.diagnostic_findings if llm_diagnosis else [],
        evidence_summary=evidence_summary,
        root_cause_hypotheses=llm_diagnosis.root_cause_hypotheses if llm_diagnosis else [],
        refinement_recommendations=llm_diagnosis.refinement_recommendations if llm_diagnosis else [],
        closed_loop_refinement_input=refinement_input,
        ready_for_closed_loop_refinement=record.ready_for_closed_loop_refinement or False,
        llm_diagnosis=llm_diagnosis,
        system_diagnostic_checks=system_checks,
        diagnosis_artifact_manifest=artifact_manifest,
        warnings=warnings or [],
        error_message=record.error_message,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
