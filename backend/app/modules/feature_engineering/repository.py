from sqlmodel import Session, select
from app.modules.feature_engineering.model import FeatureEngineering
from typing import Optional, List


class FeatureEngineeringRepository:

    def create(self, session: Session, fe: FeatureEngineering) -> FeatureEngineering:
        session.add(fe)
        session.commit()
        session.refresh(fe)
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
