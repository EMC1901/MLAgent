import logging
import concurrent.futures
from typing import Optional, List
from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError
from app.modules.interpretability_analysis.model import InterpretabilityAnalysis

logger = logging.getLogger(__name__)

_COMMIT_TIMEOUT_SECONDS = 120


def _is_connection_error(exc: OperationalError) -> bool:
    msg = str(exc).lower()
    return any(kw in msg for kw in (
        "connection abort", "server closed", "receive data",
        "connection was closed", "terminating connection",
    ))


def _commit_with_timeout(session: Session, label: str, retry_add=None):
    logger.debug("commit %s: starting (%ds timeout) ...", label, _COMMIT_TIMEOUT_SECONDS)
    for attempt in range(2):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(session.commit)
            try:
                future.result(timeout=_COMMIT_TIMEOUT_SECONDS)
                logger.debug("commit %s: done (attempt %d)", label, attempt + 1)
                return
            except concurrent.futures.TimeoutError:
                logger.warning("commit %s: TIMED OUT after %ds!", label, _COMMIT_TIMEOUT_SECONDS)
                raise TimeoutError(
                    f"Database commit timed out after {_COMMIT_TIMEOUT_SECONDS}s."
                )
            except OperationalError as exc:
                if attempt == 0 and _is_connection_error(exc):
                    logger.warning("commit %s: connection broken — %s", label, str(exc).strip()[:200])
                    logger.debug("commit %s: closing session and retrying ...", label)
                    session.close()
                    if retry_add is not None:
                        session.add(retry_add)
                    continue
                raise
            except Exception:
                raise


class InterpretabilityAnalysisRepository:

    def create(self, session: Session, record: InterpretabilityAnalysis) -> InterpretabilityAnalysis:
        session.add(record)
        _commit_with_timeout(session, "create", retry_add=record)
        session.refresh(record)
        return record

    def get_by_id(self, session: Session, ia_id: str) -> Optional[InterpretabilityAnalysis]:
        return session.get(InterpretabilityAnalysis, ia_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[InterpretabilityAnalysis]:
        statement = (
            select(InterpretabilityAnalysis)
            .where(InterpretabilityAnalysis.task_id == task_id)
            .order_by(InterpretabilityAnalysis.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[InterpretabilityAnalysis]:
        statement = (
            select(InterpretabilityAnalysis)
            .where(InterpretabilityAnalysis.task_id == task_id)
            .order_by(InterpretabilityAnalysis.created_at.desc())
        )
        return list(session.exec(statement).all())

    def update(self, session: Session, record: InterpretabilityAnalysis) -> InterpretabilityAnalysis:
        session.add(record)
        _commit_with_timeout(session, "update", retry_add=record)
        session.refresh(record)
        return record
