import logging
from typing import Dict, Any, List
from app.modules.iteration_decision.schemas import EvidenceItem
from app.modules.iteration_decision.enums import EvidenceType

logger = logging.getLogger(__name__)


def extract_ml_evidence(metrics: Dict[str, Any]) -> List[EvidenceItem]:
    items: List[EvidenceItem] = []
    di = metrics.get("result_diagnosis_input_json") or {}

    # Metric summary
    metric_summary = di.get("metric_summary") or {}
    if metric_summary:
        items.append(EvidenceItem(
            evidence_type=EvidenceType.METRIC,
            source_module="metric_evaluation",
            source_field="best_metric_value",
            value=metric_summary.get("best_metric_value"),
            interpretation="Best primary metric value across all trials.",
        ))
        items.append(EvidenceItem(
            evidence_type=EvidenceType.METRIC,
            source_module="metric_evaluation",
            source_field="mean_metric_value",
            value=metric_summary.get("mean_metric_value"),
            interpretation=f"Mean metric across {metric_summary.get('n_trials_contributing', 0)} trials.",
        ))
        if metric_summary.get("std_metric_value") is not None:
            items.append(EvidenceItem(
                evidence_type=EvidenceType.METRIC,
                source_module="metric_evaluation",
                source_field="std_metric_value",
                value=metric_summary["std_metric_value"],
                interpretation="Standard deviation of metric across trials.",
            ))

    # Baseline
    baseline = di.get("baseline_comparison") or {}
    if baseline:
        direction = di.get("metric_direction", "minimize")
        abs_imp = baseline.get("absolute_improvement")
        items.append(EvidenceItem(
            evidence_type=EvidenceType.BASELINE,
            source_module="metric_evaluation",
            source_field="candidate_beats_baseline",
            value=baseline.get("candidate_beats_baseline"),
            interpretation="Whether best candidate outperforms best baseline.",
        ))
        if abs_imp is not None:
            improved = (direction == "minimize" and abs_imp < 0) or (direction == "maximize" and abs_imp > 0)
            items.append(EvidenceItem(
                evidence_type=EvidenceType.BASELINE,
                source_module="metric_evaluation",
                source_field="absolute_improvement",
                value=abs_imp,
                interpretation=f"Absolute improvement over baseline (improved={'yes' if improved else 'no'}).",
            ))

    # Fold stability
    stability = di.get("stability_summary") or {}
    if stability:
        items.append(EvidenceItem(
            evidence_type=EvidenceType.FOLD_STABILITY,
            source_module="metric_evaluation",
            source_field="mean_cv_std",
            value=stability.get("mean_cv_std"),
            interpretation="Mean CV standard deviation across trials.",
        ))
        items.append(EvidenceItem(
            evidence_type=EvidenceType.FOLD_STABILITY,
            source_module="metric_evaluation",
            source_field="max_cv_std",
            value=stability.get("max_cv_std"),
            interpretation="Maximum CV standard deviation across trials.",
        ))

    # Model ranking
    ranking = di.get("model_ranking") or []
    if ranking:
        top3 = []
        for r in ranking[:3]:
            if isinstance(r, dict):
                top3.append(f"{r.get('model_family', '?')}(rank={r.get('rank', '?')}, val={r.get('primary_metric_value', '?')})")
            else:
                top3.append(f"{getattr(r, 'model_family', '?')}(rank={getattr(r, 'rank', '?')})")
        items.append(EvidenceItem(
            evidence_type=EvidenceType.RANKING,
            source_module="metric_evaluation",
            source_field="model_ranking",
            value=top3,
            interpretation="Top 3 models by primary metric.",
        ))

    # Failed trials
    failed = di.get("failed_trials_summary") or {}
    if failed:
        n_success = failed.get("n_successful_trials", 0)
        n_failed = failed.get("n_failed_trials", 0)
        items.append(EvidenceItem(
            evidence_type=EvidenceType.PIPELINE_LOG,
            source_module="pipeline_execution",
            source_field="trials",
            value={"successful": n_success, "failed": n_failed},
            interpretation=f"Trial execution: {n_success} succeeded, {n_failed} failed.",
        ))

    logger.info("ML evidence — %d items extracted", len(items))
    return items
