from typing import Optional, List
from sqlmodel import Session, select
from app.modules.interpretability_analysis.model import InterpretabilityAnalysis


class InterpretabilityAnalysisRepository:

    def create(self, session: Session, record: InterpretabilityAnalysis) -> InterpretabilityAnalysis:
        session.add(record)
        session.commit()
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
        session.commit()
        session.refresh(record)
        return record
