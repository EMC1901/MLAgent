import logging
from typing import Dict, Any, List
from app.modules.iteration_decision.schemas import EvidenceItem
from app.modules.iteration_decision.enums import EvidenceType

logger = logging.getLogger(__name__)


def extract_workflow_evidence(upstream: Dict[str, Any]) -> List[EvidenceItem]:
    items: List[EvidenceItem] = []

    # Pipeline execution quality
    pe = upstream.get("pipeline_execution", {}).get("execution_json") or {}
    if pe:
        n_trials_total = pe.get("n_trials_total") or pe.get("n_trials_executed") or 0
        n_failed = pe.get("n_trials_failed", 0)
        items.append(EvidenceItem(
            evidence_type=EvidenceType.WORKFLOW_QUALITY,
            source_module="pipeline_execution",
            source_field="trial_outcomes",
            value={"total": n_trials_total, "failed": n_failed},
            interpretation=f"Pipeline execution: {n_trials_total} trials total, {n_failed} failed.",
        ))
        runtime = pe.get("total_runtime_seconds")
        if runtime:
            items.append(EvidenceItem(
                evidence_type=EvidenceType.WORKFLOW_QUALITY,
                source_module="pipeline_execution",
                source_field="runtime",
                value=runtime,
                interpretation=f"Total pipeline runtime: {runtime:.0f}s.",
            ))

    # Pipeline generation
    pg = upstream.get("pipeline_generation", {}).get("pipeline_json") or {}
    pipeline_specs = upstream.get("pipeline_generation", {}).get("pipeline_specs") or []
    if pipeline_specs:
        items.append(EvidenceItem(
            evidence_type=EvidenceType.WORKFLOW_QUALITY,
            source_module="pipeline_generation",
            source_field="pipeline_spec_count",
            value=len(pipeline_specs),
            interpretation=f"{len(pipeline_specs)} pipeline specs generated.",
        ))

    # Model search context
    msc = upstream.get("model_search_context", {}).get("context_json") or {}
    if msc:
        candidate_plan = msc.get("candidate_model_plan") or {}
        families = candidate_plan.get("candidate_model_families", [])
        if families:
            items.append(EvidenceItem(
                evidence_type=EvidenceType.WORKFLOW_QUALITY,
                source_module="model_search_context",
                source_field="model_families",
                value=families,
                interpretation=f"Model families searched: {families}.",
            ))

    # Feature preprocessing summary
    fp = upstream.get("feature_preprocessing", {}).get("preprocessing_json") or {}
    if fp:
        operations = fp.get("operations_applied") or fp.get("preprocessing_steps") or []
        if operations:
            items.append(EvidenceItem(
                evidence_type=EvidenceType.WORKFLOW_QUALITY,
                source_module="feature_preprocessing",
                source_field="operations",
                value=len(operations) if isinstance(operations, list) else str(operations)[:100],
                interpretation="Preprocessing operations applied to feature matrix.",
            ))

    logger.info("Workflow evidence — %d items extracted", len(items))
    return items
