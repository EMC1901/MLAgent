import logging
from typing import Dict, Any, Optional, List, Union

from app.modules.workflow_refinement.enums import RerunStage

logger = logging.getLogger(__name__)

STAGE_ORDER = [
    RerunStage.WORKFLOW_PLANNING,
    RerunStage.FEATURE_ENGINEERING,
    RerunStage.FEATURE_PREPROCESSING,
    RerunStage.MODEL_SEARCH_CONTEXT,
    RerunStage.MODEL_SEARCH,
    RerunStage.PIPELINE_GENERATION,
    RerunStage.PIPELINE_EXECUTION,
    RerunStage.METRIC_EVALUATION,
]


def _normalize_string_list(items: Any) -> List[str]:
    """Normalize LLM output to a list of strings. LLMs often output objects like
    {'artifact_type': '...', 'reason': '...'} instead of plain strings."""
    if not items:
        return []
    if not isinstance(items, list):
        return []
    result: List[str] = []
    for item in items:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            parts = []
            for key in ("artifact_type", "target", "name", "stage", "change"):
                val = item.get(key)
                if isinstance(val, str) and val.strip():
                    parts.append(val.strip())
            if not parts:
                parts.append(str(item))
            result.append(": ".join(parts))
        else:
            result.append(str(item))
    return result


def _normalize_float(value: Any) -> Optional[float]:
    """Normalize LLM output to a float. LLMs sometimes output objects like
    {'metric': 'cv_std', 'current': 0.15, 'target': 0.10} instead of a plain number."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, bool):
            return None
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    if isinstance(value, dict):
        for key in ("target", "threshold", "value", "minimum_improvement"):
            v = value.get(key)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return float(v)
            if isinstance(v, str):
                try:
                    return float(v)
                except (ValueError, TypeError):
                    pass
        return None
    return None


def build_iteration_rerun_plan(
    llm_rerun_plan: Optional[Dict[str, Any]],
    decision: str,
    recommended_rerun_from_stage: Optional[str],
    llm_reasoning: str = "",
) -> Dict[str, Any]:
    """Build the iteration rerun plan from LLM output, with defaults and normalization."""

    if decision == "proceed_next_stage" or not llm_rerun_plan:
        return {
            "next_iteration_index": 0,
            "recommended_rerun_from_stage": None,
            "rerun_stages": [],
            "reuse_artifacts": [],
            "invalidate_artifacts": [],
            "expected_improvement_targets": [],
            "minimum_improvement_threshold": None,
            "stop_after_next_iteration_if_no_gain": True,
            "reasoning": "",
        }

    rerun_stages = _normalize_string_list(llm_rerun_plan.get("rerun_stages"))

    if not rerun_stages and recommended_rerun_from_stage:
        rerun_stages = _derive_rerun_stages(recommended_rerun_from_stage)

    return {
        "next_iteration_index": _normalize_int(llm_rerun_plan.get("next_iteration_index"), 1),
        "recommended_rerun_from_stage": recommended_rerun_from_stage,
        "rerun_stages": rerun_stages,
        "reuse_artifacts": _normalize_string_list(llm_rerun_plan.get("reuse_artifacts")),
        "invalidate_artifacts": _normalize_string_list(llm_rerun_plan.get("invalidate_artifacts")),
        "expected_improvement_targets": _normalize_string_list(
            llm_rerun_plan.get("expected_improvement_targets")
        ),
        "minimum_improvement_threshold": _normalize_float(
            llm_rerun_plan.get("minimum_improvement_threshold")
        ),
        "stop_after_next_iteration_if_no_gain": (
            llm_rerun_plan.get("stop_after_next_iteration_if_no_gain", True)
            if isinstance(llm_rerun_plan.get("stop_after_next_iteration_if_no_gain"), bool)
            else True
        ),
        "reasoning": llm_rerun_plan.get("reasoning") or llm_reasoning,
    }


def _normalize_int(value: Any, default: int = 0) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    return default


def _derive_rerun_stages(entry_stage: str) -> List[str]:
    """Derive all stages that need to rerun given an entry point."""
    try:
        idx = STAGE_ORDER.index(entry_stage)
        return STAGE_ORDER[idx:]
    except ValueError:
        return STAGE_ORDER
