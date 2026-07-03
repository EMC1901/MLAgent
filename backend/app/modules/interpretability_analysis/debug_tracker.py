"""Interpretability Analysis Debug Tracker.

Provides a context-managed step tracker that records timing, input/output
summaries, structured warnings, and error tracebacks for every step in an
interpretability analysis run.  The resulting DebugTrace is persisted into
the database record so that failures are inspectable even after the HTTP
response is gone.
"""

from __future__ import annotations

import logging
import time
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.modules.interpretability_analysis.schemas import (
    DebugTrace,
    DebugTraceStep,
    DebugWarning,
)
from app.modules.interpretability_analysis.model import InterpretabilityAnalysis

logger = logging.getLogger(__name__)


class InterpretabilityDebugTracker:
    """Tracks per-step execution details for a single interpretability run."""

    def __init__(self, run_id: str, environment: Optional[Dict[str, Any]] = None):
        self.run_id = run_id
        self.environment = environment or {}
        self._steps: List[DebugTraceStep] = []
        self._current_step: Optional[DebugTraceStep] = None
        self._started_at = time.time()
        self._cache_hit = False
        self._cached_from_ia_id: Optional[str] = None

    # ── public API ──────────────────────────────────────────────────

    def mark_cache_hit(self, cached_from_ia_id: str) -> None:
        self._cache_hit = True
        self._cached_from_ia_id = cached_from_ia_id

    @contextmanager
    def step(
        self,
        step_id: str,
        step_name: str = "",
        input_summary: Optional[Dict[str, Any]] = None,
    ):
        """Context manager that wraps a single analysis step.

        Usage::

            with tracker.step("05_load_model", input_summary={"path": p}):
                model = load_model(p)
        """
        debug_step = DebugTraceStep(
            step=step_id,
            step_name=step_name or step_id,
            status="running",
            started_at=datetime.now(timezone.utc).isoformat(),
            input_summary=input_summary or {},
        )
        self._current_step = debug_step
        t0 = time.time()

        try:
            yield debug_step
        except Exception as exc:
            elapsed = time.time() - t0
            debug_step.status = "failed"
            debug_step.finished_at = datetime.now(timezone.utc).isoformat()
            debug_step.duration_seconds = round(elapsed, 3)
            debug_step.error_type = type(exc).__name__
            debug_step.error_message = str(exc)
            debug_step.error_traceback = traceback.format_exc()
            debug_step.recoverable = False
            self._steps.append(debug_step)
            self._current_step = None
            raise
        else:
            elapsed = time.time() - t0
            debug_step.status = "completed"
            debug_step.finished_at = datetime.now(timezone.utc).isoformat()
            debug_step.duration_seconds = round(elapsed, 3)
            self._steps.append(debug_step)
            self._current_step = None

    def update_output(self, output_summary: Dict[str, Any]) -> None:
        """Update the output_summary of the *last completed* step."""
        if self._steps:
            self._steps[-1].output_summary = output_summary

    def add_warning(
        self,
        step_id: str,
        code: str,
        message: str,
        severity: str = "warning",
    ) -> None:
        """Attach a structured warning to a step."""
        dw = DebugWarning(
            step=step_id,
            code=code,
            severity=severity,
            message=message,
        )
        # Attach to the named step if it exists, else append to last
        for s in reversed(self._steps):
            if s.step == step_id:
                s.warnings.append(dw)
                return
        # Fallback: attach to most recent step
        if self._steps:
            self._steps[-1].warnings.append(dw)
        else:
            logger.warning("Warning with no step to attach: [%s] %s", code, message)

    def add_recoverable_error(
        self,
        step_id: str,
        exc: Exception,
    ) -> None:
        """Record a recoverable error (does not re-raise)."""
        # Find or create the step
        for s in reversed(self._steps):
            if s.step == step_id:
                dw = DebugWarning(
                    step=step_id,
                    code=f"{type(exc).__name__.upper()}_FAILED",
                    severity="error",
                    message=str(exc),
                )
                s.warnings.append(dw)
                if s.status == "completed":
                    # Downgrade: completed → completed_with_warnings is implicit
                    pass
                return
        # Step not found — create a minimal failed step entry
        logger.warning("Recording recoverable error for missing step %s: %s", step_id, exc)
        dw = DebugWarning(
            step=step_id,
            code=f"{type(exc).__name__.upper()}_FAILED",
            severity="error",
            message=str(exc),
        )
        self._steps.append(DebugTraceStep(
            step=step_id,
            step_name=step_id,
            status="failed",
            error_type=type(exc).__name__,
            error_message=str(exc),
            error_traceback=traceback.format_exc(),
            recoverable=True,
            warnings=[dw],
        ))

    # ── output ──────────────────────────────────────────────────────

    @property
    def last_completed_step(self) -> Optional[str]:
        for s in reversed(self._steps):
            if s.status == "completed":
                return s.step
        return None

    @property
    def current_step(self) -> Optional[str]:
        if self._current_step:
            return self._current_step.step
        return None

    def get_all_warnings(self) -> List[DebugWarning]:
        all_w: List[DebugWarning] = []
        for s in self._steps:
            all_w.extend(s.warnings)
        return all_w

    def has_errors(self) -> bool:
        return any(s.status == "failed" and not s.recoverable for s in self._steps)

    def has_warnings(self) -> bool:
        return any(
            s.warnings or (s.status == "failed" and s.recoverable)
            for s in self._steps
        )

    def to_debug_trace(self) -> DebugTrace:
        total = time.time() - self._started_at
        return DebugTrace(
            run_id=self.run_id,
            steps=list(self._steps),
            environment=self.environment,
            cache_hit=self._cache_hit,
            cached_from_ia_id=self._cached_from_ia_id,
            total_duration_seconds=round(total, 2),
        )

    def apply_to_record(
        self,
        record: InterpretabilityAnalysis,
    ) -> None:
        """Write debug state into the DB record (caller must still commit)."""
        trace = self.to_debug_trace()
        record.debug_trace_json = trace.model_dump()
        record.warnings_json = {
            "items": [w.model_dump() for w in self.get_all_warnings()],
        }
        record.current_step = self.current_step
        record.last_completed_step = self.last_completed_step

    # ── persist helpers ────────────────────────────────────────────

    def persist_after_step(
        self,
        session,
        record: InterpretabilityAnalysis,
    ) -> None:
        """Lightweight persist — update current_step on the record.

        Call this after long steps so the DB reflects real-time progress.
        """
        record.current_step = self.current_step
        record.last_completed_step = self.last_completed_step
        record.updated_at = datetime.now(timezone.utc)
        try:
            from app.modules.interpretability_analysis.repository import (
                InterpretabilityAnalysisRepository,
            )
            InterpretabilityAnalysisRepository().update(session, record)
        except Exception:
            logger.debug("Failed to persist step progress (non-fatal)", exc_info=True)


def determine_final_status(
    tracker: InterpretabilityDebugTracker,
    artifact_save_failed: bool = False,
    final_output_failed: bool = False,
) -> str:
    """Determine the final status based on debug trace and flags.

    Rules (first match wins):
        fatal (non-recoverable) error → failed
        warnings present → analyzed_with_warning
        artifact save failed → analyzed_with_warning
        final output failed → analyzed_with_warning
        otherwise → analyzed
    """
    from app.modules.interpretability_analysis.enums import InterpretabilityAnalysisStatus

    if tracker.has_errors():
        return InterpretabilityAnalysisStatus.FAILED
    if tracker.has_warnings() or artifact_save_failed or final_output_failed:
        return InterpretabilityAnalysisStatus.ANALYZED_WITH_WARNING
    return InterpretabilityAnalysisStatus.ANALYZED
