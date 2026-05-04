import logging
import re

logger = logging.getLogger(__name__)

# Patterns that must never appear in LLM output
FORBIDDEN_LLM_CONTENT = [
    r"\.fit\s*\(",
    r"\.predict\s*\(",
    r"\.transform\s*\(",
    r"\.fit_transform\s*\(",
    r"\bimport\b",
    r"\bdef\b\s+\w+\s*\(",
    r"\bclass\b\s+\w+\s*[:\(]",
    r"\bexec\s*\(",
    r"\beval\s*\(",
    r"\bcompile\s*\(",
    r"\bexecfile\s*\(",
    r"\b__import__\b",
    r"\bos\.system\b",
    r"\bsubprocess\b",
    r"\brm\s+-rf\b",
    r"\bos\.remove\b",
    r"\bshutil\.rmtree\b",
    r"```python",
    r"```",
    r"\bopen\s*\([^)]*['\"]w",
    r"\bsklearn\.",
    r"\bPipeline\s*\(",
    r"\bGridSearchCV\b",
    r"\bRandomizedSearchCV\b",
    r"\boptuna\.create_study\b",
]

# Fields that LLM must NOT include in output (approval-style fields)
FORBIDDEN_LLM_FIELDS = {
    "approval_status",
    "approved",
    "rejected",
    "conditional",
    "needs_improvement",
    "final_decision",
    "execution_allowed",
    "ready_for_execution",
    "modify_pipeline",
    "recommended_code",
    "python_code",
}

ALLOWED_REVIEW_STATUSES = {
    "advisory_completed",
    "advisory_failed",
    "advisory_unavailable",
}

ALLOWED_EXECUTION_IMPACTS = {"non_blocking", "potentially_blocking"}
ALLOWED_RISK_LEVELS = {"none", "low", "medium", "high"}
ALLOWED_CONFIDENCE_LEVELS = {"low", "medium", "high"}
ALLOWED_CHECKLIST_STATUSES = {"pass", "warning", "not_applicable"}


def validate_llm_review(parsed_data: dict, pipeline_specs: list) -> dict:
    """Validate LLM advisory review output. Returns validation dict with:
    - is_valid: bool
    - errors: list[str]
    - warnings: list[str]
    """
    errors = []
    warnings = []

    # --- 1. Scan for forbidden content (code, scripts) ---
    all_text = json_safe_str(parsed_data)
    for pattern in FORBIDDEN_LLM_CONTENT:
        if re.search(pattern, all_text, re.IGNORECASE):
            errors.append(f"Forbidden LLM content detected: pattern '{pattern}'.")

    # --- 2. Check for forbidden approval-style fields ---
    for key in FORBIDDEN_LLM_FIELDS:
        if key in parsed_data:
            warnings.append(
                f"LLM returned forbidden field '{key}'. "
                "It will be removed by the Normalizer."
            )

    # --- 3. Check for attempted pipeline modifications ---
    forbidden_mod_keys = {"pipeline_specs", "trial_plan", "execution_input", "search_space"}
    for key in forbidden_mod_keys:
        if key in parsed_data:
            errors.append(f"LLM attempted to modify '{key}', which is not allowed.")

    # --- 4. Validate standard fields if present ---
    review_status = parsed_data.get("review_status", "")
    if review_status and review_status not in ALLOWED_REVIEW_STATUSES:
        warnings.append(f"Unknown review_status '{review_status}', will be normalized.")

    exec_impact = parsed_data.get("execution_impact", "")
    if exec_impact and exec_impact not in ALLOWED_EXECUTION_IMPACTS:
        warnings.append(f"Unknown execution_impact '{exec_impact}', will be normalized.")

    risk_level = parsed_data.get("risk_level", "")
    if risk_level and risk_level not in ALLOWED_RISK_LEVELS:
        warnings.append(f"Unknown risk_level '{risk_level}', will be normalized.")

    conf_level = parsed_data.get("confidence_level", "")
    if conf_level and conf_level not in ALLOWED_CONFIDENCE_LEVELS:
        warnings.append(f"Unknown confidence_level '{conf_level}', will be normalized.")

    # --- 5. Validate checklist items ---
    checklist = parsed_data.get("checklist", [])
    if isinstance(checklist, list):
        for item in checklist:
            if isinstance(item, dict):
                status = item.get("status", "")
                if status and status not in ALLOWED_CHECKLIST_STATUSES:
                    warnings.append(
                        f"Checklist item '{item.get('dimension', '?')}' has "
                        f"invalid status '{status}', will be normalized."
                    )

    is_valid = len(errors) == 0

    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
    }


def json_safe_str(obj) -> str:
    """Convert any object to a string for pattern scanning."""
    try:
        import json as _json
        return _json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return str(obj)
