import logging
import os
import sys
import warnings

# Suppress sklearn ConvergenceWarning noise
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
warnings.filterwarnings("ignore", message=".*did not converge.*")

# ── Application logging ──
# uvicorn applies logging.config.dictConfig AFTER the on_event("startup")
# handler runs, which overwrites any root-level handler we install.
# Workaround: install a handler directly on every "app.*" logger as they are
# created, via a small monkey-patch on logging.getLogger.

# Respect LOG_LEVEL env var (default INFO)
_LOG_LEVEL_NAME = os.environ.get("LOG_LEVEL", "INFO").upper()
_LOG_LEVEL = getattr(logging, _LOG_LEVEL_NAME, logging.INFO)

_APP_FMT = logging.Formatter(
    "%(asctime)s  %(levelname)-5s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
_APP_HANDLER = logging.StreamHandler(sys.stderr)
_APP_HANDLER.setFormatter(_APP_FMT)
_APP_HANDLER_LOGGERS = set()

_orig_getLogger = logging.getLogger

def _patched_getLogger(name=None):
    logger = _orig_getLogger(name)
    if name and (name == "app" or name.startswith("app.")):
        logger.setLevel(_LOG_LEVEL)
        if _APP_HANDLER not in logger.handlers:
            logger.addHandler(_APP_HANDLER)
            _APP_HANDLER_LOGGERS.add(logger)
        logger.propagate = False
    return logger

logging.getLogger = _patched_getLogger

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from alembic.config import Config
from alembic import command
from app.shared.config.settings import settings
from app.shared.database.connection import engine
from app.shared.common.response import error_response
from app.shared.common.exceptions import BusinessException
from app.modules.task_specification.api import router as task_spec_router
from app.modules.task_interpretation.api import router as task_interp_router
from app.modules.dataset_profile.api import router as dataset_profile_router
from app.modules.workflow_planning.api import router as workflow_planning_router
from app.modules.feature_engineering.api import router as feature_engineering_router
from app.modules.feature_engineering.registry_api import registry_router
from app.modules.feature_preprocessing.api import router as feature_preprocessing_router
from app.modules.model_search_context.api import router as model_search_context_router
from app.modules.pipeline_generation.api import router as pipeline_generation_router
from app.modules.pipeline_execution.api import router as pipeline_execution_router
from app.modules.metric_evaluation.api import router as metric_evaluation_router
from app.modules.iteration_decision.api import router as iteration_decision_router
from app.modules.interpretability_analysis.api import router as interpretability_analysis_router
from app.modules.final_output.api import router as final_output_router
from app.modules.visualization.api import router as visualization_router
from app.modules.llm_config.api import router as llm_config_router

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Suppress verbose third-party logging
    for lib in ("sklearn", "optuna", "matplotlib", "PIL", "uvicorn", "fastapi"):
        logging.getLogger(lib).setLevel(logging.WARNING)
    try:
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
    except ImportError:
        pass

    # On a fresh database, create all tables directly from SQLModel metadata.
    # Alembic migrations are only needed when migrating from an older schema.
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(bind=engine)
    logger.info("MLAgent backend started successfully.")


@app.on_event("shutdown")
def on_shutdown():
    logger.info("MLAgent backend shutting down...")

    # Dispose the database connection pool — this closes all pooled TCP
    # connections to PostgreSQL so the process can exit cleanly.
    try:
        engine.dispose()
        logger.info("Database connection pool disposed.")
    except Exception:
        logger.exception("Failed to dispose database engine.")

    # Remove the application-level stream handler so that any remaining
    # file descriptors are released before the interpreter finalizes.
    for h in list(_APP_HANDLER_LOGGERS):
        try:
            h.removeHandler(_APP_HANDLER)
        except Exception:
            pass
    _APP_HANDLER_LOGGERS.clear()
    _APP_HANDLER.close()

    logger.info("MLAgent backend shutdown complete.")


app.include_router(task_spec_router)
app.include_router(task_interp_router)
app.include_router(dataset_profile_router)
app.include_router(workflow_planning_router)
app.include_router(feature_engineering_router)
app.include_router(registry_router)
app.include_router(feature_preprocessing_router)
app.include_router(model_search_context_router)
app.include_router(pipeline_generation_router)
app.include_router(pipeline_execution_router)
app.include_router(metric_evaluation_router)
app.include_router(iteration_decision_router)
app.include_router(interpretability_analysis_router)
app.include_router(final_output_router)
app.include_router(visualization_router)
app.include_router(llm_config_router)


@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=400,
        content=error_response(message=exc.message, error_code=exc.error_code),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content=error_response(
            message=f"Internal server error: {str(exc)}" if settings.DEBUG else "Internal server error.",
            error_code="INTERNAL_ERROR",
        ),
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}
