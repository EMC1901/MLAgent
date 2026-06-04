import logging
from typing import Dict, Any
from app.modules.iteration_decision.schemas import SystemChecks

logger = logging.getLogger(__name__)


def run_guard_rules(history: Dict[str, Any], max_iterations: int = 5, min_improvement: float = 0.01) -> SystemChecks:
    checks = SystemChecks()

    n_iter = history.get("n_iterations_completed", 0)

    # Max iterations reached
    if n_iter >= max_iterations:
        checks.max_iterations_reached = True
        checks.warnings.append(f"Maximum iterations ({max_iterations}) reached.")

    # No improvement trend
    trend = history.get("metric_trend", "unknown")
    if trend in ("degrading", "stable") and n_iter >= 2:
        checks.no_improvement_trend = True
        checks.warnings.append(f"Metric trend is '{trend}' after {n_iter} iterations — further iterations unlikely to help.")

    # Repeated root causes
    repeated = history.get("repeated_root_causes", [])
    if repeated:
        checks.repeated_root_cause = True
        checks.warnings.append(f"Root causes persist across iterations: {repeated}. May indicate a fundamental limitation.")

    triggered = [k for k, v in checks.model_dump().items()
                 if v is True and k not in ("warnings", "additional_checks")]
    logger.info("Guard rules — %d triggered (%s)",
                 len(triggered), ", ".join(triggered) if triggered else "none")
    return checks
