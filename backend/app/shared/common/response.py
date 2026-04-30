from pydantic import BaseModel
from typing import Any, Optional


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None


def success_response(message: str, data: Any = None) -> dict:
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def error_response(message: str, error_code: Optional[str] = None, data: Any = None) -> dict:
    return {
        "success": False,
        "message": message,
        "data": data,
        "error_code": error_code,
    }
