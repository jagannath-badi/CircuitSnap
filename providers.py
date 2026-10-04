"""
CircuitSnap — AI Provider Layer

Handles communication with the AI providers used by CircuitSnap.

The provider layer is intentionally independent from the UI.
CircuitSnap owns the conversation history and passes it here,
allowing the user to switch providers without losing context.
"""

import base64

import streamlit as st
from google import genai
from google.genai import types
from groq import Groq

from prompts import SYSTEM_PROMPT


# ============================================================
# CLIENTS
# ============================================================

@st.cache_resource
def get_gemini_client():
    """Create and cache the Gemini client."""

    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )


@st.cache_resource
def get_groq_client():
    """Create and cache the Groq client."""

    return Groq(
        api_key=st.secrets["GROQ_API_KEY"]
    )


# ============================================================
# IMAGE HELPERS
# ============================================================

def image_to_data_url(image_bytes, mime_type):
    """
    Convert image bytes to a base64 data URL.

    Groq accepts images through data URLs.
    """

    encoded = base64.b64encode(image_bytes).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


# ============================================================
# HISTORY HELPERS
# ============================================================

def _build_history_text(history):
    """
    Convert CircuitSnap conversation history into a compact
    text transcript.

    This is used by providers where a text representation of
    previous conversation context is sufficient.
    """

    if not history:
        return ""

    lines = []

    for message in history:
        role = message.get("role", "user")
        content = message.get("content", "")

        if not content:
            continue

        if role == "assistant":
            label = "CircuitSnap"
        else:
            label = "User"

        lines.append(f"{label}: {content}")

    return "\n\n".join(lines)


# ============================================================
# GEMINI
# ============================================================

def ask_gemini(
    model_id,
    prompt,
    history=None,
    image_bytes=None,
    mime_type=None,
):
    """
    Send a request to Gemini.

    Conversation history is supplied by CircuitSnap rather than
    relying on a provider-specific chat session.
    """

    client = get_gemini_client()

    contents = []

    # --------------------------------------------------------
    # Previous conversation
    # --------------------------------------------------------

    if history:
        for message in history:
            role = message.get("role", "user")
            content = message.get("content", "")

            if not content:
                continue

            sdk_role = "model" if role == "assistant" else "user"

            contents.append(
                types.Content(
                    role=sdk_role,
                    parts=[
                        types.Part.from_text(
                            text=content
                        )
                    ],
                )
            )

    # --------------------------------------------------------
    # Current user message
    # --------------------------------------------------------

    current_parts = []

    if image_bytes is not None:
        current_parts.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type,
            )
        )

    current_parts.append(
        types.Part.from_text(
            text=prompt
        )
    )

    contents.append(
        types.Content(
            role="user",
            parts=current_parts,
        )
    )

    # --------------------------------------------------------
    # Request
    # --------------------------------------------------------

    response = client.models.generate_content(
        model=model_id,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=1200,
        ),
    )

    return response.text


# ============================================================
# GROQ
# ============================================================

def ask_groq(
    model_id,
    prompt,
    history=None,
    image_bytes=None,
    mime_type=None,
):
    """
    Send a request to Groq.

    Previous CircuitSnap conversation history is supplied as
    normal chat messages.
    """

    client = get_groq_client()

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    # --------------------------------------------------------
    # Previous conversation
    # --------------------------------------------------------

    if history:
        for message in history:
            role = message.get("role", "user")
            content = message.get("content", "")

            if not content:
                continue

            if role not in {"user", "assistant"}:
                continue

            messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )

    # --------------------------------------------------------
    # Current user message
    # --------------------------------------------------------

    current_content = [
        {
            "type": "text",
            "text": prompt,
        }
    ]

    if image_bytes is not None:
        current_content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": image_to_data_url(
                        image_bytes,
                        mime_type,
                    )
                },
            }
        )

    messages.append(
        {
            "role": "user",
            "content": current_content,
        }
    )

    # --------------------------------------------------------
    # Request
    # --------------------------------------------------------

    response = client.chat.completions.create(
        model=model_id,
        messages=messages,
        max_completion_tokens=1200,
    )

    return response.choices[0].message.content


# ============================================================
# PROVIDER DISPATCHER
# ============================================================

def _is_transient_error(error):
    """
    Return True when the provider failure is temporary
    and another attempt may succeed.
    """

    error_text = str(error).lower()

    transient_terms = (
        "503",
        "502",
        "500",
        "service unavailable",
        "temporarily unavailable",
        "high demand",
        "timeout",
        "timed out",
        "connection reset",
        "connection error",
    )

    return any(term in error_text for term in transient_terms)


def ask_provider(
    provider,
    model_id,
    prompt,
    history=None,
    image_bytes=None,
    mime_type=None,
):
    """
    Send a request to the selected provider.

    Reliability strategy:

    Gemini 3.8
        ↓ temporary failure
    Retry once
        ↓ still failing
    Gemini 3.7
        ↓ still failing
    Groq
    """

    # ========================================================
    # GEMINI
    # ========================================================

    if provider == "Gemini":

        # ----------------------------------------------------
        # Primary Gemini model
        # ----------------------------------------------------

        try:
            return ask_gemini(
                model_id=model_id,
                prompt=prompt,
                history=history,
                image_bytes=image_bytes,
                mime_type=mime_type,
            )

        except Exception as primary_error:

            print(
                f"\n[CircuitSnap] Gemini primary error:"
                f"\nType: {type(primary_error).__name__}"
                f"\nMessage: {primary_error}\n"
            )

            # ------------------------------------------------
            # Only fallback for temporary failures
            # ------------------------------------------------

            if not _is_transient_error(primary_error):
                return _format_provider_error(
                    provider="Gemini",
                    error=primary_error,
                )

            # ------------------------------------------------
            # Retry primary model once
            # ------------------------------------------------

            try:
                print(
                    "[CircuitSnap] Retrying Gemini primary model..."
                )

                return ask_gemini(
                    model_id=model_id,
                    prompt=prompt,
                    history=history,
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                )

            except Exception as retry_error:

                print(
                    f"\n[CircuitSnap] Gemini retry failed:"
                    f"\nType: {type(retry_error).__name__}"
                    f"\nMessage: {retry_error}\n"
                )

            # ------------------------------------------------
            # Gemini fallback model
            # ------------------------------------------------

            fallback_model = "gemini-3.7-flash"

            try:
                print(
                    f"[CircuitSnap] Trying Gemini fallback: "
                    f"{fallback_model}"
                )

                return ask_gemini(
                    model_id=fallback_model,
                    prompt=prompt,
                    history=history,
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                )

            except Exception as fallback_error:

                print(
                    f"\n[CircuitSnap] Gemini fallback failed:"
                    f"\nType: {type(fallback_error).__name__}"
                    f"\nMessage: {fallback_error}\n"
                )

            # ------------------------------------------------
            # Final fallback → Groq
            # ------------------------------------------------

            try:
                print(
                    "[CircuitSnap] Falling back to Groq..."
                )

                return ask_groq(
                    model_id="qwen/qwen3.8-27b",
                    prompt=prompt,
                    history=history,
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                )

            except Exception as groq_error:

                print(
                    f"\n[CircuitSnap] Groq fallback failed:"
                    f"\nType: {type(groq_error).__name__}"
                    f"\nMessage: {groq_error}\n"
                )

                return _format_provider_error(
                    provider="Gemini",
                    error=primary_error,
                )

    # ========================================================
    # GROQ
    # ========================================================

    if provider == "Groq":

        try:
            return ask_groq(
                model_id=model_id,
                prompt=prompt,
                history=history,
                image_bytes=image_bytes,
                mime_type=mime_type,
            )

        except Exception as exc:

            print(
                f"\n[CircuitSnap] Groq error:"
                f"\nType: {type(exc).__name__}"
                f"\nMessage: {exc}\n"
            )

            return _format_provider_error(
                provider="Groq",
                error=exc,
            )

    # ========================================================
    # UNKNOWN PROVIDER
    # ========================================================

    return (
        f"⚠️ Unsupported provider: {provider}"
    )


# ============================================================
# ERROR HANDLING
# ============================================================

def _format_provider_error(provider, error):
    """
    Convert provider/API failures into a useful user-facing
    message without exposing unnecessary implementation details.
    """

    error_text = str(error).lower()

    # --------------------------------------------------------
    # Authentication / API key
    # --------------------------------------------------------

    if (
        "api key" in error_text
        or "authentication" in error_text
        or "unauthenticated" in error_text
        or "401" in error_text
    ):
        return (
            f"🔐 {provider} authentication failed. "
            "Please check the configured API key."
        )

    # --------------------------------------------------------
    # Quota / rate limiting
    # --------------------------------------------------------

    if (
        "quota" in error_text
        or "rate limit" in error_text
        or "resource exhausted" in error_text
        or "429" in error_text
    ):
        return (
            f"⚠️ {provider} is temporarily rate-limited. "
            "Please try again in a moment or switch to another model."
        )

    # --------------------------------------------------------
    # Temporary server / availability problems
    # --------------------------------------------------------

    if (
        "503" in error_text
        or "502" in error_text
        or "500" in error_text
        or "service unavailable" in error_text
        or "temporarily unavailable" in error_text
        or "high demand" in error_text
        or "timeout" in error_text
        or "timed out" in error_text
    ):
        return (
            f"⏳ {provider} is temporarily unavailable. "
            "Please try again in a moment."
        )

    # --------------------------------------------------------
    # Permission / access
    # --------------------------------------------------------

    if (
        "permission denied" in error_text
        or "forbidden" in error_text
        or "403" in error_text
    ):
        return (
            f"🔒 {provider} denied access to the selected model. "
            "Check that the API key or project has access to this model."
        )

    # --------------------------------------------------------
    # Model genuinely not found
    # --------------------------------------------------------

    if (
        "model not found" in error_text
        or "not found" in error_text
        or "404" in error_text
    ):
        return (
            f"⚠️ The selected {provider} model could not be found. "
            "Please verify the model configuration."
        )

    # --------------------------------------------------------
    # Generic provider failure
    # --------------------------------------------------------

    return (
        f"⚠️ CircuitSnap couldn't get a response from {provider}. "
        "Please try again."
    )