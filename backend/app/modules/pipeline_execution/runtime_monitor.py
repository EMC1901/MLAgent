"""Runtime Monitor — captures execution metadata and environment info."""

import sys
import platform
from datetime import datetime
from app.modules.pipeline_execution.schemas import RuntimeEnvironmentDTO


def capture_runtime_environment() -> RuntimeEnvironmentDTO:
    """Capture Python and library versions for reproducibility."""
    info = RuntimeEnvironmentDTO(
        python_version=sys.version.split()[0] if sys.version else None,
        platform=platform.platform(),
    )
    try:
        import sklearn
        info.scikit_learn_version = sklearn.__version__
    except ImportError:
        pass
    try:
        import pandas as pd
        info.pandas_version = pd.__version__
    except ImportError:
        pass
    try:
        import numpy as np
        info.numpy_version = np.__version__
    except ImportError:
        pass
    try:
        import joblib
        info.joblib_version = joblib.__version__
    except ImportError:
        pass
    return info


def build_runtime_log(
    started_at: datetime,
    finished_at: datetime,
    status: str,
    warnings: list,
    error_message: str = None,
    events: list = None,
    env_info: dict = None,
    n_trials_planned: int = 0,
    n_trials_completed: int = 0,
    n_trials_failed: int = 0,
) -> dict:
    """Build a runtime log summary with optional event timeline."""
    return {
        "started_at": started_at.isoformat() if started_at else None,
        "finished_at": finished_at.isoformat() if finished_at else None,
        "duration_seconds": (
            (finished_at - started_at).total_seconds()
            if started_at and finished_at
            else 0.0
        ),
        "status": status,
        "warnings": warnings,
        "error_message": error_message,
        "events": events or [],
        "environment": env_info or {},
        "trial_summary": {
            "n_trials_planned": n_trials_planned,
            "n_trials_completed": n_trials_completed,
            "n_trials_failed": n_trials_failed,
        },
    }
