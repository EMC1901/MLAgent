import logging
import re
from typing import Dict, Any, Tuple, List

from app.modules.workflow_refinement.enums import (
    VALID_DECISIONS,
    VALID_CONFIDENCE_LEVELS,
    VALID_RERUN_STAGES,
)

logger = logging.getLogger(__name__)

FORBIDDEN_PATTERNS = [
    "import ",
    "def ",
    "class ",
    "eval(",
    "exec(",
    "subprocess",
    "os.system",
    "open(",
    "write(",
    "delete ",
    "remove(",
    "shutil",
    "model.fit",
    "model.predict",
    "Pipeline(",
    "optuna.create_study",
    "__import__",
    "compile(",
]

FORBIDDEN_FIELDS = [
    "code",
    "python_code",
    "script",
    "shell_command",
    "sql",
    "workflow_patch",
    "pipeline_patch",
    "registry_patch",
    "model_fit_code",
    "train_code",
    "executable",
    "direct_execution",
]


def validate_workflow_refinement_decision(
    parsed: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """Validate the parsed LLM workflow refinement decision."""
    issues: List[str] = []

    decision_obj = parsed.get("workflow_refinement_decision") or {}
    decision = decision_obj.get("decision")

    if not decision:
        issues.append("Missing workflow_refinement_decision.decision")
    elif decision not in VALID_DECISIONS:
        issues.append(
            f"Invalid decision '{decision}'. Must be one of: {VALID_DECISIONS}"
        )

    confidence = decision_obj.get("decision_confidence_level")
    if confidence and confidence not in VALID_CONFIDENCE_LEVELS:
        issues.append(f"Invalid decision_confidence_level '{confidence}'")

    rerun_stage = decision_obj.get("recommended_rerun_from_stage")
    if rerun_stage and rerun_stage not in VALID_RERUN_STAGES:
        issues.append(f"Invalid recommended_rerun_from_stage '{rerun_stage}'")

    reasoning = parsed.get("decision_reasoning")
    if not reasoning or not isinstance(reasoning, dict):
        issues.append("Missing or invalid decision_reasoning")

    if decision == "proceed_next_stage":
        rwp = parsed.get("revised_workflow_plan")
        if rwp is not None:
            issues.append(
                "revised_workflow_plan must be null when decision is proceed_next_stage"
            )

    if decision == "iterate_refinement":
        rwp = parsed.get("revised_workflow_plan")
        if not rwp:
            issues.append(
                "revised_workflow_plan is required when decision is iterate_refinement"
            )
        irp = parsed.get("iteration_rerun_plan")
        if not irp:
            issues.append(
                "iteration_rerun_plan is required when decision is iterate_refinement"
            )

    evidence = parsed.get("evidence_used")
    if evidence is not None and not isinstance(evidence, list):
        issues.append("evidence_used must be a list")

    return len(issues) == 0, issues


def scan_for_forbidden_content(data: Any, path: str = "root") -> List[str]:
    """Recursively scan the data for forbidden content patterns."""
    issues: List[str] = []

    if isinstance(data, str):
        data_lower = data.lower()
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.lower() in data_lower:
                issues.append(f"Forbidden pattern '{pattern}' found at {path}")
        for field in FORBIDDEN_FIELDS:
            if re.search(r'\b' + re.escape(field) + r'\b', data_lower):
                issues.append(f"Forbidden field name '{field}' found at {path}")

    elif isinstance(data, dict):
        for key, value in data.items():
            if key in FORBIDDEN_FIELDS:
                issues.append(f"Forbidden field '{key}' found at {path}")
            issues.extend(scan_for_forbidden_content(value, f"{path}.{key}"))

    elif isinstance(data, list):
        for i, item in enumerate(data):
            issues.extend(scan_for_forbidden_content(item, f"{path}[{i}]"))

    return issues
