import logging
from typing import Dict, Any, List, Tuple
from app.modules.iteration_decision.enums import (
    VALID_DECISIONS,
    VALID_CONFIDENCE_VALUES,
    VALID_TARGET_STAGES,
)

logger = logging.getLogger(__name__)

FORBIDDEN_FIELDS = {
    "python_code", "code", "script", "executable",
    "workflow_patch", "pipeline_patch", "model_fit_code",
    "train_code", "shell_command", "sql", "direct_execution",
}

CODE_PATTERNS = [
    "def ", "class ", "eval(", "exec(", "subprocess",
    "os.system", "shutil", "model.fit", "model.predict", "Pipeline(",
    "optuna.create_study", "__import__", "compile(", "globals()", "locals()",
]


def validate_decision(raw: Dict[str, Any]) -> Tuple[bool, List[str]]:
    issues: List[str] = []

    # Required top-level fields
    for field in ("decision", "reasoning", "confidence"):
        if field not in raw:
            issues.append(f"Missing required field: {field}")

    # Validate decision
    decision = raw.get("decision", "")
    if isinstance(decision, str):
        decision = decision.strip().lower()
        raw["decision"] = decision
    if decision not in VALID_DECISIONS:
        issues.append(f"Invalid decision: '{decision}'. Must be 'iterate' or 'stop'.")

    # Validate confidence
    if raw.get("confidence") not in VALID_CONFIDENCE_VALUES:
        issues.append(f"Invalid confidence: '{raw.get('confidence')}'.")

    # Validate reasoning structure
    reasoning = raw.get("reasoning") or {}
    if isinstance(reasoning, dict):
        for sub in ("task_completion", "performance_assessment", "gap_analysis", "root_cause", "improvement_potential", "final_reasoning_summary"):
            if not reasoning.get(sub):
                issues.append(f"reasoning.{sub} is missing or empty.")

        # Root cause dimension
        rc = reasoning.get("root_cause") or {}
        if isinstance(rc, dict):
            dim = rc.get("dimension", "")
            valid_dims = {"data_side", "feature_side", "model_side", "evaluation_side"}
            if dim and dim not in valid_dims:
                issues.append(f"Invalid root_cause.dimension: '{dim}'.")
            upstream = rc.get("upstream_stage_at_fault")
            if upstream and upstream not in VALID_TARGET_STAGES:
                issues.append(f"Invalid upstream_stage_at_fault: '{upstream}'.")

        # Improvement potential
        ip_ = reasoning.get("improvement_potential") or {}
        if isinstance(ip_, dict):
            valid_est = {"high", "moderate", "low", "none"}
            if ip_.get("estimate") not in valid_est:
                issues.append(f"Invalid improvement_potential.estimate: '{ip_.get('estimate')}'.")

    # Decision-specific validation
    if decision == "iterate":
        plan = raw.get("iteration_plan") or {}
        if not plan:
            issues.append("Decision is 'iterate' but iteration_plan is null or empty.")
        else:
            if plan.get("rerun_from_stage") not in VALID_TARGET_STAGES:
                issues.append(f"Invalid rerun_from_stage: '{plan.get('rerun_from_stage')}'.")
            if not plan.get("stage_changes"):
                issues.append("iteration_plan.stage_changes is empty — must specify what to change.")
            if not plan.get("stop_condition"):
                issues.append("iteration_plan.stop_condition is missing.")
        # stop_rationale should be null for iterate
        if raw.get("stop_rationale"):
            issues.append("Decision is 'iterate' but stop_rationale is populated.")

    elif decision == "stop":
        sr = raw.get("stop_rationale") or {}
        if not sr:
            issues.append("Decision is 'stop' but stop_rationale is null or empty.")
        else:
            valid_cats = {"target_achieved", "converged", "diminishing_returns", "resource_limit", "insoluble"}
            if sr.get("category") not in valid_cats:
                issues.append(f"Invalid stop_rationale.category: '{sr.get('category')}'.")
        # iteration_plan should be null for stop
        if raw.get("iteration_plan"):
            issues.append("Decision is 'stop' but iteration_plan is populated.")

    # Security scan
    security_issues = _scan_for_code(raw)
    issues.extend(security_issues)

    is_valid = len(issues) == 0
    if not is_valid:
        logger.warning("Decision validation failed — %d issue(s): %s",
                       len(issues), "; ".join(str(i) for i in issues[:5]))

    return is_valid, issues


def _scan_for_code(data: Any, path: str = "") -> List[str]:
    issues: List[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in FORBIDDEN_FIELDS:
                issues.append(f"Security: forbidden field '{path}.{key}'.")
            _scan_value(value, f"{path}.{key}", issues)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            _scan_value(item, f"{path}[{i}]", issues)
    elif isinstance(data, str):
        for pattern in CODE_PATTERNS:
            if pattern in data:
                issues.append(f"Security: code pattern '{pattern}' at {path}.")
    return issues


def _scan_value(value: Any, path: str, issues: List[str]):
    if isinstance(value, str):
        for pattern in CODE_PATTERNS:
            if pattern in value:
                issues.append(f"Security: code pattern '{pattern}' at {path}.")
    if isinstance(value, (dict, list)):
        issues.extend(_scan_for_code(value, path))
