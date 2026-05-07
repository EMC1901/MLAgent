from typing import Optional, List
from sqlmodel import Session, select
from app.modules.result_diagnosis.model import ResultDiagnosis


class ResultDiagnosisRepository:

    def create(self, session: Session, record: ResultDiagnosis) -> ResultDiagnosis:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    def get_by_id(self, session: Session, rd_id: str) -> Optional[ResultDiagnosis]:
        return session.get(ResultDiagnosis, rd_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[ResultDiagnosis]:
        statement = (
            select(ResultDiagnosis)
            .where(ResultDiagnosis.task_id == task_id)
            .order_by(ResultDiagnosis.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[ResultDiagnosis]:
        statement = (
            select(ResultDiagnosis)
            .where(ResultDiagnosis.task_id == task_id)
            .order_by(ResultDiagnosis.created_at.desc())
        )
        return list(session.exec(statement).all())

    def count_by_task_id(self, session: Session, task_id: str) -> int:
        statement = (
            select(ResultDiagnosis)
            .where(ResultDiagnosis.task_id == task_id)
        )
        return len(list(session.exec(statement).all()))

    def update(self, session: Session, record: ResultDiagnosis) -> ResultDiagnosis:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
