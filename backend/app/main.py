from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel
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
    SQLModel.metadata.create_all(engine)


@app.on_event("shutdown")
def on_shutdown():
    pass


app.include_router(task_spec_router)
app.include_router(task_interp_router)
app.include_router(dataset_profile_router)
app.include_router(workflow_planning_router)
app.include_router(feature_engineering_router)
app.include_router(registry_router)
app.include_router(feature_preprocessing_router)


@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=400,
        content=error_response(message=exc.message, error_code=exc.error_code),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=error_response(message="Internal server error.", error_code="INTERNAL_ERROR"),
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}
