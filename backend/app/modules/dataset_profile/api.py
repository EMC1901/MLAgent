import os
import uuid

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from app.shared.database.session import get_session
from app.shared.common.response import success_response
from app.shared.common.exceptions import BusinessException
from app.shared.config.settings import settings
from app.modules.dataset_profile.schemas import (
    DatasetProfileCreateRequest,
    DatasetFileUploadResponse,
)
from app.modules.dataset_profile.service import DatasetProfileService

router = APIRouter(prefix="/api", tags=["dataset-profile"])
service = DatasetProfileService()


@router.post("/dataset-profiles/upload", response_model=dict)
async def upload_dataset_file(file: UploadFile = File(...)):
    allowed_ext = set(
        e.strip() for e in settings.DATASET_ALLOWED_EXTENSIONS.split(",")
    )
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext.lstrip(".") not in allowed_ext and ext not in allowed_ext:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Unsupported file type '{ext}'. Allowed: {allowed_ext}",
                "error_code": "UNSUPPORTED_FILE_TYPE",
            },
        )

    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)
    if file_size_mb > settings.DATASET_MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    f"File size {file_size_mb:.1f}MB exceeds limit "
                    f"of {settings.DATASET_MAX_FILE_SIZE_MB}MB."
                ),
                "error_code": "FILE_TOO_LARGE",
            },
        )

    upload_dir = settings.DATASET_UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    file_id = f"file_{uuid.uuid4().hex[:8]}{ext}"
    save_path = os.path.join(upload_dir, file_id)
    with open(save_path, "wb") as f:
        f.write(contents)

    try:
        if ext in (".csv",):
            df = pd.read_csv(save_path)
        else:
            df = pd.read_excel(save_path)
    except Exception as e:
        os.remove(save_path)
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Failed to parse file: {str(e)}",
                "error_code": "FILE_PARSE_ERROR",
            },
        )

    if df.empty:
        os.remove(save_path)
        raise HTTPException(
            status_code=400,
            detail={
                "message": "File contains no data rows.",
                "error_code": "FILE_EMPTY",
            },
        )

    preview_rows = (
        df.head(settings.DATASET_PREVIEW_ROWS)
        .fillna("")
        .to_dict(orient="records")
    )

    result = DatasetFileUploadResponse(
        file_id=file_id,
        file_name=file.filename or "unknown",
        file_size_bytes=len(contents),
        n_rows=len(df),
        n_columns=len(df.columns),
        columns=list(df.columns),
        preview_rows=preview_rows,
    )

    return success_response(
        "File uploaded successfully.",
        data=result.model_dump(),
    )


@router.post("/dataset-profiles/{task_id}", response_model=dict)
def create_dataset_profile(
    task_id: str,
    request: DatasetProfileCreateRequest = DatasetProfileCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.create_profile(session, task_id, request)
        return success_response(
            "Dataset profile created successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=400,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/dataset-profiles/{dataset_profile_id}", response_model=dict)
def get_dataset_profile(dataset_profile_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_profile(session, dataset_profile_id)
        return success_response(
            "Dataset profile retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code == "DATASET_PROFILE_NOT_FOUND" else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/tasks/{task_id}/dataset-profile", response_model=dict)
def get_latest_dataset_profile(task_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_latest_by_task_id(session, task_id)
        return success_response(
            "Latest dataset profile retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code == "DATASET_PROFILE_NOT_FOUND" else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.post("/dataset-profiles/{task_id}/rerun", response_model=dict)
def rerun_dataset_profile(
    task_id: str,
    request: DatasetProfileCreateRequest = DatasetProfileCreateRequest(),
    session: Session = Depends(get_session),
):
    try:
        result = service.rerun_profile(session, task_id, request)
        return success_response(
            "Dataset profile re-run successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        raise HTTPException(
            status_code=400,
            detail={"message": e.message, "error_code": e.error_code},
        )


@router.get("/dataset-profiles/{dataset_profile_id}/preview", response_model=dict)
def get_dataset_preview(dataset_profile_id: str, session: Session = Depends(get_session)):
    try:
        result = service.get_preview(session, dataset_profile_id)
        return success_response(
            "Dataset preview retrieved successfully.",
            data=result.model_dump(),
        )
    except BusinessException as e:
        status_code = 404 if e.error_code == "DATASET_PROFILE_NOT_FOUND" else 400
        raise HTTPException(
            status_code=status_code,
            detail={"message": e.message, "error_code": e.error_code},
        )
