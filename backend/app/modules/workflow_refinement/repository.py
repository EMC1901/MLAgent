from typing import Optional, List
from sqlmodel import Session, select
from app.modules.workflow_refinement.model import WorkflowRefinement


class WorkflowRefinementRepository:

    def create(self, session: Session, record: WorkflowRefinement) -> WorkflowRefinement:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    def get_by_id(self, session: Session, wr_id: str) -> Optional[WorkflowRefinement]:
        return session.get(WorkflowRefinement, wr_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[WorkflowRefinement]:
        statement = (
            select(WorkflowRefinement)
            .where(WorkflowRefinement.task_id == task_id)
            .order_by(WorkflowRefinement.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[WorkflowRefinement]:
        statement = (
            select(WorkflowRefinement)
            .where(WorkflowRefinement.task_id == task_id)
            .order_by(WorkflowRefinement.created_at.desc())
        )
        return list(session.exec(statement).all())

    def get_by_result_diagnosis_id(
        self, session: Session, rd_id: str
    ) -> Optional[WorkflowRefinement]:
        statement = (
            select(WorkflowRefinement)
            .where(WorkflowRefinement.result_diagnosis_id == rd_id)
            .order_by(WorkflowRefinement.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def update(self, session: Session, record: WorkflowRefinement) -> WorkflowRefinement:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
