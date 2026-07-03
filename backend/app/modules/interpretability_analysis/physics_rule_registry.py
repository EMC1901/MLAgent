import logging
import numpy as np
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PhysicsConstraintRule:
    """Single physics constraint with metadata."""
    constraint_name: str
    description: str
    check_fn: Callable[[np.ndarray], np.ndarray]
    severity: str  # "info", "warning", "critical"
    target_patterns: List[str] = field(default_factory=list)
    feature_semantics: Dict[str, str] = field(default_factory=dict)
    domain_prior: Optional[Dict[str, Any]] = None


class PhysicsRuleRegistry:
    """Extensible registry for physics constraints, feature semantics, and domain priors.

    Singleton pattern — use `get_registry()` to access the shared instance.
    Supports custom constraint injection at runtime.

    Example:
        registry = get_registry()
        registry.register_constraint(PhysicsConstraintRule(
            constraint_name="custom_rule",
            description="My custom check",
            check_fn=lambda v: v > 0,
            severity="warning",
            target_patterns=["my_target"],
        ))
    """

    def __init__(self):
        self._constraints: Dict[str, PhysicsConstraintRule] = {}
        self._feature_semantics: Dict[str, Dict[str, Any]] = {}
        self._domain_priors: List[Dict[str, Any]] = []
        self._register_defaults()

    def register_constraint(self, rule: PhysicsConstraintRule) -> None:
        """Register a physics constraint rule."""
        if not rule.constraint_name:
            raise ValueError("Constraint name cannot be empty")
        if not callable(rule.check_fn):
            raise ValueError(f"check_fn must be callable for constraint '{rule.constraint_name}'")
        valid_severities = {"info", "warning", "critical"}
        if rule.severity not in valid_severities:
            logger.warning(
                "Constraint '%s' has invalid severity '%s', defaulting to 'warning'",
                rule.constraint_name, rule.severity)
            rule.severity = "warning"
        self._constraints[rule.constraint_name] = rule
        logger.info("Registered physics constraint: %s (severity=%s)",
                     rule.constraint_name, rule.severity)

    def register_feature_semantics(
        self, feature_pattern: str, semantics: Dict[str, Any]
    ) -> None:
        """Register feature-level semantics (e.g., expected relationships, units)."""
        if not feature_pattern:
            raise ValueError("feature_pattern cannot be empty")
        self._feature_semantics[feature_pattern] = semantics
        logger.info("Registered feature semantics for pattern '%s'", feature_pattern)

    def register_custom_constraints(self, custom: Dict[str, Any]) -> None:
        """Register constraints from a user-provided dict.

        Format: {constraint_name: {check: callable, description: str, severity: str, ...}}
        """
        if not custom:
            return
        for name, spec in custom.items():
            if not isinstance(spec, dict):
                logger.warning("Skipping custom constraint '%s': spec is not a dict", name)
                continue
            check_fn = spec.get("check")
            if not callable(check_fn):
                logger.warning(
                    "Skipping custom constraint '%s': 'check' must be callable", name)
                continue
            rule = PhysicsConstraintRule(
                constraint_name=name,
                description=spec.get("description", name),
                check_fn=check_fn,
                severity=spec.get("severity", "warning"),
                target_patterns=spec.get("target_patterns", [name]),
                feature_semantics=spec.get("feature_semantics", {}),
                domain_prior=spec.get("domain_prior"),
            )
            self.register_constraint(rule)

    def unregister_constraint(self, constraint_name: str) -> bool:
        """Remove a constraint by name. Returns True if removed."""
        if constraint_name in self._constraints:
            del self._constraints[constraint_name]
            return True
        return False

    def get_all_constraints(self) -> Dict[str, PhysicsConstraintRule]:
        """Return all registered constraints."""
        return dict(self._constraints)

    def match_constraints(
        self, target_property: str, prediction_target_name: Optional[str] = None
    ) -> Dict[str, PhysicsConstraintRule]:
        """Find constraints matching a target property name.

        Matches by checking if the constraint's target_patterns appear in
        the target_property or prediction_target_name (case-insensitive).
        """
        if not target_property and not prediction_target_name:
            return {}

        if target_property is None:
            target_property = ""
        if prediction_target_name is None:
            prediction_target_name = ""

        search_str = f"{target_property} {prediction_target_name}".lower()
        matched: Dict[str, PhysicsConstraintRule] = {}

        for name, rule in self._constraints.items():
            for pattern in rule.target_patterns:
                if pattern.lower() in search_str:
                    matched[name] = rule
                    break

        logger.info("Matched %d physics constraints for target='%s'",
                     len(matched), target_property)
        return matched

    def get_feature_semantics(self, feature_name: str) -> Dict[str, Any]:
        """Get registered semantics for a feature by pattern matching."""
        result: Dict[str, Any] = {}
        feature_lower = feature_name.lower()
        for pattern, semantics in self._feature_semantics.items():
            if pattern.lower() in feature_lower:
                result.update(semantics)
        return result

    def check_all(
        self,
        y_pred: Any,
        target_property: str,
        prediction_target_name: Optional[str] = None,
        custom_constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Check all matching constraints against predictions.

        Args:
            y_pred: Array of predicted values.
            target_property: The target column name (e.g., "band_gap").
            prediction_target_name: Human-readable target name.
            custom_constraints: Optional user-provided constraints to merge.

        Returns:
            Dict with 'constraints' list and 'passed' bool flag.
            Each constraint result has: constraint_name, description, expected,
            actual, passed, severity, n_violations, violation_rate, violating_sample_indices.
        """
        if y_pred is None:
            logger.warning("check_all called with y_pred=None, returning empty results")
            return {"constraints": [], "passed": True}

        values = np.asarray(y_pred, dtype=float).flatten()
        if len(values) == 0:
            logger.warning("check_all called with empty y_pred array")
            return {"constraints": [], "passed": True}

        # If custom constraints are provided, temporarily register them
        temp_names: List[str] = []
        if custom_constraints:
            for name, spec in custom_constraints.items():
                if isinstance(spec, dict) and callable(spec.get("check")):
                    rule = PhysicsConstraintRule(
                        constraint_name=name,
                        description=spec.get("description", name),
                        check_fn=spec["check"],
                        severity=spec.get("severity", "warning"),
                        target_patterns=[name, target_property or "", prediction_target_name or ""],
                    )
                    self.register_constraint(rule)
                    temp_names.append(name)

        applicable = self.match_constraints(target_property, prediction_target_name)

        if not applicable:
            logger.info("No physics constraints matched for target '%s'", target_property)
            # Clean up temp constraints
            for name in temp_names:
                self.unregister_constraint(name)
            return {"constraints": [], "passed": True}

        results = []
        all_passed = True

        for key, constraint in applicable.items():
            try:
                satisfied = constraint.check_fn(values)
                satisfied_bool = np.asarray(satisfied, dtype=bool)
                n_violations = int(np.sum(~satisfied_bool))
                passed = n_violations == 0
                if not passed:
                    all_passed = False

                violation_indices: List[int] = []
                if n_violations > 0:
                    violation_abs = np.where(~satisfied_bool)[0]
                    violation_indices = violation_abs[:10].tolist()

                results.append({
                    "constraint_name": key,
                    "description": constraint.description,
                    "expected": constraint.description,
                    "actual": (
                        f"{n_violations} of {len(values)} predictions violate the constraint"
                        if n_violations > 0
                        else f"All {len(values)} predictions satisfy the constraint"
                    ),
                    "passed": passed,
                    "severity": constraint.severity,
                    "n_violations": n_violations,
                    "violation_rate": round(n_violations / len(values), 4) if len(values) > 0 else 0.0,
                    "violating_sample_indices": violation_indices,
                })
            except Exception as e:
                logger.error("Physics constraint check '%s' raised exception: %s", key, str(e))
                results.append({
                    "constraint_name": key,
                    "description": constraint.description,
                    "passed": False,
                    "severity": constraint.severity,
                    "error": str(e),
                })
                all_passed = False

        # Clean up temporary constraints
        for name in temp_names:
            self.unregister_constraint(name)

        logger.info("Physics constraint check: %d/%d passed",
                     sum(1 for r in results if r.get("passed", False)), len(results))
        return {"constraints": results, "passed": all_passed}

    def compute_physics_consistency_score(
        self, constraint_results: Dict[str, Any]
    ) -> float:
        """Compute a [0, 1] physics consistency score from constraint check results.

        All passed = 1.0.
        Critical violation -> capped at 0.5 maximum.
        Each warning violation -> -0.1 per violation.
        """
        constraints = constraint_results.get("constraints", [])
        if not constraints:
            return 1.0

        score = 1.0
        has_critical = False

        for c in constraints:
            if not c.get("passed", True):
                severity = c.get("severity", "warning")
                if severity == "critical":
                    has_critical = True
                    score -= 0.3
                elif severity == "warning":
                    score -= 0.1
                else:  # info
                    score -= 0.05

        if has_critical:
            score = min(score, 0.5)
        return max(score, 0.0)

    def _register_defaults(self) -> None:
        """Register the built-in materials science constraints."""
        defaults = [
            PhysicsConstraintRule(
                constraint_name="band_gap",
                description="Band gap must be non-negative (>= 0 eV)",
                check_fn=lambda v: v >= 0,
                severity="critical",
                target_patterns=["band_gap", "bandgap", "gap", "bg"],
            ),
            PhysicsConstraintRule(
                constraint_name="formation_energy",
                description="Formation energy should be <= 0 eV/atom for stable compounds",
                check_fn=lambda v: v <= 0,
                severity="warning",
                target_patterns=["formation_energy", "formation", "e_form", "formation enthalpy"],
            ),
            PhysicsConstraintRule(
                constraint_name="bulk_modulus",
                description="Bulk modulus must be non-negative (>= 0 GPa)",
                check_fn=lambda v: v >= 0,
                severity="critical",
                target_patterns=["bulk_modulus", "bulk", "k_vrh", "bulkmodulus"],
            ),
            PhysicsConstraintRule(
                constraint_name="shear_modulus",
                description="Shear modulus must be non-negative (>= 0 GPa)",
                check_fn=lambda v: v >= 0,
                severity="critical",
                target_patterns=["shear_modulus", "shear", "g_vrh", "shearmodulus"],
            ),
            PhysicsConstraintRule(
                constraint_name="thermal_conductivity",
                description="Thermal conductivity must be non-negative (>= 0 W/mK)",
                check_fn=lambda v: v >= 0,
                severity="critical",
                target_patterns=["thermal_conductivity", "kappa", "thermal", "thermalcond"],
            ),
            PhysicsConstraintRule(
                constraint_name="electrical_conductivity",
                description="Electrical conductivity must be non-negative (>= 0 S/m)",
                check_fn=lambda v: v >= 0,
                severity="critical",
                target_patterns=["electrical_conductivity", "conductivity", "sigma"],
            ),
            PhysicsConstraintRule(
                constraint_name="density",
                description="Density must be positive (> 0 g/cm^3)",
                check_fn=lambda v: v > 0,
                severity="critical",
                target_patterns=["density", "rho", "mass_density"],
            ),
            PhysicsConstraintRule(
                constraint_name="melting_point",
                description="Melting point must be positive (> 0 K)",
                check_fn=lambda v: v > 0,
                severity="critical",
                target_patterns=["melting_point", "melting", "t_melt", "melting_temperature"],
            ),
            PhysicsConstraintRule(
                constraint_name="elastic_modulus",
                description="Elastic modulus (Young's) must be non-negative (>= 0 GPa)",
                check_fn=lambda v: v >= 0,
                severity="critical",
                target_patterns=["elastic_modulus", "youngs_modulus", "e_modulus", "elastic"],
            ),
            PhysicsConstraintRule(
                constraint_name="poisson_ratio",
                description="Poisson ratio must be between -1.0 and 0.5",
                check_fn=lambda v: (v >= -1.0) & (v <= 0.5),
                severity="warning",
                target_patterns=["poisson_ratio", "poisson", "nu"],
            ),
        ]
        for rule in defaults:
            self.register_constraint(rule)

        # Register common feature semantics for materials science
        self._feature_semantics = {
            "electronegativity": {"category": "elemental", "expected_direction": "context_dependent"},
            "atomic_radius": {"category": "elemental", "expected_direction": "context_dependent"},
            "atomic_mass": {"category": "elemental", "expected_direction": "context_dependent"},
            "valence": {"category": "elemental", "expected_direction": "context_dependent"},
            "density": {"category": "structure", "expected_direction": "context_dependent"},
            "volume": {"category": "structure", "expected_direction": "context_dependent"},
            "lattice_parameter": {"category": "structure", "expected_direction": "context_dependent"},
            "formation_energy": {"category": "thermodynamic", "expected_direction": "stability_indicator"},
            "band_gap": {"category": "electronic", "expected_direction": "context_dependent"},
        }

        # Domain priors
        self._domain_priors = [
            {
                "description": "Elemental features (electronegativity, radius, valence) often show non-linear relationships with materials properties.",
                "implication": "Non-monotonic PDPs for elemental features are expected and not necessarily problematic.",
            },
            {
                "description": "Formation energy and band gap are correlated in many material families.",
                "implication": "Models capturing both may show correlated importance patterns.",
            },
        ]


# Module-level singleton
_registry: Optional[PhysicsRuleRegistry] = None


def get_registry() -> PhysicsRuleRegistry:
    """Get or create the global PhysicsRuleRegistry singleton."""
    global _registry
    if _registry is None:
        _registry = PhysicsRuleRegistry()
    return _registry


def check_physics_constraints(
    y_pred: Any,
    target_property: Optional[str] = None,
    prediction_target_name: Optional[str] = None,
    custom_constraints: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Backward-compatible wrapper around PhysicsRuleRegistry.check_all().

    Preserves the exact return format used by existing callers in service.py
    and other modules. For new code, prefer using get_registry() directly.
    """
    return get_registry().check_all(
        y_pred=y_pred,
        target_property=target_property or "",
        prediction_target_name=prediction_target_name,
        custom_constraints=custom_constraints,
    )
