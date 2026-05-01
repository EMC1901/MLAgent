from sqlmodel import Session, select
from app.modules.task_interpretation.model import TaskInterpretation
from typing import Optional, List


class TaskInterpretationRepository:

    def create(self, session: Session, interpretation: TaskInterpretation) -> TaskInterpretation:
        session.add(interpretation)
        session.commit()
        session.refresh(interpretation)
        return interpretation

    def get_by_id(self, session: Session, interpretation_id: str) -> Optional[TaskInterpretation]:
        return session.get(TaskInterpretation, interpretation_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[TaskInterpretation]:
        statement = (
            select(TaskInterpretation)
            .where(TaskInterpretation.task_id == task_id)
            .order_by(TaskInterpretation.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[TaskInterpretation]:
        statement = (
            select(TaskInterpretation)
            .where(TaskInterpretation.task_id == task_id)
            .order_by(TaskInterpretation.created_at.desc())
        )
        return list(session.exec(statement).all())
