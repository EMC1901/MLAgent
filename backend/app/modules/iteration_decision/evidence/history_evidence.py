import logging
from typing import Dict, Any, List
from app.modules.iteration_decision.schemas import EvidenceItem

logger = logging.getLogger(__name__)


def extract_history_evidence(history: Dict[str, Any]) -> List[EvidenceItem]:
    items: List[EvidenceItem] = []

    n_iter = history.get("n_iterations_completed", 0)
    items.append(EvidenceItem(
        evidence_type="history",
        source_module="iteration_decision",
        source_field="n_iterations_completed",
        value=n_iter,
        interpretation=f"{n_iter} previous iteration(s) completed.",
    ))

    trend = history.get("metric_trend", "unknown")
    items.append(EvidenceItem(
        evidence_type="history",
        source_module="iteration_decision",
        source_field="metric_trend",
        value=trend,
        interpretation=f"Metric trend across iterations: {trend}.",
    ))

    best_so_far = history.get("best_metric_so_far")
    if best_so_far is not None:
        items.append(EvidenceItem(
            evidence_type="history",
            source_module="iteration_decision",
            source_field="best_metric_so_far",
            value=best_so_far,
            interpretation="Best metric value achieved across all iterations.",
        ))

    repeated = history.get("repeated_root_causes", [])
    if repeated:
        items.append(EvidenceItem(
            evidence_type="history",
            source_module="iteration_decision",
            source_field="repeated_root_causes",
            value=repeated,
            interpretation=f"Root causes that persist across iterations: {repeated}. May indicate a fundamental limitation.",
        ))

    tried_models = history.get("tried_model_families", [])
    if tried_models:
        items.append(EvidenceItem(
            evidence_type="history",
            source_module="iteration_decision",
            source_field="tried_model_families",
            value=tried_models,
            interpretation=f"Model families already explored: {tried_models}.",
        ))

    runtime = history.get("runtime_cost_summary")
    if runtime:
        items.append(EvidenceItem(
            evidence_type="history",
            source_module="iteration_decision",
            source_field="runtime_cost",
            value=runtime,
            interpretation="Cumulative compute cost across iterations.",
        ))

    failed = history.get("failed_trial_summary")
    if failed:
        items.append(EvidenceItem(
            evidence_type="history",
            source_module="iteration_decision",
            source_field="failed_trials",
            value=failed,
            interpretation="Cumulative trial failure summary.",
        ))

    logger.info("History evidence — %d items extracted", len(items))
    return items
