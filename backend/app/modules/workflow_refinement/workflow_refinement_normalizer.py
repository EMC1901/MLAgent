import logging
from typing import Dict, Any

from app.modules.workflow_refinement.enums import (
    VALID_DECISIONS,
    VALID_CONFIDENCE_LEVELS,
    VALID_RERUN_STAGES,
)

logger = logging.getLogger(__name__)


def normalize_workflow_refinement_result(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize the LLM output to canonical forms."""

    decision_obj = parsed.get("workflow_refinement_decision")
    if isinstance(decision_obj, dict):
        decision = decision_obj.get("decision", "")
        if decision and decision not in VALID_DECISIONS:
            decision_obj["decision"] = _normalize_decision(decision)

        conf = decision_obj.get("decision_confidence_level", "")
        if conf and conf not in VALID_CONFIDENCE_LEVELS:
            decision_obj["decision_confidence_level"] = _normalize_confidence(conf)

        rerun = decision_obj.get("recommended_rerun_from_stage")
        if rerun and rerun not in VALID_RERUN_STAGES:
            decision_obj["recommended_rerun_from_stage"] = _normalize_rerun_stage(rerun)

    decision = (decision_obj or {}).get("decision", "iterate_refinement")
    if decision == "proceed_next_stage":
        parsed.setdefault("revised_workflow_plan", None)
        parsed.setdefault("iteration_rerun_plan", None)

    confidence = parsed.get("confidence_level", "")
    if confidence and confidence not in VALID_CONFIDENCE_LEVELS:
        parsed["confidence_level"] = _normalize_confidence(confidence)

    rwp = parsed.get("revised_workflow_plan")
    if isinstance(rwp, dict):
        rwp["status"] = "planned_by_refinement"
        rwp["planning_mode"] = "llm_refinement"

    irp = parsed.get("iteration_rerun_plan")
    if isinstance(irp, dict):
        _normalize_iteration_rerun_plan(irp)

    return parsed


def _normalize_iteration_rerun_plan(irp: Dict[str, Any]) -> None:
    """Fix LLM output where objects are used instead of plain strings/numbers."""
    for key in ("reuse_artifacts", "invalidate_artifacts", "expected_improvement_targets", "rerun_stages"):
        val = irp.get(key)
        if isinstance(val, list):
            irp[key] = _normalize_string_list(val)

    threshold = irp.get("minimum_improvement_threshold")
    if threshold is not None and isinstance(threshold, dict):
        for k in ("target", "threshold", "value", "minimum_improvement"):
            v = threshold.get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                irp["minimum_improvement_threshold"] = float(v)
                return
        irp["minimum_improvement_threshold"] = None


def _normalize_string_list(items: list) -> list:
    result = []
    for item in items:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            parts = []
            for k in ("artifact_type", "target", "name", "stage", "change"):
                v = item.get(k)
                if isinstance(v, str) and v.strip():
                    parts.append(v.strip())
            if not parts:
                parts.append(str(item))
            result.append(": ".join(parts))
        else:
            result.append(str(item))
    return result


def _normalize_decision(raw: str) -> str:
    raw_lower = raw.lower().replace(" ", "_").replace("-", "_")
    if "proceed" in raw_lower or "final" in raw_lower or "next" in raw_lower:
        return "proceed_next_stage"
    if "iterate" in raw_lower or "refine" in raw_lower or "revise" in raw_lower:
        return "iterate_refinement"
    return "iterate_refinement"


def _normalize_confidence(raw: str) -> str:
    raw_lower = raw.lower()
    if raw_lower in VALID_CONFIDENCE_LEVELS:
        return raw_lower
    if "high" in raw_lower:
        return "high"
    if "low" in raw_lower:
        return "low"
    return "medium"


def _normalize_rerun_stage(raw: str) -> str:
    raw_lower = raw.lower().replace(" ", "_").replace("-", "_")
    stage_map = {
        "workflow": "workflow_planning",
        "workflow_plan": "workflow_planning",
        "planning": "workflow_planning",
        "feature": "feature_engineering",
        "features": "feature_engineering",
        "feature_eng": "feature_engineering",
        "preprocessing": "feature_preprocessing",
        "feature_preprocess": "feature_preprocessing",
        "model_search_context": "model_search_context",
        "search_context": "model_search_context",
        "model": "model_search_context",
        "models": "model_search_context",
        "hpo": "model_search_context",
        "pipeline": "pipeline_generation",
        "pipeline_gen": "pipeline_generation",
        "execution": "pipeline_execution",
        "train": "pipeline_execution",
        "metric": "metric_evaluation",
        "evaluation": "metric_evaluation",
    }
    for key, value in stage_map.items():
        if key in raw_lower:
            return value
    if raw_lower in VALID_RERUN_STAGES:
        return raw_lower
    return "workflow_planning"
