from typing import Optional, List
from sqlmodel import Session, select
from app.modules.final_pipeline_selection.model import FinalPipelineSelection


class FinalPipelineSelectionRepository:

    def create(self, session: Session, record: FinalPipelineSelection) -> FinalPipelineSelection:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    def get_by_id(self, session: Session, fps_id: str) -> Optional[FinalPipelineSelection]:
        return session.get(FinalPipelineSelection, fps_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[FinalPipelineSelection]:
        statement = (
            select(FinalPipelineSelection)
            .where(FinalPipelineSelection.task_id == task_id)
            .order_by(FinalPipelineSelection.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[FinalPipelineSelection]:
        statement = (
            select(FinalPipelineSelection)
            .where(FinalPipelineSelection.task_id == task_id)
            .order_by(FinalPipelineSelection.created_at.desc())
        )
        return list(session.exec(statement).all())

    def update(self, session: Session, record: FinalPipelineSelection) -> FinalPipelineSelection:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
