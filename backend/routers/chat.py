import logging

from fastapi import APIRouter, HTTPException, status

import engine
import models
from backend.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    # Resolve provider and model_id based on request.model or fallback to provider config
    if request.model and request.model != "auto":
        model_str = request.model.lower()
        if "gemini" in model_str:
            provider = "Gemini"
            model_id = request.model
        elif any(k in model_str for k in ("groq", "llama", "qwen")):
            provider = "Groq"
            model_id = request.model
        else:
            try:
                cfg = models.get_model(request.model)
                provider = cfg.get("provider", request.model)
                model_id = cfg.get("model_id")
            except (KeyError, ValueError):
                default_name = models.get_default_model()
                provider_config = models.get_model(default_name)
                provider = provider_config.get("provider", default_name)
                model_id = provider_config.get("model_id")
    else:
        default_name = models.get_default_model()
        chosen_name = request.provider or default_name

        try:
            provider_config = models.get_model(chosen_name)
        except (KeyError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: '{chosen_name}'",
            ) from exc

        provider = provider_config.get("provider", chosen_name)
        model_id = request.model_id or provider_config.get("model_id")

    if not model_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No model is configured for this provider.",
        )

    history = [
        message.model_dump() for message in request.history
    ] or None

    try:
        result = engine.run_engine(
            provider=provider,
            model_id=model_id,
            user_text=request.message,
            conversation_history=history,
            image_bytes=None,
            mime_type=None,
            previous_visual_context=request.previous_visual_context,
        )
    except Exception as exc:
        logger.exception("CircuitSnap engine execution failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CircuitSnap could not process this request.",
        ) from exc

    return ChatResponse(
        answer=result.get("answer") or "",
        provider=result.get("provider") or provider,
        model_id=result.get("model_id") or model_id,
        status=result.get("status", "error"),
        error_type=result.get("error_type"),
        fallback_used=result.get("fallback_used", False),
        attempts=result.get("attempts", 1),
    )