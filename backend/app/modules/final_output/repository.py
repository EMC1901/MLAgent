from typing import Optional, List
from sqlmodel import Session, select
from app.modules.final_output.model import FinalOutput


class FinalOutputRepository:

    def create(self, session: Session, record: FinalOutput) -> FinalOutput:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    def get_by_id(self, session: Session, fo_id: str) -> Optional[FinalOutput]:
        return session.get(FinalOutput, fo_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[FinalOutput]:
        statement = (
            select(FinalOutput)
            .where(FinalOutput.task_id == task_id)
            .order_by(FinalOutput.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[FinalOutput]:
        statement = (
            select(FinalOutput)
            .where(FinalOutput.task_id == task_id)
            .order_by(FinalOutput.created_at.desc())
        )
        return list(session.exec(statement).all())

    def update(self, session: Session, record: FinalOutput) -> FinalOutput:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
