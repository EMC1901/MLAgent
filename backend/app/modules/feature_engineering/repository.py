import sys
import concurrent.futures
from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError
from app.modules.feature_engineering.model import FeatureEngineering
from typing import Optional, List

def _diag(msg, *args):
    formatted = msg % args if args else msg
    print(f"DIAG     [repo] {formatted}", file=sys.stderr, flush=True)

_COMMIT_TIMEOUT_SECONDS = 120


def _is_connection_error(exc: OperationalError) -> bool:
    """Detect connection-aborted errors (common after long idle periods in Docker/WSL)."""
    msg = str(exc).lower()
    return any(kw in msg for kw in (
        "connection abort", "server closed", "receive data",
        "connection was closed", "terminating connection",
    ))


def _commit_with_timeout(session: Session, label: str, retry_add=None):
    """Commit with timeout and retry on connection-abort errors.

    After a long LLM call, Docker Desktop on Windows may drop the idle TCP
    connection to PostgreSQL.  When a connection error is detected we close
    the session (which releases the dead connection back to the pool and
    resets transaction state), re-add the record, and retry.
    """
    _diag("%s: committing (%ds timeout) ...", label, _COMMIT_TIMEOUT_SECONDS)
    for attempt in range(2):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(session.commit)
            try:
                future.result(timeout=_COMMIT_TIMEOUT_SECONDS)
                _diag("%s: commit done (attempt %d)", label, attempt + 1)
                return
            except concurrent.futures.TimeoutError:
                _diag("%s: commit TIMED OUT after %ds!", label, _COMMIT_TIMEOUT_SECONDS)
                raise TimeoutError(
                    f"Database commit timed out after {_COMMIT_TIMEOUT_SECONDS}s."
                )
            except OperationalError as exc:
                if attempt == 0 and _is_connection_error(exc):
                    _diag("%s: connection broken — %s", label, str(exc).strip()[:200])
                    _diag("%s: closing session and retrying ...", label)
                    session.close()
                    if retry_add is not None:
                        session.add(retry_add)
                    continue
                raise
            except Exception:
                raise


class FeatureEngineeringRepository:

    def create(self, session: Session, fe: FeatureEngineering) -> FeatureEngineering:
        _diag("session.add(fe) ...")
        session.add(fe)
        _commit_with_timeout(session, "create", retry_add=fe)
        _diag("session.refresh(fe) ...")
        session.refresh(fe)
        _diag("session.refresh(fe) done")
        return fe

    def get_by_id(self, session: Session, fe_id: str) -> Optional[FeatureEngineering]:
        return session.get(FeatureEngineering, fe_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[FeatureEngineering]:
        statement = (
            select(FeatureEngineering)
            .where(FeatureEngineering.task_id == task_id)
            .order_by(FeatureEngineering.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[FeatureEngineering]:
        statement = (
            select(FeatureEngineering)
            .where(FeatureEngineering.task_id == task_id)
            .order_by(FeatureEngineering.created_at.desc())
        )
        return list(session.exec(statement).all())
