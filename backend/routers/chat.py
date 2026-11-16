import asyncio
import logging

from fastapi import APIRouter, status
from backend.jarvis_engine.orchestrator import process_jarvis_query
from backend.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Sub-50ms offline J.A.R.V.I.S. Chat endpoint.
    Handles component lookups, math derivations, and technical queries instantly.
    """
    history = [
        message.model_dump() for message in request.history
    ] if request.history else None

    # Resolve model_id
    model_id = request.model or request.model_id or "jarvis-auto"
    if model_id == "auto":
        model_id = "jarvis-auto"

    # Execute completely offline in background thread
    result = await asyncio.to_thread(
        process_jarvis_query,
        user_text=request.message,
        image_bytes=None,
        conversation_history=history,
        model_id=model_id,
    )

    return ChatResponse(
        answer=result.get("answer", ""),
        provider=result.get("provider", "J.A.R.V.I.S. Core"),
        model_id=result.get("model_id", model_id),
        status=result.get("status", "success"),
        error_type=result.get("error_type"),
        fallback_used=result.get("fallback_used", False),
        attempts=result.get("attempts", 1),
    )
