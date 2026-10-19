"""
CircuitSnap — Backend Engine Integration Layer.

Re-exports core engine functions and provides resilient multi-model execution.
"""

from typing import Any, Optional

import engine as _root_engine
from engine import (
    INPUT_TYPES,
    INTENTS,
    WORKFLOWS,
    RequestContext,
    build_context,
    build_engine_prompt,
    build_evidence_rules,
    detect_intent,
    determine_detail_level,
    infer_input_type_hint,
    prepare_request,
    run_engine,
    select_request_image_context,
    select_workflow,
)

__all__ = [
    "INPUT_TYPES",
    "INTENTS",
    "WORKFLOWS",
    "RequestContext",
    "build_context",
    "build_engine_prompt",
    "build_evidence_rules",
    "detect_intent",
    "determine_detail_level",
    "infer_input_type_hint",
    "prepare_request",
    "run_engine",
    "run_engine_resilient",
    "select_request_image_context",
    "select_workflow",
]


def run_engine_resilient(
    *,
    provider: str,
    model_id: str,
    user_text: str,
    conversation_history: Optional[list[dict[str, Any]]] = None,
    image_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
    previous_visual_context: Optional[dict[str, Any]] = None,
    fallback_candidates: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Executes CircuitSnap engine with automatic multi-model failover.

    If the requested model fails (due to invalid model name, 404, rate limits, or unavailability),
    this function attempts the provided fallback candidates in sequence.
    """
    if fallback_candidates is None:
        fallback_candidates = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-2.5-flash"]

    original_model = model_id
    original_provider = provider
    attempts = 1
    fallback_used = False

    # First attempt
    try:
        result = _root_engine.run_engine(
            provider=provider,
            model_id=model_id,
            user_text=user_text,
            conversation_history=conversation_history,
            image_bytes=image_bytes,
            mime_type=mime_type,
            previous_visual_context=previous_visual_context,
        )
    except Exception:
        result = None

    # Check for failure (either exception or status == "error")
    if not result or result.get("status") == "error":
        for fb_model in fallback_candidates:
            if fb_model == original_model:
                continue

            attempts += 1
            try:
                fb_result = _root_engine.run_engine(
                    provider="Gemini",
                    model_id=fb_model,
                    user_text=user_text,
                    conversation_history=conversation_history,
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                    previous_visual_context=previous_visual_context,
                )
                if fb_result and fb_result.get("status") != "error":
                    result = fb_result
                    provider = "Gemini"
                    model_id = fb_model
                    fallback_used = True
                    break
            except Exception:
                continue

    if not result:
        # Ultimate fallback structure if all candidates failed
        return {
            "answer": "CircuitSnap could not complete the request. All fallback models were exhausted.",
            "provider": provider,
            "model_id": model_id,
            "status": "error",
            "error_type": "fallback_exhausted",
            "fallback_used": fallback_used,
            "attempts": attempts,
            "original_model": original_model,
        }

    if fallback_used:
        result["fallback_used"] = True
        result["attempts"] = attempts
        result["original_model"] = original_model
        result["model_id"] = model_id
        result["provider"] = provider

    return result

