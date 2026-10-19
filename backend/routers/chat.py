import logging
import re

from fastapi import APIRouter, HTTPException, status

import engine
import models
import providers
from backend.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Chat"])

MATH_FORMULA_PATTERN = re.compile(
    r"(?i)\b(calculate|computation|derive|derivation|formula|equation|math|"
    r"impedance|transfer\s*function|fourier|laplace|bode|decibel|\bdb\b|gain|"
    r"resonance|resonant|cutoff\s*frequency|frequency\s*response|ohms?\s*law|"
    r"thevenin|norton|kirchhoff|kvl|kcl|reactance|inductance|capacitance|"
    r"integral|differential|diff\s*amp|op-?amp\s*gain|filter\s*order)\b|"
    r"[\$\\\^]|(?:[0-9\.]+\s*[\+\-\*\/]\s*[0-9\.]+)|(?:=.*[\+\-\*\/])"
)

LOOKUP_PATTERN = re.compile(
    r"(?i)\b(pinout|pin\s*diagram|pin\s*\d+|datasheet|pins|package|smd\s*code|"
    r"marking|specs|specifications|ratings|absolute\s*maximum|quick\s*lookup|"
    r"what\s*is|define|definition|lead\s*spacing|pitch)\b"
)


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
    elif request.model is None and request.provider:
        chosen_name = request.provider
        try:
            provider_config = models.get_model(chosen_name)
        except (KeyError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: '{chosen_name}'",
            ) from exc

        provider = provider_config.get("provider", chosen_name)
        model_id = request.model_id or provider_config.get("model_id")
    else:
        # Autonomous Smart Router:
        # 1. Math/formula queries -> gemini-3.8-flash (current verified endpoint for circuit math & derivations)
        # 2. Text-only lookups -> Groq llama-3.3-70b-versatile (if Groq key available)
        # 3. Optical / general queries -> gemini-3.8-flash (active default)
        has_groq = bool(providers._get_api_key("GROQ_API_KEY"))
        message_text = request.message or ""

        if MATH_FORMULA_PATTERN.search(message_text):
            provider = "Gemini"
            model_id = "gemini-3.8-flash"
        elif has_groq and LOOKUP_PATTERN.search(message_text):
            provider = "Groq"
            model_id = "llama-3.3-70b-versatile"
        else:
            provider = "Gemini"
            model_id = "gemini-3.8-flash"

    if not model_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No model is configured for this provider.",
        )

    history = [
        message.model_dump() for message in request.history
    ] or None

    original_provider = provider
    original_model_id = model_id
    fallback_used = False
    attempts = 1
    result = None

    # Fallback roster: default model first ("gemini-3.8-flash"), then "gemini-3.6-flash" / "gemini-2.5-flash"
    fallback_candidates = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-2.5-flash"]

    # 1. First attempt with requested or auto-routed model
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
        logger.warning(
            f"Execution failed for {provider}/{model_id}: {exc}. Triggering fallback."
        )
        result = None

    # 2. If initial attempt failed (exception or returned status == 'error'), try fallback candidates
    if not result or result.get("status") == "error":
        error_type = result.get("error_type") if result else "exception"
        logger.warning(
            f"Model {original_model_id} failed with error_type '{error_type}'. "
            f"Initiating resilient fallback to working default models."
        )

        for fb_model in fallback_candidates:
            if fb_model == original_model_id:
                continue

            attempts += 1
            try:
                fb_result = engine.run_engine(
                    provider="Gemini",
                    model_id=fb_model,
                    user_text=request.message,
                    conversation_history=history,
                    image_bytes=None,
                    mime_type=None,
                    previous_visual_context=request.previous_visual_context,
                )
                if fb_result and fb_result.get("status") != "error":
                    result = fb_result
                    provider = "Gemini"
                    model_id = fb_model
                    fallback_used = True
                    break
            except Exception as fb_exc:
                logger.warning(f"Fallback candidate {fb_model} failed: {fb_exc}")
                continue

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CircuitSnap could not process this request after all fallback attempts.",
        )

    final_fallback_used = result.get("fallback_used", False) or fallback_used
    final_attempts = result.get("attempts", attempts)
    if fallback_used:
        final_attempts = max(final_attempts, attempts)

    return ChatResponse(
        answer=result.get("answer") or "",
        provider=result.get("provider") or provider,
        model_id=result.get("model_id") or model_id,
        status=result.get("status", "error"),
        error_type=result.get("error_type"),
        fallback_used=final_fallback_used,
        attempts=final_attempts,
        original_model=original_model_id if final_fallback_used else None,
    )