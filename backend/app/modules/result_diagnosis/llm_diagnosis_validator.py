import logging
from typing import Dict, Any, List, Tuple
from app.modules.result_diagnosis.enums import (
    VALID_DIAGNOSIS_TYPES,
    VALID_SEVERITY_VALUES,
    VALID_CONFIDENCE_VALUES,
    VALID_EVIDENCE_STRENGTH_VALUES,
    VALID_TARGET_STAGES,
    VALID_RECOMMENDATION_TYPES,
    DIAGNOSIS_TYPE_ALIASES,
)

logger = logging.getLogger(__name__)

FORBIDDEN_FIELDS = {
    "python_code", "code", "script", "executable",
    "workflow_patch", "pipeline_patch", "model_fit_code",
    "train_code", "shell_command", "sql", "direct_execution",
}

CODE_PATTERNS = [
    "import ", "def ", "class ", "eval(", "exec(", "subprocess",
    "os.system", "open(", "write(", "delete", "remove", "shutil",
    "model.fit", "model.predict", "Pipeline(", "optuna.create_study",
    "__import__", "compile(", "globals()", "locals()",
]


def validate_llm_diagnosis(raw_diagnosis: Dict[str, Any]) -> Tuple[bool, List[str]]:
    issues: List[str] = []

    # Check required top-level fields
    required_fields = ["overall_assessment", "diagnostic_findings"]
    for field in required_fields:
        if field not in raw_diagnosis:
            issues.append(f"Missing required field: {field}")

    # Validate overall_assessment
    oa = raw_diagnosis.get("overall_assessment") or {}
    if isinstance(oa, dict):
        valid_perf = {"excellent", "acceptable", "weak", "failed"}
        if oa.get("performance_level") not in valid_perf:
            issues.append(f"Invalid performance_level: {oa.get('performance_level')}")
        valid_imp = {"strong", "moderate", "weak", "none", "unknown"}
        if oa.get("baseline_improvement_level") not in valid_imp:
            issues.append(f"Invalid baseline_improvement_level: {oa.get('baseline_improvement_level')}")
        valid_stab = {"stable", "moderately_unstable", "unstable", "unknown"}
        if oa.get("stability_level") not in valid_stab:
            issues.append(f"Invalid stability_level: {oa.get('stability_level')}")
        if oa.get("confidence_level") not in VALID_CONFIDENCE_VALUES:
            issues.append(f"Invalid overall confidence_level: {oa.get('confidence_level')}")

    # Validate diagnostic_findings
    findings = raw_diagnosis.get("diagnostic_findings") or []
    if not isinstance(findings, list):
        issues.append("diagnostic_findings must be a list")
    else:
        for i, finding in enumerate(findings):
            if not isinstance(finding, dict):
                issues.append(f"Finding {i} is not an object")
                continue
            raw_type = finding.get("diagnosis_type", "")
            if raw_type not in VALID_DIAGNOSIS_TYPES and raw_type not in DIAGNOSIS_TYPE_ALIASES:
                issues.append(f"Finding {i}: invalid diagnosis_type '{raw_type}'")
            if finding.get("severity") not in VALID_SEVERITY_VALUES:
                issues.append(f"Finding {i}: invalid severity '{finding.get('severity')}'")
            if finding.get("evidence_strength") not in VALID_EVIDENCE_STRENGTH_VALUES:
                issues.append(f"Finding {i}: invalid evidence_strength '{finding.get('evidence_strength')}'")
            if finding.get("confidence_level") not in VALID_CONFIDENCE_VALUES:
                issues.append(f"Finding {i}: invalid confidence_level '{finding.get('confidence_level')}'")
            if not finding.get("evidence_items"):
                issues.append(f"Finding {i}: missing evidence_items — every finding must include evidence")

    # Validate refinement_recommendations
    recommendations = raw_diagnosis.get("refinement_recommendations") or []
    if isinstance(recommendations, list):
        for i, rec in enumerate(recommendations):
            if not isinstance(rec, dict):
                continue
            if rec.get("target_stage") not in VALID_TARGET_STAGES:
                issues.append(f"Recommendation {i}: invalid target_stage '{rec.get('target_stage')}'")
            if rec.get("recommendation_type") not in VALID_RECOMMENDATION_TYPES:
                issues.append(f"Recommendation {i}: invalid recommendation_type '{rec.get('recommendation_type')}'")

    # Validate confidence_level
    if raw_diagnosis.get("confidence_level") not in VALID_CONFIDENCE_VALUES:
        issues.append(f"Invalid top-level confidence_level: {raw_diagnosis.get('confidence_level')}")

    # Security scan
    security_issues = _scan_for_code(raw_diagnosis)
    issues.extend(security_issues)

    is_valid = len(issues) == 0
    if not is_valid:
        logger.warning("LLM diagnosis validation failed: %s", issues)

    return is_valid, issues


def _scan_for_code(data: Any, path: str = "") -> List[str]:
    issues: List[str] = []

    if isinstance(data, dict):
        for key, value in data.items():
            if key in FORBIDDEN_FIELDS:
                issues.append(f"Security: forbidden field '{path}.{key}' found in LLM output")
            _scan_value_for_code(value, f"{path}.{key}", issues)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            _scan_value_for_code(item, f"{path}[{i}]", issues)
    elif isinstance(data, str):
        for pattern in CODE_PATTERNS:
            if pattern in data:
                issues.append(f"Security: code pattern '{pattern}' found at {path}")

    return issues


def _scan_value_for_code(value: Any, path: str, issues: List[str]):
    for pattern in CODE_PATTERNS:
        if isinstance(value, str) and pattern in value:
            issues.append(f"Security: code pattern '{pattern}' found at {path}")
    if isinstance(value, (dict, list)):
        issues.extend(_scan_for_code(value, path))
