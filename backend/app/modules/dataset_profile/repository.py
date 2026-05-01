from sqlmodel import Session, select
from app.modules.dataset_profile.model import DatasetProfile
from app.shared.common.exceptions import NotFoundException
from typing import Optional, List


class DatasetProfileRepository:

    def create(self, session: Session, profile: DatasetProfile) -> DatasetProfile:
        session.add(profile)
        session.commit()
        session.refresh(profile)
        return profile

    def get_by_id(self, session: Session, profile_id: str) -> Optional[DatasetProfile]:
        return session.get(DatasetProfile, profile_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[DatasetProfile]:
        statement = (
            select(DatasetProfile)
            .where(DatasetProfile.task_id == task_id)
            .order_by(DatasetProfile.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[DatasetProfile]:
        statement = (
            select(DatasetProfile)
            .where(DatasetProfile.task_id == task_id)
            .order_by(DatasetProfile.created_at.desc())
        )
        return list(session.exec(statement).all())
