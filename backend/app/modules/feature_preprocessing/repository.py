from sqlmodel import Session, select
from app.modules.feature_preprocessing.model import FeaturePreprocessing
from typing import Optional, List


class FeaturePreprocessingRepository:

    def create(self, session: Session, record: FeaturePreprocessing) -> FeaturePreprocessing:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    def get_by_id(self, session: Session, fmp_id: str) -> Optional[FeaturePreprocessing]:
        return session.get(FeaturePreprocessing, fmp_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[FeaturePreprocessing]:
        statement = (
            select(FeaturePreprocessing)
            .where(FeaturePreprocessing.task_id == task_id)
            .order_by(FeaturePreprocessing.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[FeaturePreprocessing]:
        statement = (
            select(FeaturePreprocessing)
            .where(FeaturePreprocessing.task_id == task_id)
            .order_by(FeaturePreprocessing.created_at.desc())
        )
        return list(session.exec(statement).all())
