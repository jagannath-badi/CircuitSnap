"""
CircuitSnap — Backend Engine Integration Layer.
Seamless bridge to J.A.R.V.I.S. Local Intelligence Engine.
"""

from typing import Any, Optional
from backend.jarvis_engine.orchestrator import process_jarvis_query


def run_engine_resilient(
    *,
    provider: str = "J.A.R.V.I.S. Core",
    model_id: str = "jarvis-auto",
    user_text: str = "",
    conversation_history: Optional[list[dict[str, Any]]] = None,
    image_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
    previous_visual_context: Optional[dict[str, Any]] = None,
    fallback_candidates: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Executes offline J.A.R.V.I.S. query with sub-50ms deterministic response."""
    return process_jarvis_query(
        user_text=user_text,
        image_bytes=image_bytes,
        conversation_history=conversation_history,
        model_id=model_id,
    )


# Re-export process_jarvis_query as run_engine for backward-compatibility
run_engine = run_engine_resilient
