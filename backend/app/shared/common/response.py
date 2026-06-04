from pydantic import BaseModel
from typing import Any, Optional, Generic, TypeVar, List


T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    error_code: Optional[str] = None


class APIResponseList(BaseModel, Generic[T]):
    success: bool
    message: str
    data: List[T]
    total: int = 0
    error_code: Optional[str] = None


def success_response(message: str, data: Any = None) -> dict:
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def success_list_response(message: str, data: List[Any], total: int = 0) -> dict:
    return {
        "success": True,
        "message": message,
        "data": data,
        "total": total,
    }


def error_response(message: str, error_code: Optional[str] = None, data: Any = None) -> dict:
    return {
        "success": False,
        "message": message,
        "data": data,
        "error_code": error_code,
    }
