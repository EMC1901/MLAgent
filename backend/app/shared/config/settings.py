from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "MLAgent"
    APP_ENV: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/mlagent"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # LLM configuration
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4.1"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_TIMEOUT: int = 60
    LLM_MAX_RETRIES: int = 2
    LLM_TEMPERATURE: float = 0.0

    # Dataset upload configuration
    DATASET_UPLOAD_DIR: str = "/app/uploads"
    DATASET_MAX_FILE_SIZE_MB: int = 100
    DATASET_ALLOWED_EXTENSIONS: str = "csv,xlsx,xls"
    DATASET_PREVIEW_ROWS: int = 20

    class Config:
        env_file = ".env"


settings = Settings()
