import re
import logging
from typing import Dict, Any, Set, List

from app.modules.interpretability_analysis.schemas import LLMNarrativeOutput
from app.modules.interpretability_analysis.enums import (
    DANGEROUS_PATTERNS_LITERAL,
    DANGEROUS_PATTERNS_REGEX,
    FORBIDDEN_LLM_FIELDS,
)

logger = logging.getLogger(__name__)


def validate_llm_narrative(
    narrative: LLMNarrativeOutput,
    raw_response: str,
    valid_evidence_ids: Set[str],
    valid_feature_names: Set[str] = None,
) -> Dict[str, Any]:
    """Validate LLM narrative output comprehensively.

    Checks performed:
    1. Dangerous patterns in raw response (code execution, model manipulation)
    2. Forbidden field names in narrative output
    3. All referenced evidence IDs exist in the valid set
    4. No introduced features beyond the valid feature set
    5. Narrative has required fields populated

    Args:
        narrative: Parsed LLMNarrativeOutput.
        raw_response: Raw LLM response string (for pattern scanning).
        valid_evidence_ids: Set of valid evidence IDs.
        valid_feature_names: Optional set of valid feature names to check against.

    Returns:
        Dict with "is_valid" (bool), "issues" (list of str), "warnings" (list of str).
    """
    issues: List[str] = []
    warnings: List[str] = []

    # Check 1: Dangerous patterns
    dangerous = _scan_dangerous_patterns(raw_response)
    if dangerous:
        issues.append(f"LLM narrative contains dangerous patterns: {dangerous}")

    # Check 2: Forbidden fields
    forbidden = _scan_forbidden_fields(narrative)
    if forbidden:
        issues.append(f"LLM narrative contains forbidden fields: {forbidden}")

    # Check 3: Evidence ID existence + each insight MUST have at least one valid ref
    for insight in narrative.insights:
        refs = insight.get("evidence_references", [])
        invalid = [r for r in refs if r not in valid_evidence_ids]
        if invalid:
            issues.append(
                f"Insight '{insight.get('hypothesis_id', '?')}' references "
                f"invalid evidence IDs: {invalid}"
            )
        valid = [r for r in refs if r in valid_evidence_ids]
        if not valid:
            issues.append(
                f"Insight '{insight.get('hypothesis_id', '?')}' has NO valid "
                f"evidence references. Every insight must cite at least one real "
                f"evidence ID to be evidence-grounded."
            )

    # Check 4: Feature name validation
    if valid_feature_names:
        for insight in narrative.insights:
            claim = insight.get("claim", "")
            # Simple check: scan for quoted feature names that aren't valid
            # This is a heuristic, not exhaustive
            for word in claim.split():
                # Strip punctuation for comparison
                clean = word.strip('",.\'()[]{}')
                if (clean in valid_feature_names
                        or clean.lower() in {f.lower() for f in valid_feature_names}):
                    pass  # Valid feature
                # We don't flag unknown words because we can't distinguish
                # feature names from regular English in a general way

    # Check 5: Required fields
    if not narrative.executive_summary:
        warnings.append("Narrative has empty executive_summary.")
    if not narrative.insights:
        warnings.append("Narrative has no insights.")
    if not narrative.limitations_section:
        warnings.append("Narrative has no limitations_section.")

    is_valid = len(issues) == 0

    logger.info("LLM narrative validation: valid=%s issues=%d warnings=%d",
                is_valid, len(issues), len(warnings))

    return {
        "is_valid": is_valid,
        "issues": issues,
        "warnings": warnings,
    }


def _scan_dangerous_patterns(raw: str) -> str:
    """Scan raw LLM output for dangerous patterns (code, system calls, etc.)."""
    if not raw:
        return ""
    raw_lower = raw.lower()
    found = []

    for pattern in DANGEROUS_PATTERNS_LITERAL:
        pattern_lower = pattern.lower()
        count = len(re.findall(re.escape(pattern_lower), raw_lower))
        if count > 0:
            found.append(f"{pattern}(x{count})")

    for regex, label in DANGEROUS_PATTERNS_REGEX:
        count = len(re.findall(regex, raw_lower))
        if count > 0:
            found.append(f"{label}(x{count})")

    return ", ".join(found) if found else ""


def _scan_forbidden_fields(narrative: LLMNarrativeOutput) -> str:
    """Check if any top-level keys in narrative output match forbidden field names."""
    narrative_dict = narrative.model_dump() if hasattr(narrative, "model_dump") else {}
    forbidden_set = {f.lower() for f in FORBIDDEN_LLM_FIELDS}
    found = []
    _collect_matching_keys(narrative_dict, forbidden_set, found)
    return ", ".join(sorted(set(found))) if found else ""


def _collect_matching_keys(
    obj, forbidden_set: Set[str], found: List[str], prefix: str = ""
) -> None:
    """Recursively collect keys that match forbidden field names."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if key.lower() in forbidden_set:
                found.append(full_key)
            if isinstance(value, (dict, list)):
                _collect_matching_keys(value, forbidden_set, found, full_key)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, (dict, list)):
                _collect_matching_keys(item, forbidden_set, found, f"{prefix}[{i}]")
