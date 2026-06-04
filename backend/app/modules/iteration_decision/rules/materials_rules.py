import logging
from typing import Dict, Any, List
from app.modules.iteration_decision.schemas import SystemChecks

logger = logging.getLogger(__name__)

SMALL_SAMPLE_THRESHOLD = 200
LOW_FEATURE_THRESHOLD = 10
HIGH_DROPPED_FEATURE_RATIO = 0.50

# Properties with known physical constraints
PHYSICS_CONSTRAINTS = {
    "band_gap": {"min": 0.0, "description": "Band gap must be non-negative."},
    "formation_energy": {"max": 0.0, "description": "Formation energy should typically be negative for stable compounds."},
    "bulk_modulus": {"min": 0.0, "description": "Bulk modulus must be positive."},
    "shear_modulus": {"min": 0.0, "description": "Shear modulus must be positive."},
    "thermal_conductivity": {"min": 0.0, "description": "Thermal conductivity must be non-negative."},
    "electrical_conductivity": {"min": 0.0, "description": "Electrical conductivity must be non-negative."},
}


def run_materials_rules(upstream: Dict[str, Any], metrics: Dict[str, Any]) -> SystemChecks:
    checks = SystemChecks()

    # Check physics constraints for the target property
    ti = upstream.get("task_interpretation", {}).get("interpretation_json") or {}
    target = (ti.get("prediction_target") or ti.get("target_property") or "").lower().replace(" ", "_")

    di = metrics.get("result_diagnosis_input_json") or {}
    best_val = None
    metric_summary = di.get("metric_summary") or {}
    if metric_summary:
        best_val = metric_summary.get("best_metric_value")

    if target in PHYSICS_CONSTRAINTS:
        constraint = PHYSICS_CONSTRAINTS[target]
        if best_val is not None:
            violated = False
            if "min" in constraint and best_val < constraint["min"]:
                violated = True
            if "max" in constraint and best_val > constraint["max"]:
                violated = True
            if violated:
                checks.physics_constraint_violated = True
                checks.warnings.append(
                    f"Physics constraint violated for '{target}': {constraint['description']} (best value={best_val:.4f})."
                )

    # Check chemical space coverage from dataset profile
    dp = upstream.get("dataset_profile", {}).get("profile_json") or {}
    n_samples = dp.get("n_samples") or dp.get("row_count")
    if n_samples is not None and n_samples < SMALL_SAMPLE_THRESHOLD:
        checks.small_sample_warning = True
        checks.chemical_space_coverage_low = True
        checks.warnings.append(f"Small dataset ({n_samples} samples). Chemical space coverage is likely limited.")

    # Check feature materials relevance
    fp = upstream.get("feature_preprocessing", {}).get("preprocessing_json") or {}
    n_final = fp.get("n_final_features")
    if n_final is not None and n_final < LOW_FEATURE_THRESHOLD:
        checks.feature_count_low = True
        checks.feature_materials_relevance_low = True
        checks.warnings.append(
            f"Low feature count ({n_final}). May lack sufficient materials descriptors for the target property."
        )

    # Check if many features were dropped
    n_initial = fp.get("n_initial_features")
    n_dropped = fp.get("n_features_dropped")
    if n_initial and n_dropped and n_initial > 0:
        dropped_ratio = n_dropped / n_initial
        if dropped_ratio > HIGH_DROPPED_FEATURE_RATIO:
            checks.many_features_dropped = True
            checks.warnings.append(f"High feature drop ratio ({dropped_ratio:.1%}). Review if materials-relevant features were removed.")

    triggered = [k for k, v in checks.model_dump().items()
                 if v is True and k not in ("warnings", "additional_checks")]
    logger.info("Materials rules — %d triggered (%s)",
                 len(triggered), ", ".join(triggered) if triggered else "none")
    return checks
