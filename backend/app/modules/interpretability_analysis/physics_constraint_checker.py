import logging
import numpy as np
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Built-in physics constraints for common materials properties
DEFAULT_CONSTRAINTS = {
    "band_gap": {
        "description": "Band gap must be non-negative (>= 0 eV)",
        "check": lambda values: values >= 0,
        "severity": "critical",
    },
    "formation_energy": {
        "description": "Formation energy should be <= 0 eV/atom for stable compounds",
        "check": lambda values: values <= 0,
        "severity": "warning",
    },
    "bulk_modulus": {
        "description": "Bulk modulus must be non-negative (>= 0 GPa)",
        "check": lambda values: values >= 0,
        "severity": "critical",
    },
    "shear_modulus": {
        "description": "Shear modulus must be non-negative (>= 0 GPa)",
        "check": lambda values: values >= 0,
        "severity": "critical",
    },
    "thermal_conductivity": {
        "description": "Thermal conductivity must be non-negative (>= 0 W/mK)",
        "check": lambda values: values >= 0,
        "severity": "critical",
    },
    "electrical_conductivity": {
        "description": "Electrical conductivity must be non-negative (>= 0 S/m)",
        "check": lambda values: values >= 0,
        "severity": "critical",
    },
    "density": {
        "description": "Density must be positive (> 0 g/cm³)",
        "check": lambda values: values > 0,
        "severity": "critical",
    },
    "melting_point": {
        "description": "Melting point must be positive (> 0 K)",
        "check": lambda values: values > 0,
        "severity": "critical",
    },
}


def check_physics_constraints(
    y_pred,
    target_property: Optional[str] = None,
    prediction_target_name: Optional[str] = None,
    custom_constraints: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Check if predictions violate known physics constraints for the target property.

    Args:
        y_pred: Array of predicted values
        target_property: The target column name (e.g., "band_gap")
        prediction_target_name: Human-readable target name (e.g., "Band Gap")
        custom_constraints: User-provided constraint dict, merged with defaults

    Returns:
        Dict with constraints list and passed flag
    """
    if y_pred is None:
        return {"constraints": [], "passed": True}

    values = np.asarray(y_pred, dtype=float).flatten()

    # Determine which constraints to apply
    applicable = {}
    if custom_constraints:
        applicable = dict(custom_constraints)
    else:
        # Auto-match target property name to known constraints
        search_name = (target_property or "").lower().replace(" ", "_").replace("-", "_")
        if prediction_target_name:
            search_name = f"{search_name} {prediction_target_name.lower()}"

        for key, constraint in DEFAULT_CONSTRAINTS.items():
            if key in search_name or (prediction_target_name and key in prediction_target_name.lower()):
                applicable[key] = constraint

    if not applicable:
        logger.info("No physics constraints matched for target '%s'", target_property)
        return {"constraints": [], "passed": True}

    results = []
    all_passed = True

    for key, constraint in applicable.items():
        try:
            satisfied = constraint["check"](values)
            n_violations = int((~satisfied).sum())
            passed = n_violations == 0
            if not passed:
                all_passed = False

            # Get indices of worst violations (up to 10)
            violation_indices = []
            if n_violations > 0:
                violation_abs = np.where(~satisfied)[0]
                violation_indices = violation_abs[:10].tolist()

            results.append({
                "constraint_name": key,
                "description": constraint["description"],
                "expected": f"All values satisfy: {constraint['description'].split('(')[-1].rstrip(')') if '(' in constraint['description'] else constraint['description']}",
                "actual": f"{n_violations} of {len(values)} predictions violate the constraint" if n_violations > 0 else f"All {len(values)} predictions satisfy the constraint",
                "passed": passed,
                "severity": constraint.get("severity", "warning"),
                "n_violations": n_violations,
                "violation_rate": round(n_violations / len(values), 4) if len(values) > 0 else 0.0,
                "violating_sample_indices": violation_indices,
            })
        except Exception as e:
            logger.warning("Physics constraint check '%s' failed: %s", key, str(e))
            results.append({
                "constraint_name": key,
                "description": constraint.get("description", key),
                "passed": False,
                "severity": "warning",
                "error": str(e),
            })

    logger.info("Physics constraint check: %d/%d passed", sum(1 for r in results if r["passed"]), len(results))
    return {"constraints": results, "passed": all_passed}
