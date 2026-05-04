from sqlmodel import Session, select
from app.modules.pipeline_generation.model import PipelineGeneration
from typing import Optional, List


class PipelineGenerationRepository:

    def create(self, session: Session, record: PipelineGeneration) -> PipelineGeneration:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    def get_by_id(self, session: Session, pg_id: str) -> Optional[PipelineGeneration]:
        return session.get(PipelineGeneration, pg_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[PipelineGeneration]:
        statement = (
            select(PipelineGeneration)
            .where(PipelineGeneration.task_id == task_id)
            .order_by(PipelineGeneration.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[PipelineGeneration]:
        statement = (
            select(PipelineGeneration)
            .where(PipelineGeneration.task_id == task_id)
            .order_by(PipelineGeneration.created_at.desc())
        )
        return list(session.exec(statement).all())
