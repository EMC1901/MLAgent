import logging
import concurrent.futures
from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError
from app.modules.feature_preprocessing.model import FeaturePreprocessing
from typing import Optional, List

logger = logging.getLogger(__name__)

_COMMIT_TIMEOUT_SECONDS = 120


def _is_connection_error(exc: OperationalError) -> bool:
    """Detect connection-aborted errors (common after long idle periods in Docker/WSL)."""
    msg = str(exc).lower()
    # Windows: "Software caused connection abort" (10053)
    # Linux: "server closed the connection unexpectedly"
    # TCP keepalive / timeout
    return any(kw in msg for kw in (
        "connection abort", "server closed", "receive data",
        "connection was closed", "terminating connection",
    ))


def _commit_with_timeout(session: Session, label: str, retry_add=None):
    """Commit with timeout and retry on connection-abort errors.

    After a long LLM call, Docker Desktop on Windows may drop the idle TCP
    connection to PostgreSQL.  When a connection error is detected we close
    the session (which releases the dead connection back to the pool and
    resets transaction state), re-add the record, and retry.  Closing is safer
    than rolling-back-and-invalidating because the latter leaves the session
    holding a reference to the invalidated connection, which causes
    PendingRollbackError on the retry flush.
    """
    logger.debug("%s: committing (%ds timeout) ...", label, _COMMIT_TIMEOUT_SECONDS)
    for attempt in range(2):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(session.commit)
            try:
                future.result(timeout=_COMMIT_TIMEOUT_SECONDS)
                logger.debug("%s: commit done (attempt %d)", label, attempt + 1)
                return
            except concurrent.futures.TimeoutError:
                logger.debug("%s: commit TIMED OUT after %ds!", label, _COMMIT_TIMEOUT_SECONDS)
                raise TimeoutError(
                    f"Database commit timed out after {_COMMIT_TIMEOUT_SECONDS}s."
                )
            except OperationalError as exc:
                if attempt == 0 and _is_connection_error(exc):
                    logger.debug("%s: connection broken — %s", label, str(exc).strip()[:200])
                    logger.debug("%s: closing session and retrying ...", label)
                    session.close()
                    if retry_add is not None:
                        session.add(retry_add)
                    continue
                raise
            except Exception:
                raise


class FeaturePreprocessingRepository:

    def create(self, session: Session, record: FeaturePreprocessing) -> FeaturePreprocessing:
        logger.debug("session.add(record) ...")
        session.add(record)
        _commit_with_timeout(session, "create", retry_add=record)
        logger.debug("session.refresh(record) ...")
        session.refresh(record)
        return record

    def save(self, session: Session, record: FeaturePreprocessing) -> FeaturePreprocessing:
        """INSERT if new, UPDATE if existing (uses session.merge)."""
        logger.debug("session.merge(record) ...")
        merged = session.merge(record)
        _commit_with_timeout(session, "save", retry_add=merged)
        logger.debug("session.refresh(merged) ...")
        session.refresh(merged)
        return merged

    def get_by_id(self, session: Session, fmp_id: str) -> Optional[FeaturePreprocessing]:
        return session.get(FeaturePreprocessing, fmp_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[FeaturePreprocessing]:
        statement = (
            select(FeaturePreprocessing)
            .where(FeaturePreprocessing.task_id == task_id)
            .order_by(FeaturePreprocessing.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[FeaturePreprocessing]:
        statement = (
            select(FeaturePreprocessing)
            .where(FeaturePreprocessing.task_id == task_id)
            .order_by(FeaturePreprocessing.created_at.desc())
        )
        return list(session.exec(statement).all())
