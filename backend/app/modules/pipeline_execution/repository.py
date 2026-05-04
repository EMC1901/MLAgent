from sqlmodel import Session, select
from app.modules.pipeline_execution.model import PipelineExecution
from typing import Optional, List


class PipelineExecutionRepository:

    def create(self, session: Session, record: PipelineExecution) -> PipelineExecution:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    def get_by_id(self, session: Session, pe_id: str) -> Optional[PipelineExecution]:
        return session.get(PipelineExecution, pe_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[PipelineExecution]:
        statement = (
            select(PipelineExecution)
            .where(PipelineExecution.task_id == task_id)
            .order_by(PipelineExecution.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[PipelineExecution]:
        statement = (
            select(PipelineExecution)
            .where(PipelineExecution.task_id == task_id)
            .order_by(PipelineExecution.created_at.desc())
        )
        return list(session.exec(statement).all())

    def update(self, session: Session, record: PipelineExecution) -> PipelineExecution:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
