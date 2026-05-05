from typing import Optional, List
from sqlmodel import Session, select
from app.modules.metric_evaluation.model import MetricEvaluation


class MetricEvaluationRepository:

    def create(self, session: Session, record: MetricEvaluation) -> MetricEvaluation:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    def get_by_id(self, session: Session, me_id: str) -> Optional[MetricEvaluation]:
        return session.get(MetricEvaluation, me_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[MetricEvaluation]:
        statement = (
            select(MetricEvaluation)
            .where(MetricEvaluation.task_id == task_id)
            .order_by(MetricEvaluation.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[MetricEvaluation]:
        statement = (
            select(MetricEvaluation)
            .where(MetricEvaluation.task_id == task_id)
            .order_by(MetricEvaluation.created_at.desc())
        )
        return list(session.exec(statement).all())

    def update(self, session: Session, record: MetricEvaluation) -> MetricEvaluation:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
