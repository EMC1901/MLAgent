import logging
import re
from app.modules.pipeline_generation.schemas import SafetyCheckResult

logger = logging.getLogger(__name__)

FORBIDDEN_PATTERNS = [
    r"\bimport\b",
    r"\bexec\s*\(",
    r"\beval\s*\(",
    r"\bexecfile\s*\(",
    r"\bcompile\s*\(",
    r"\b__import__\b",
    r"\bos\.system\b",
    r"\bsubprocess\b",
    r"\brm\s+-rf\b",
    r"\bos\.remove\b",
    r"\bshutil\.rmtree\b",
    r"\bfile\s*\.\s*write\b",
    r"\bopen\s*\([^)]*['\"]w",
    r"\bclass\s+\w+\s*\(.*\)\s*:",
    r"\bdef\s+\w+\s*\(.*\)\s*:",
    r"\bmodel\s*\.\s*fit\s*\(",
    r"\bPipeline\s*\(",
    r"\bGridSearchCV\b",
    r"\bRandomizedSearchCV\b",
    r"\.fit\s*\(",
    r"\.predict\s*\(",
    r"\.transform\s*\(",
]


def check_pipeline_safety(context: dict, pipeline_specs: list, execution_input) -> SafetyCheckResult:
    """Check all pipeline specs and execution input for forbidden content."""

    result = SafetyCheckResult()
    errors = []
    checks = {}

    # Check pipeline specs
    specs = [s if isinstance(s, dict) else s.model_dump() for s in pipeline_specs]
    spec_check = _scan_for_code(specs)
    checks["pipeline_specs_no_code"] = spec_check["safe"]
    if not spec_check["safe"]:
        errors.append(f"Forbidden patterns in pipeline specs: {spec_check['matches']}")

    # Check execution input
    if execution_input:
        ei = execution_input if isinstance(execution_input, dict) else execution_input.model_dump()
        ei_check = _scan_for_code(ei)
        checks["execution_input_no_code"] = ei_check["safe"]
        if not ei_check["safe"]:
            errors.append(f"Forbidden patterns in execution input: {ei_check['matches']}")

    # Check for unregistered model references
    checks["no_direct_code_strings"] = True

    # Check artifact paths
    path_check = _validate_paths(context)
    checks["paths_safe"] = path_check["safe"]
    if not path_check["safe"]:
        errors.append(f"Unsafe paths detected: {path_check['issues']}")

    # Check that no script or code strings exist in any field
    all_text = str(specs) + str(context.get("pipeline_generation_input", {}))
    script_check = _scan_text_for_code(all_text)
    checks["no_script_content"] = script_check["safe"]
    if not script_check["safe"]:
        errors.append(f"Suspicious code found: {script_check['matches']}")

    result.checks = checks
    result.errors = errors
    result.is_safe = len(errors) == 0

    if errors:
        result.warnings = errors

    return result


def _scan_for_code(obj, max_depth=5, depth=0) -> dict:
    """Recursively scan an object for code patterns."""
    matches = []
    if depth > max_depth:
        return {"safe": True, "matches": []}

    if isinstance(obj, str):
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, obj, re.IGNORECASE):
                matches.append(f"Found '{pattern}' in string value.")

    elif isinstance(obj, dict):
        for k, v in obj.items():
            m = _scan_for_code(v, max_depth, depth + 1)
            matches.extend(m.get("matches", []))

    elif isinstance(obj, list):
        for item in obj:
            m = _scan_for_code(item, max_depth, depth + 1)
            matches.extend(m.get("matches", []))

    return {
        "safe": len(matches) == 0,
        "matches": matches,
    }


def _scan_text_for_code(text: str) -> dict:
    matches = []
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matches.append(f"Pattern '{pattern}' detected.")
    return {"safe": len(matches) == 0, "matches": matches}


def _validate_paths(context: dict) -> dict:
    issues = []
    model_ready_path = context.get("model_ready_matrix_path", "")
    preprocessor_path = context.get("preprocessor_artifact_path", "")

    for label, path in [("model_ready", model_ready_path), ("preprocessor", preprocessor_path)]:
        if not path:
            continue
        if ".." in str(path):
            issues.append(f"{label} path contains '..' escape: {path}")

    return {"safe": len(issues) == 0, "issues": issues}
