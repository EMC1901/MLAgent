import sys
import concurrent.futures
from sqlmodel import Session, select, func
from sqlalchemy.exc import OperationalError
from app.modules.task_specification.model import TaskSpecification
from app.shared.common.exceptions import NotFoundException
from typing import Optional, List, Tuple

def _diag(msg, *args):
    formatted = msg % args if args else msg
    print(f"DIAG     [ts-repo] {formatted}", file=sys.stderr, flush=True)

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


class TaskSpecificationRepository:

    def create(self, session: Session, task_spec: TaskSpecification) -> TaskSpecification:
        session.add(task_spec)
        _commit_with_timeout(session, "create", retry_add=task_spec)
        session.refresh(task_spec)
        return task_spec

    def get_by_id(self, session: Session, task_id: str) -> Optional[TaskSpecification]:
        return session.get(TaskSpecification, task_id)

    def update(self, session: Session, task_id: str, task_spec: TaskSpecification) -> TaskSpecification:
        existing = self.get_by_id(session, task_id)
        if not existing:
            raise NotFoundException(f"Task specification with id {task_id} not found.")

        for key, value in task_spec.model_dump(exclude_unset=True).items():
            setattr(existing, key, value)

        session.add(existing)
        _commit_with_timeout(session, "update", retry_add=existing)
        session.refresh(existing)
        return existing

    def exists(self, session: Session, task_id: str) -> bool:
        return self.get_by_id(session, task_id) is not None

    def list_tasks(self, session: Session, offset: int = 0, limit: int = 50) -> Tuple[List[TaskSpecification], int]:
        base_query = select(TaskSpecification)
        total = session.scalar(select(func.count()).select_from(TaskSpecification)) or 0

        tasks = session.exec(
            base_query
            .order_by(TaskSpecification.created_at.desc().nullslast())
            .offset(offset)
            .limit(limit)
        ).all()

        return list(tasks), total
