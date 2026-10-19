from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class UserRegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class UserLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: str
    username: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ChatMessage(BaseModel):
    """A message from the conversation history."""

    role: Literal["user", "assistant"]
    content: str


class ModelOption(BaseModel):
    """Available AI model configuration."""

    id: str
    label: str
    provider: str
    specialty: str
    supports_vision: bool


class ModelsResponse(BaseModel):
    """Response from GET /api/models."""

    models: list[ModelOption]
    default_model: str


class ChatRequest(BaseModel):
    """Request body for POST /api/chat."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=20000)
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=100,
    )
    provider: str | None = None
    model_id: str | None = None
    model: str | None = None
    previous_visual_context: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    """Public response for the chat endpoint."""

    answer: str
    provider: str
    model_id: str
    status: Literal["success", "error"]
    error_type: str | None = None
    fallback_used: bool = False
    attempts: int = 1


class HealthResponse(BaseModel):
    """Response from GET /api/health."""

    status: str
    models: dict[str, Any]