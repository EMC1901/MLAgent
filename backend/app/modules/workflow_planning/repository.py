from sqlmodel import Session, select
from app.modules.workflow_planning.model import WorkflowPlan
from typing import Optional, List


class WorkflowPlanRepository:

    def create(self, session: Session, plan: WorkflowPlan) -> WorkflowPlan:
        session.add(plan)
        session.commit()
        session.refresh(plan)
        return plan

    def get_by_id(self, session: Session, plan_id: str) -> Optional[WorkflowPlan]:
        return session.get(WorkflowPlan, plan_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[WorkflowPlan]:
        statement = (
            select(WorkflowPlan)
            .where(WorkflowPlan.task_id == task_id)
            .order_by(WorkflowPlan.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[WorkflowPlan]:
        statement = (
            select(WorkflowPlan)
            .where(WorkflowPlan.task_id == task_id)
            .order_by(WorkflowPlan.created_at.desc())
        )
        return list(session.exec(statement).all())
