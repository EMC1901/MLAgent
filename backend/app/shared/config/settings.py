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

    # Feature engineering configuration
    FEATURE_ARTIFACT_DIR: str = "/app/artifacts/features"
    FEATURE_ARTIFACT_FORMAT: str = "parquet"
    FEATURE_PREVIEW_ROWS: int = 20
    FEATURE_MAX_FAILED_SAMPLE_RATIO: float = 0.2
    ENABLE_COMPOSITION_FEATURIZER: bool = True
    ENABLE_DESCRIPTOR_FEATURIZER: bool = True
    ENABLE_STRUCTURE_FEATURIZER: bool = False

    # External feature library configuration
    ENABLE_PYMATGEN: bool = True
    ENABLE_MATMINER: bool = True
    ENABLE_MATMINER_MAGPIE: bool = True
    ENABLE_MATMINER_STOICHIOMETRY: bool = True
    ENABLE_MATMINER_ELEMENT_PROPERTY: bool = True
    ENABLE_MATMINER_VALENCE_ORBITAL: bool = True
    ENABLE_STRUCTURE_FEATURIZER_FULL: bool = False
    MAX_FEATURE_DIMENSION: int = 2000
    MAX_FEATURE_MISSING_RATIO: float = 0.5
    FEATURE_GROUP_PREFIX_ENABLED: bool = True
    FEATURE_EXTERNAL_LIBRARY_TIMEOUT: int = 300

    # Feature preprocessing configuration
    MODEL_READY_ARTIFACT_DIR: str = "/app/artifacts/model_ready"
    MODEL_READY_ARTIFACT_FORMAT: str = "parquet"
    PREPROCESSOR_ARTIFACT_FORMAT: str = "joblib"
    FEATURE_PREPROCESSING_PREVIEW_ROWS: int = 20
    FEATURE_PREPROCESSING_MAX_MISSING_RATIO: float = 0.5
    FEATURE_PREPROCESSING_DROP_INVALID: bool = True
    FEATURE_PREPROCESSING_DROP_ALL_MISSING: bool = True
    FEATURE_PREPROCESSING_DROP_CONSTANT: bool = True
    FEATURE_PREPROCESSING_DROP_HIGH_MISSING: bool = True
    FEATURE_PREPROCESSING_MIN_VALID_FEATURES: int = 1
    FEATURE_PREPROCESSING_IMPUTATION_STRATEGY: str = "median"
    FEATURE_PREPROCESSING_SCALING_STRATEGY: str = "standard_scaler"
    FEATURE_PREPROCESSING_ENABLE_FEATURE_SELECTION: bool = True
    FEATURE_PREPROCESSING_FEATURE_SELECTION_STRATEGY: str = "variance_threshold"
    FEATURE_PREPROCESSING_ALLOW_CATEGORICAL: bool = False

    # Model search context configuration
    MODEL_CONTEXT_ENABLE_LLM_ADVISOR: bool = True
    MODEL_CONTEXT_LLM_TEMPERATURE: float = 0.0
    MODEL_CONTEXT_LLM_TIMEOUT: int = 60
    MODEL_CONTEXT_LLM_MAX_RETRIES: int = 2

    MODEL_CONTEXT_LOW_FEATURE_THRESHOLD: int = 20
    MODEL_CONTEXT_HIGH_REDUCTION_RATIO: float = 0.8
    MODEL_CONTEXT_SMALL_SAMPLE_THRESHOLD: int = 200

    MODEL_CONTEXT_MAX_HPO_TRIALS: int = 50
    MODEL_CONTEXT_DEFAULT_HPO_MAX_TRIALS_SMALL: int = 20
    MODEL_CONTEXT_DEFAULT_HPO_MAX_TRIALS_MEDIUM: int = 30
    MODEL_CONTEXT_DEFAULT_HPO_MAX_TRIALS_LARGE: int = 50

    class Config:
        env_file = ".env"


settings = Settings()
