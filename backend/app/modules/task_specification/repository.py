from sqlmodel import Session
from app.modules.task_specification.model import TaskSpecification
from app.shared.common.exceptions import NotFoundException
from typing import Optional, List


class TaskSpecificationRepository:

    def create(self, session: Session, task_spec: TaskSpecification) -> TaskSpecification:
        session.add(task_spec)
        session.commit()
        session.refresh(task_spec)
        return task_spec

    def get_by_id(self, session: Session, task_id: str) -> Optional[TaskSpecification]:
        return session.get(TaskSpecification, task_id)

    def update(self, session: Session, task_id: str, task_spec: TaskSpecification) -> TaskSpecification:
        existing = self.get_by_id(session, task_id)
        if not existing:
            raise NotFoundException(f"Task specification with id {task_id} not found.")

        for key, value in task_spec.dict(exclude_unset=True).items():
            setattr(existing, key, value)

        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    def exists(self, session: Session, task_id: str) -> bool:
        return self.get_by_id(session, task_id) is not None

    def list_tasks(self, session: Session) -> List[TaskSpecification]:
        return session.query(TaskSpecification).order_by(
            TaskSpecification.created_at.desc().nullslast()
        ).limit(50).all()
