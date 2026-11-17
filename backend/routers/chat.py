import json
import logging
import time
from typing import Generator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.jarvis_engine.orchestrator import (
    process_jarvis_query,
    get_cognitive_trace_steps,
    detect_response_style,
)
from backend.schemas import ChatRequest, ChatResponse
from providers import redact_secrets

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Sub-20ms offline J.A.R.V.I.S. Chat endpoint.
    Handles component lookups, math derivations, and multi-branch engineering queries instantly.
    """
    history = [
        message.model_dump() for message in request.history
    ] if request.history else None

    # Resolve model_id
    model_id = request.model or request.model_id or "jarvis-auto"
    if model_id == "auto":
        model_id = "jarvis-auto"

    chosen_style = request.response_style or request.style

    user_message = request.message
    if request.privacy_mode == "guarded":
        user_message = redact_secrets(user_message)
        if history:
            history = [
                {"role": m.get("role", "user"), "content": redact_secrets(str(m.get("content", "")))}
                for m in history
            ]

    # Execute completely offline in memory
    result = process_jarvis_query(
        user_text=user_message,
        image_bytes=None,
        conversation_history=history,
        model_id=model_id,
        response_style=chosen_style,
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


@router.post("/chat/stream")
def chat_stream_endpoint(request: ChatRequest):
    """
    Server-Sent Events (SSE) streaming endpoint for J.A.R.V.I.S.
    Emits real-time cognitive trace steps ('step' events) and smooth response tokens ('chunk' events).
    """
    history = [
        message.model_dump() for message in request.history
    ] if request.history else None

    model_id = request.model or request.model_id or "jarvis-auto"
    if model_id == "auto":
        model_id = "jarvis-auto"

    chosen_style = request.response_style or request.style or detect_response_style(request.message)

    stream_message = request.message
    if request.privacy_mode == "guarded":
        stream_message = redact_secrets(stream_message)
        if history:
            history = [
                {"role": m.get("role", "user"), "content": redact_secrets(str(m.get("content", "")))}
                for m in history
            ]

    def sse_generator() -> Generator[str, None, None]:
        try:
            # 1. Emit cognitive trace steps
            steps = get_cognitive_trace_steps(stream_message, model_id, chosen_style)
            for s in steps:
                yield f"event: step\ndata: {json.dumps({'step': s})}\n\n"
                time.sleep(0.01)

            # 2. Run offline computation in memory
            result = process_jarvis_query(
                user_text=stream_message,
                image_bytes=None,
                conversation_history=history,
                model_id=model_id,
                response_style=chosen_style,
            )

            full_answer = result.get("answer", "")

            # 3. Stream chunks smoothly (words/tokens with micro delay)
            # Split into small chunks of ~4-8 words for smooth Google Flow spatial feel
            words = full_answer.split(" ")
            chunk_size = 5
            for i in range(0, len(words), chunk_size):
                chunk_slice = " ".join(words[i:i + chunk_size]) + (" " if i + chunk_size < len(words) else "")
                yield f"event: chunk\ndata: {json.dumps({'chunk': chunk_slice})}\n\n"
                time.sleep(0.005)

            # 4. Final completion payload
            final_meta = {
                "answer": full_answer,
                "provider": result.get("provider", "J.A.R.V.I.S. Core"),
                "model_id": result.get("model_id", model_id),
                "style": result.get("style", chosen_style),
                "attempts": result.get("attempts", 1),
                "fallback_used": result.get("fallback_used", False),
            }
            yield f"event: done\ndata: {json.dumps(final_meta)}\n\n"
        except (GeneratorExit, ConnectionResetError, BrokenPipeError):
            logger.info("SSE client disconnected mid-stream.")
            return
        except Exception as err:
            logger.error("SSE stream encountered unexpected error: %s", err, exc_info=True)
            fallback_payload = {
                "answer": "An unexpected error occurred while processing the engineering response. Please try again or rephrase your query.",
                "provider": "J.A.R.V.I.S. Core",
                "model_id": model_id,
                "style": chosen_style,
                "attempts": 1,
                "fallback_used": True,
                "status": "error",
                "error_type": type(err).__name__,
            }
            yield f"event: done\ndata: {json.dumps(fallback_payload)}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
