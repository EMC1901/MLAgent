from sqlmodel import create_engine
from app.shared.config.settings import settings

engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)
