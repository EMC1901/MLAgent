import sys
import concurrent.futures
from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError
from app.modules.pipeline_generation.model import PipelineGeneration
from typing import Optional, List

def _diag(msg, *args):
    formatted = msg % args if args else msg
    print(f"DIAG     [pg-repo] {formatted}", file=sys.stderr, flush=True)

_COMMIT_TIMEOUT_SECONDS = 120


def _is_connection_error(exc: OperationalError) -> bool:
    msg = str(exc).lower()
    return any(kw in msg for kw in (
        "connection abort", "server closed", "receive data",
        "connection was closed", "terminating connection",
    ))


def _commit_with_timeout(session: Session, label: str, retry_add=None):
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


class PipelineGenerationRepository:

    def create(self, session: Session, record: PipelineGeneration) -> PipelineGeneration:
        session.add(record)
        _commit_with_timeout(session, "create", retry_add=record)
        session.refresh(record)
        return record

    def get_by_id(self, session: Session, pg_id: str) -> Optional[PipelineGeneration]:
        return session.get(PipelineGeneration, pg_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[PipelineGeneration]:
        statement = (
            select(PipelineGeneration)
            .where(PipelineGeneration.task_id == task_id)
            .order_by(PipelineGeneration.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[PipelineGeneration]:
        statement = (
            select(PipelineGeneration)
            .where(PipelineGeneration.task_id == task_id)
            .order_by(PipelineGeneration.created_at.desc())
        )
        return list(session.exec(statement).all())
