import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import pool
from sqlmodel import SQLModel
from alembic import context

# Ensure backend app is on the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.shared.config.settings import settings
from app.shared.database.connection import engine

# Import ALL model modules so SQLModel.metadata discovers every table
import app.modules.task_specification.model          # noqa: F401
import app.modules.task_interpretation.model         # noqa: F401
import app.modules.dataset_profile.model             # noqa: F401
import app.modules.workflow_planning.model           # noqa: F401
import app.modules.feature_engineering.model         # noqa: F401
import app.modules.feature_preprocessing.model       # noqa: F401
import app.modules.model_search_context.model        # noqa: F401
import app.modules.pipeline_generation.model         # noqa: F401
import app.modules.pipeline_execution.model          # noqa: F401
import app.modules.metric_evaluation.model           # noqa: F401
import app.modules.iteration_decision.model          # noqa: F401
import app.modules.interpretability_analysis.model   # noqa: F401
import app.modules.final_output.model                # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
