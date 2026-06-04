from pydantic import BaseModel, Field


class LLMConfigRequest(BaseModel):
    model_name: str = Field(..., min_length=1, max_length=256, description="LLM model name, e.g. gpt-4.1 or deepseek-v4-pro")
    thinking_enabled: bool = Field(False, description="Enable extended thinking / reasoning mode")
    api_key: str = Field(..., min_length=1, max_length=512, description="API key for the LLM provider")
    base_url: str = Field("", max_length=1024, description="Optional base URL for the LLM API")


class LLMConfigResponse(BaseModel):
    model_name: str
    thinking_enabled: bool
    api_key_masked: str
    base_url: str
    is_custom: bool


class LLMConfigValidateResponse(BaseModel):
    valid: bool
    message: str
    model_name: str
    latency_ms: float = 0.0
    tokens_used: int = 0
