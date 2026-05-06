import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

STRATEGY_SECTIONS = [
    "feature_strategy",
    "model_strategy",
    "hpo_strategy",
    "validation_strategy",
    "evaluation_strategy",
    "data_strategy",
    "interpretability_strategy",
]


def build_workflow_plan_delta(
    original_plan: Optional[Dict[str, Any]],
    revised_plan: Optional[Dict[str, Any]],
    refinement_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the delta/diff between original and revised workflow plans."""

    if not original_plan or not revised_plan:
        return {
            "changed_sections": [],
            "preserved_sections": [],
            "feature_strategy_delta": None,
            "model_strategy_delta": None,
            "hpo_strategy_delta": None,
            "validation_strategy_delta": None,
            "evaluation_strategy_delta": None,
            "change_reason_map": {},
            "diagnosis_to_change_map": {},
            "rejected_or_unsafe_changes": [],
        }

    changed = []
    preserved = []

    for section in STRATEGY_SECTIONS:
        orig = original_plan.get(section)
        rev = revised_plan.get(section)
        if orig != rev:
            changed.append(section)
        else:
            preserved.append(section)

    meta = refinement_metadata or {}
    if meta:
        changed_from_meta = meta.get("changed_sections") or []
        preserved_from_meta = meta.get("preserved_sections") or []
        for s in changed_from_meta:
            if s not in changed:
                changed.append(s)
        for s in preserved_from_meta:
            if s not in preserved and s not in changed:
                preserved.append(s)

    delta: Dict[str, Any] = {
        "changed_sections": changed,
        "preserved_sections": preserved,
        "feature_strategy_delta": _section_diff(
            (original_plan.get("feature_strategy") or {}),
            (revised_plan.get("feature_strategy") or {}),
        ),
        "model_strategy_delta": _section_diff(
            (original_plan.get("model_strategy") or {}),
            (revised_plan.get("model_strategy") or {}),
        ),
        "hpo_strategy_delta": _section_diff(
            (original_plan.get("hpo_strategy") or {}),
            (revised_plan.get("hpo_strategy") or {}),
        ),
        "validation_strategy_delta": _section_diff(
            (original_plan.get("validation_strategy") or {}),
            (revised_plan.get("validation_strategy") or {}),
        ),
        "evaluation_strategy_delta": _section_diff(
            (original_plan.get("evaluation_strategy") or {}),
            (revised_plan.get("evaluation_strategy") or {}),
        ),
        "change_reason_map": {},
        "diagnosis_to_change_map": {},
        "rejected_or_unsafe_changes": [],
    }

    return delta


def _section_diff(original: Dict[str, Any], revised: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Compute a simple diff showing what was added, removed, or changed."""
    all_keys = set(list(original.keys()) + list(revised.keys()))
    added = {}
    removed = {}
    changed_fields = {}

    for key in all_keys:
        orig_val = original.get(key)
        rev_val = revised.get(key)
        if key not in original and key in revised:
            added[key] = rev_val
        elif key in original and key not in revised:
            removed[key] = orig_val
        elif orig_val != rev_val:
            changed_fields[key] = {"from": orig_val, "to": rev_val}

    if not added and not removed and not changed_fields:
        return None

    return {
        "added": added,
        "removed": removed,
        "changed": changed_fields,
    }
