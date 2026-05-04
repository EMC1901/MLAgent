from sqlmodel import Session, select
from app.modules.model_search_context.model import ModelSearchContext
from typing import Optional, List


class ModelSearchContextRepository:

    def create(self, session: Session, record: ModelSearchContext) -> ModelSearchContext:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    def get_by_id(self, session: Session, msc_id: str) -> Optional[ModelSearchContext]:
        return session.get(ModelSearchContext, msc_id)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> Optional[ModelSearchContext]:
        statement = (
            select(ModelSearchContext)
            .where(ModelSearchContext.task_id == task_id)
            .order_by(ModelSearchContext.created_at.desc())
            .limit(1)
        )
        return session.exec(statement).first()

    def list_by_task_id(self, session: Session, task_id: str) -> List[ModelSearchContext]:
        statement = (
            select(ModelSearchContext)
            .where(ModelSearchContext.task_id == task_id)
            .order_by(ModelSearchContext.created_at.desc())
        )
        return list(session.exec(statement).all())
