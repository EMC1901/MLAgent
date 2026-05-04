from sqlmodel import Session, select
from app.modules.model_search.model import ModelSearchPlan
from typing import Optional, List


class ModelSearchPlanRepository:

    def create(self, session: Session, record: ModelSearchPlan) -> ModelSearchPlan:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    def get_by_id(self, session: Session, plan_id: str) -> Optional[ModelSearchPlan]:
        return session.get(ModelSearchPlan, plan_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[ModelSearchPlan]:
        statement = (
            select(ModelSearchPlan)
            .where(ModelSearchPlan.task_id == task_id)
            .order_by(ModelSearchPlan.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[ModelSearchPlan]:
        statement = (
            select(ModelSearchPlan)
            .where(ModelSearchPlan.task_id == task_id)
            .order_by(ModelSearchPlan.created_at.desc())
        )
        return list(session.exec(statement).all())
