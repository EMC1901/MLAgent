import logging

from fastapi import APIRouter

from app.shared.common.response import success_response, error_response
from app.modules.llm_config.schemas import LLMConfigRequest
from app.modules.llm_config import service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm-config", tags=["LLM Configuration"])


@router.post("")
async def set_llm_config(request: LLMConfigRequest):
    """Set and validate a custom LLM configuration.

    The configuration is validated by sending a test request to the LLM API
    before being stored. Once set, all subsequent LLM calls use this config.
    """
    config_response, validation = await service.set_config(request)
    if not validation.valid:
        return error_response(
            message=validation.message,
            error_code="LLM_VALIDATION_FAILED",
            data={
                "config": config_response.model_dump(),
                "validation": validation.model_dump(),
            },
        )
    return success_response(
        message="LLM configuration validated and applied successfully.",
        data={
            "config": config_response.model_dump(),
            "validation": validation.model_dump(),
        },
    )


@router.get("")
async def get_llm_config():
    """Return the current LLM configuration with masked API key."""
    config = service.get_config()
    return success_response(
        message="Current LLM configuration.",
        data=config.model_dump(),
    )


@router.delete("")
async def reset_llm_config():
    """Reset LLM configuration to server defaults (from .env / settings)."""
    config = service.clear_config()
    logger.info("LLM config reset to server defaults")
    return success_response(
        message="LLM configuration reset to server defaults.",
        data=config.model_dump(),
    )
