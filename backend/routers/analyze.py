
import asyncio
import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

import engine
import models
from backend.schemas import ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Analysis"])

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/analyze", response_model=ChatResponse)
async def analyze_endpoint(
    file: UploadFile = File(...),
    prompt: str = Form(
        default=(
            "Identify this component or circuit, explain key pinouts "
            "or specifications, and note practical lab usage."
        ),
    ),
    provider: str | None = Form(default=None),
    model_id: str | None = Form(default=None),
    model: str | None = Form(default=None),
) -> ChatResponse:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image type. Use JPEG, PNG, WEBP, or GIF.",
        )

    image_bytes = bytearray()

    try:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break

            image_bytes.extend(chunk)

            if len(image_bytes) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Uploaded image exceeds the 10 MB limit.",
                )
    finally:
        await file.close()

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image is empty.",
        )

    # Optical analysis strictly requires multimodal vision.
    # Always utilize a vision-capable model (Gemini), regardless of text model selection.
    gemini_config = models.get_model("Gemini")
    resolved_provider = "Gemini"
    resolved_model_id = gemini_config.get("model_id", "gemini-3.8-flash")

    # If the caller requested a specific Gemini vision model, respect it
    requested_model = model or model_id
    if requested_model and "gemini" in requested_model.lower():
        resolved_model_id = requested_model

    if not resolved_model_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No vision model is configured.",
        )

    original_model_id = resolved_model_id
    fallback_used = False
    attempts = 1
    # Silent failover buffer: default models first, then lightweight high-throughput fallbacks
    fallback_candidates = [
        "gemini-3.8-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-flash-latest",
    ]

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                engine.run_engine,
                provider=resolved_provider,
                model_id=resolved_model_id,
                user_text=prompt,
                conversation_history=None,
                image_bytes=bytes(image_bytes),
                mime_type=file.content_type,
                previous_visual_context=None,
            ),
            timeout=25.0,
        )
    except asyncio.TimeoutError:
        logger.warning(f"Image analysis timed out (25s) for {resolved_model_id}")
        result = None
    except Exception as exc:
        logger.warning(f"Image analysis failed for {resolved_model_id}: {exc}")
        result = None

    if not result or result.get("status") == "error":
        logger.warning(
            f"Vision model {original_model_id} failed. Initiating fallback to working default vision models."
        )
        for fb_model in fallback_candidates:
            if fb_model == original_model_id:
                continue

            attempts += 1
            try:
                fb_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        engine.run_engine,
                        provider="Gemini",
                        model_id=fb_model,
                        user_text=prompt,
                        conversation_history=None,
                        image_bytes=bytes(image_bytes),
                        mime_type=file.content_type,
                        previous_visual_context=None,
                    ),
                    timeout=20.0,
                )
                if fb_result and fb_result.get("status") != "error":
                    result = fb_result
                    resolved_provider = "Gemini"
                    resolved_model_id = fb_model
                    fallback_used = True
                    break
            except asyncio.TimeoutError:
                logger.warning(f"Fallback vision candidate {fb_model} timed out after 20s.")
                continue
            except Exception as fb_exc:
                logger.warning(f"Fallback vision candidate {fb_model} failed: {fb_exc}")
                continue

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CircuitSnap could not analyze this image after all fallback attempts.",
        )

    final_fallback_used = result.get("fallback_used", False) or fallback_used
    final_attempts = max(result.get("attempts", attempts), attempts)

    return ChatResponse(
        answer=result.get("answer") or "",
        provider=result.get("provider") or resolved_provider,
        model_id=result.get("model_id") or resolved_model_id,
        status=result.get("status", "error"),
        error_type=result.get("error_type"),
        fallback_used=final_fallback_used,
        attempts=final_attempts,
        original_model=original_model_id if final_fallback_used else None,
    )
