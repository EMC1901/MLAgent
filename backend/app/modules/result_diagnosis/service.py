import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Session

from app.modules.result_diagnosis.model import ResultDiagnosis
from app.modules.result_diagnosis.repository import ResultDiagnosisRepository
from app.modules.result_diagnosis.schemas import (
    ResultDiagnosisCreateRequest,
    ResultDiagnosisResponse,
    ResultDiagnosisSummaryResponse,
    ClosedLoopRefinementInput,
)
from app.modules.result_diagnosis.enums import (
    ResultDiagnosisStatus,
    DiagnosisMode,
)
from app.modules.result_diagnosis.exceptions import (
    ResultDiagnosisNotFoundException,
    MetricEvaluationRequiredException,
)

from app.modules.result_diagnosis.context_builder import build_result_diagnosis_context
from app.modules.result_diagnosis.diagnosis_input_loader import load_result_diagnosis_input
from app.modules.result_diagnosis.evidence_extractor import extract_evidence
from app.modules.result_diagnosis.system_diagnostic_checker import run_system_diagnostic_checks
from app.modules.result_diagnosis.diagnostic_context_builder import build_llm_diagnostic_context
from app.modules.result_diagnosis.llm_prompt_builder import build_llm_prompt
from app.modules.result_diagnosis.llm_result_diagnoser import LLMResultDiagnoser
from app.modules.result_diagnosis.llm_response_parser import parse_llm_response
from app.modules.result_diagnosis.llm_diagnosis_validator import validate_llm_diagnosis
from app.modules.result_diagnosis.llm_diagnosis_normalizer import normalize_llm_diagnosis
from app.modules.result_diagnosis.refinement_input_builder import build_closed_loop_refinement_input
from app.modules.result_diagnosis.diagnosis_artifact_manager import save_diagnosis_artifacts
from app.modules.result_diagnosis.builder import build_response

logger = logging.getLogger(__name__)


def _load_optional_context(session: Session, task_id: str, request: ResultDiagnosisCreateRequest) -> dict:
    """Optionally load upstream context records for richer diagnosis."""
    contexts: dict = {}
    try:
        if request.include_dataset_context:
            from app.modules.dataset_profile.repository import DatasetProfileRepository
            dp_repo = DatasetProfileRepository()
            dp = dp_repo.get_latest_by_task_id(session, task_id)
            if dp:
                contexts["dataset_profile"] = dp.__dict__ if hasattr(dp, "__dict__") else dp
    except Exception as e:
        logger.debug("Could not load dataset profile: %s", str(e))

    try:
        if request.include_feature_context:
            from app.modules.feature_engineering.repository import FeatureEngineeringRepository
            from app.modules.feature_preprocessing.repository import FeaturePreprocessingRepository
            fe_repo = FeatureEngineeringRepository()
            fe = fe_repo.get_latest_by_task_id(session, task_id)
            if fe and hasattr(fe, "feature_json"):
                contexts["feature_engineering"] = {"feature_json": fe.feature_json}
            fp_repo = FeaturePreprocessingRepository()
            fp = fp_repo.get_latest_by_task_id(session, task_id)
            if fp and hasattr(fp, "preprocessing_json"):
                contexts["feature_preprocessing"] = {"preprocessing_json": fp.preprocessing_json}
    except Exception as e:
        logger.debug("Could not load feature context: %s", str(e))

    try:
        if request.include_pipeline_context:
            from app.modules.pipeline_execution.repository import PipelineExecutionRepository
            pe_repo = PipelineExecutionRepository()
            pe = pe_repo.get_latest_by_task_id(session, task_id)
            if pe and hasattr(pe, "execution_json"):
                contexts["pipeline_execution"] = {"execution_json": pe.execution_json}
    except Exception as e:
        logger.debug("Could not load pipeline execution context: %s", str(e))

    return contexts


class ResultDiagnosisService:

    def __init__(self):
        self.repo = ResultDiagnosisRepository()
        self.llm_diagnoser = LLMResultDiagnoser()

    def create_result_diagnosis(
        self,
        session: Session,
        task_id: str,
        request: ResultDiagnosisCreateRequest,
    ) -> ResultDiagnosisResponse:
        warnings_list: list = []

        # Step 1: Build context & validate upstream
        me = build_result_diagnosis_context(session, task_id, request.metric_evaluation_id)

        # If not force_rerun, check for existing diagnosis
        if not request.force_rerun:
            existing = self.repo.get_latest_by_task_id(session, task_id)
            if existing and existing.metric_evaluation_id == me.id and existing.status in (
                ResultDiagnosisStatus.DIAGNOSED,
                ResultDiagnosisStatus.DIAGNOSED_WITH_WARNING,
                ResultDiagnosisStatus.FALLBACK_DIAGNOSED,
            ):
                return self.get_result_diagnosis(session, existing.id)

        # Create record
        rd_id = f"rd_{uuid.uuid4().hex[:8]}"
        record = ResultDiagnosis(
            id=rd_id,
            task_id=task_id,
            metric_evaluation_id=me.id,
            pipeline_execution_id=me.pipeline_execution_id,
            status=ResultDiagnosisStatus.DIAGNOSING,
            diagnosis_mode=DiagnosisMode.HYBRID if request.use_llm else DiagnosisMode.SYSTEM_RULE_BASED,
            llm_used=request.use_llm,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.repo.create(session, record)

        try:
            # Step 2: Load diagnosis input
            di_input = load_result_diagnosis_input(me)

            # Step 3: Collect optional context
            optional_contexts = _load_optional_context(session, task_id, request)

            # Step 4: Extract evidence
            evidence = extract_evidence(di_input, optional_contexts)

            # Step 5: Run system diagnostic checks
            system_checks = run_system_diagnostic_checks(di_input, evidence, optional_contexts)
            record.system_checks_json = system_checks.model_dump()

            # Step 6: Build LLM diagnostic context
            diag_context = build_llm_diagnostic_context(
                di_input, evidence, system_checks, optional_contexts, request.diagnosis_profile
            )

            llm_available = False
            llm_diagnosis = None
            refinement_input = None

            # Steps 7-11: LLM diagnosis flow
            if request.use_llm:
                try:
                    prompt = build_llm_prompt(diag_context)
                    llm_result = self.llm_diagnoser.diagnose(
                        prompt["system_prompt"], prompt["user_message"]
                    )
                    record.llm_request_json = prompt
                    record.llm_response_json = {"raw_response": llm_result["raw_response"]}

                    parsed = parse_llm_response(llm_result["raw_response"])
                    is_valid, validation_issues = validate_llm_diagnosis(parsed)

                    if is_valid:
                        llm_diagnosis = normalize_llm_diagnosis(parsed)
                        llm_available = True
                        record.diagnosis_mode = DiagnosisMode.HYBRID
                    else:
                        warnings_list.append(
                            f"LLM diagnosis validation failed: {'; '.join(validation_issues[:5])}"
                        )
                        llm_available = False

                except Exception as e:
                    logger.warning("LLM diagnosis failed, falling back to system rules: %s", str(e))
                    warnings_list.append(f"LLM diagnosis failed: {str(e)}")
                    llm_available = False

            # Step 12: Build closed-loop refinement input
            refinement_input = build_closed_loop_refinement_input(
                result_diagnosis_id=rd_id,
                metric_evaluation_id=me.id,
                task_id=task_id,
                llm_diagnosis=llm_diagnosis,
                system_checks=system_checks,
                llm_available=llm_available,
            )

            # Step 13: Save artifacts
            diag_dict = llm_diagnosis.model_dump() if llm_diagnosis else {}
            artifact_manifest = save_diagnosis_artifacts(
                result_diagnosis_id=rd_id,
                diagnosis_result={"status": record.status, "warnings": warnings_list},
                diagnostic_context=diag_context,
                system_checks=system_checks.model_dump(),
                llm_diagnosis=diag_dict,
                evidence_summary=evidence.model_dump(),
                refinement_input=refinement_input.model_dump() if refinement_input else {},
            )

            # Step 14: Update record
            record.status = ResultDiagnosisStatus.DIAGNOSED
            if warnings_list:
                record.status = ResultDiagnosisStatus.DIAGNOSED_WITH_WARNING
            if not llm_available and request.use_llm:
                record.status = ResultDiagnosisStatus.FALLBACK_DIAGNOSED

            oa = llm_diagnosis.overall_assessment if llm_diagnosis else None
            record.main_issue_category = oa.main_issue_category if oa else None
            record.performance_level = oa.performance_level if oa else None
            record.should_refine = refinement_input.should_refine if refinement_input else False
            record.ready_for_closed_loop_refinement = (
                refinement_input.ready_for_closed_loop_refinement if refinement_input else False
            )
            record.llm_confidence_level = llm_diagnosis.confidence_level if llm_diagnosis else None
            record.diagnosis_json = diag_dict
            record.closed_loop_refinement_input_json = refinement_input.model_dump() if refinement_input else None
            record.diagnosis_artifact_dir = f"/app/artifacts/diagnosis/{rd_id}"
            record.updated_at = datetime.now(timezone.utc)

            self.repo.update(session, record)

            return build_response(
                record=record,
                llm_diagnosis=llm_diagnosis,
                system_checks=system_checks,
                evidence_summary=evidence,
                refinement_input=refinement_input,
                artifact_manifest=artifact_manifest,
                warnings=warnings_list,
            )

        except Exception as e:
            logger.error("Result diagnosis failed: %s", str(e))
            record.status = ResultDiagnosisStatus.FAILED
            record.error_message = str(e)
            record.updated_at = datetime.now(timezone.utc)
            self.repo.update(session, record)

            return build_response(
                record=record,
                warnings=warnings_list,
            )

    def get_result_diagnosis(
        self, session: Session, rd_id: str
    ) -> ResultDiagnosisResponse:
        record = self.repo.get_by_id(session, rd_id)
        if not record:
            raise ResultDiagnosisNotFoundException(
                f"ResultDiagnosis '{rd_id}' not found."
            )

        llm_diag = None
        if record.diagnosis_json:
            from app.modules.result_diagnosis.schemas import LLMDiagnosisResult
            try:
                llm_diag = LLMDiagnosisResult(**record.diagnosis_json)
            except Exception:
                pass

        system_checks = None
        if record.system_checks_json:
            from app.modules.result_diagnosis.schemas import SystemDiagnosticChecks
            try:
                system_checks = SystemDiagnosticChecks(**record.system_checks_json)
            except Exception:
                pass

        refinement_input = None
        if record.closed_loop_refinement_input_json:
            try:
                refinement_input = ClosedLoopRefinementInput(**record.closed_loop_refinement_input_json)
            except Exception:
                pass

        return build_response(
            record=record,
            llm_diagnosis=llm_diag,
            system_checks=system_checks,
            refinement_input=refinement_input,
        )

    def get_latest_by_task_id(
        self, session: Session, task_id: str
    ) -> ResultDiagnosisResponse:
        record = self.repo.get_latest_by_task_id(session, task_id)
        if not record:
            raise ResultDiagnosisNotFoundException(
                f"No ResultDiagnosis found for task '{task_id}'."
            )
        return self.get_result_diagnosis(session, record.id)

    def rerun_result_diagnosis(
        self, session: Session, task_id: str
    ) -> ResultDiagnosisResponse:
        request = ResultDiagnosisCreateRequest(force_rerun=True)
        return self.create_result_diagnosis(session, task_id, request)

    def get_summary(
        self, session: Session, rd_id: str
    ) -> ResultDiagnosisSummaryResponse:
        record = self.repo.get_by_id(session, rd_id)
        if not record:
            raise ResultDiagnosisNotFoundException(
                f"ResultDiagnosis '{rd_id}' not found."
            )

        top_findings = []
        top_recommendations = []
        if record.diagnosis_json:
            findings = record.diagnosis_json.get("diagnostic_findings") or []
            for f in findings[:5]:
                if isinstance(f, dict):
                    top_findings.append({
                        "diagnosis_type": f.get("diagnosis_type"),
                        "severity": f.get("severity"),
                        "description": f.get("description"),
                    })
            recs = record.diagnosis_json.get("refinement_recommendations") or []
            for r in recs[:5]:
                if isinstance(r, dict):
                    top_recommendations.append({
                        "target_stage": r.get("target_stage"),
                        "recommendation_type": r.get("recommendation_type"),
                        "priority": r.get("priority"),
                        "description": r.get("description"),
                    })

        return ResultDiagnosisSummaryResponse(
            result_diagnosis_id=record.id,
            task_id=record.task_id or "",
            status=record.status or "",
            main_issue_category=record.main_issue_category,
            performance_level=record.performance_level,
            should_refine=record.should_refine or False,
            ready_for_closed_loop_refinement=record.ready_for_closed_loop_refinement or False,
            top_findings=top_findings,
            top_recommendations=top_recommendations,
            created_at=record.created_at,
        )

    def needs_fresh_diagnosis(self, session: Session, task_id: str) -> dict:
        """Check if the latest diagnosis is stale (its metric_evaluation is not the latest)."""
        existing = self.repo.get_latest_by_task_id(session, task_id)
        try:
            me = build_result_diagnosis_context(session, task_id, None)
            latest_me_id = me.id
        except Exception:
            latest_me_id = None

        if not existing:
            return {"needs_fresh": True, "reason": "No existing diagnosis."}

        if latest_me_id and existing.metric_evaluation_id != latest_me_id:
            return {
                "needs_fresh": True,
                "reason": (
                    f"Existing diagnosis ({existing.id}) was run against "
                    f"metric_evaluation {existing.metric_evaluation_id}, "
                    f"but the latest is {latest_me_id}."
                ),
                "existing_diagnosis_id": existing.id,
                "existing_metric_evaluation_id": existing.metric_evaluation_id,
                "latest_metric_evaluation_id": latest_me_id,
            }

        return {
            "needs_fresh": False,
            "reason": "Existing diagnosis is up-to-date.",
            "existing_diagnosis_id": existing.id,
            "latest_metric_evaluation_id": latest_me_id,
        }

    def get_closed_loop_refinement_input(
        self, session: Session, rd_id: str
    ) -> dict:
        record = self.repo.get_by_id(session, rd_id)
        if not record:
            raise ResultDiagnosisNotFoundException(
                f"ResultDiagnosis '{rd_id}' not found."
            )
        if record.closed_loop_refinement_input_json:
            return record.closed_loop_refinement_input_json
        return {}
