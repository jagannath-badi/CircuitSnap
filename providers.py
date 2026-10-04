"""
CircuitSnap — AI Provider Layer

Handles communication with the AI providers used by CircuitSnap.

The provider layer is intentionally independent from the UI.
CircuitSnap owns the conversation history and passes it here,
allowing the user to switch providers without losing context.
"""

import base64
import re

import streamlit as st
from google import genai
from google.genai import types
from groq import Groq

from models import get_model
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

def _exception_chain(error):
    """Yield an exception and its wrapped causes without looping."""

    seen = set()
    current = error

    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def _status_code(error):
    """Read an HTTP status from common SDK exception attributes."""

    candidates = (
        error,
        getattr(error, "response", None),
    )

    for candidate in candidates:
        if candidate is None:
            continue

        for attribute in ("status_code", "status", "code"):
            value = getattr(candidate, attribute, None)

            if hasattr(value, "value"):
                value = value.value

            if isinstance(value, int) and not isinstance(value, bool):
                return value

            match = re.search(r"\b\d{3}\b", str(value or ""))

            if match:
                return int(match.group(0))

    return None


def _classify_provider_error(error):
    """
    Classify known provider failures.

    Unknown exceptions are intentionally left unclassified so callers
    can surface programming errors instead of masking them as API errors.
    """

    for current_error in _exception_chain(error):
        status = _status_code(current_error)

        if status == 408 or 500 <= (status or 0) <= 599:
            return "temporary_unavailability"

        error_text = re.sub(r"[_-]+", " ", str(current_error).lower())
        error_name = type(current_error).__name__.lower()
        error_module = type(current_error).__module__.lower()
        provider_exception = (
            error_module.startswith(
                ("google.genai", "groq", "openai", "httpx", "httpcore", "requests", "urllib3")
            )
            or any(
                term in error_name
                for term in (
                    "apierror",
                    "apiresponse",
                    "clienterror",
                    "servererror",
                    "serviceunavailable",
                    "badrequest",
                    "invalidargument",
                    "notfound",
                    "ratelimit",
                    "authentication",
                    "permissiondenied",
                )
            )
        )

        missing_secret = (
            isinstance(current_error, KeyError)
            and str(current_error).strip("'\" ").upper()
            in {"GEMINI_API_KEY", "GROQ_API_KEY"}
        )
        secret_lookup_failure = (
            "secret" in error_name
            and any(term in error_name for term in ("missing", "notfound"))
        )

        if (
            missing_secret
            or secret_lookup_failure
            or status in {401, 403}
            or any(
                term in error_text
                for term in (
                    "api key",
                    "api_key",
                    "api-key",
                    "invalid key",
                    "authentication",
                    "unauthenticated",
                    "unauthorized",
                    "permission denied",
                    "forbidden",
                    "401",
                    "403",
                )
            )
            or any(
                term in error_name
                for term in (
                    "authentication",
                    "permissiondenied",
                    "forbidden",
                )
            )
        ):
            return "authentication_configuration"

        if (
            any(
                term in error_text
                for term in (
                    "model not found",
                    "model does not exist",
                    "unknown model",
                    "invalid model",
                    "unsupported model",
                    "model not supported",
                    "model unavailable",
                    "no such model",
                )
            )
            or (provider_exception and "not found" in error_text)
            or "notfound" in error_name
            or status == 404
        ):
            return "invalid_model"

        if (
            any(
                term in error_text
                for term in (
                    "invalid request",
                    "bad request",
                    "invalid argument",
                    "unsupported parameter",
                )
            )
            or any(
                term in error_name
                for term in ("badrequest", "invalidargument")
            )
            or status in {400, 422}
        ):
            return "invalid_request"

        if status == 429 or any(
            term in error_text
            for term in (
                "quota",
                "rate limit",
                "resource exhausted",
                "too many requests",
                "429",
            )
        ) or "ratelimit" in error_name:
            return "rate_limited"

        if (
            isinstance(current_error, (TimeoutError, ConnectionError))
            or any(
                term in error_name
                for term in (
                    "timeout",
                    "connectionerror",
                    "connecterror",
                    "connecttimeout",
                    "readtimeout",
                    "apiconnection",
                    "serviceunavailable",
                    "internalserver",
                    "badgateway",
                    "gatewaytimeout",
                    "servererror",
                )
            )
            or (
                provider_exception
                and (
                    any(
                        term in error_text
                        for term in (
                            "timed out",
                            "timeout",
                            "deadline exceeded",
                            "service unavailable",
                            "temporarily unavailable",
                            "internal server error",
                            "bad gateway",
                            "gateway timeout",
                            "connection reset",
                            "connection refused",
                            "connection error",
                            "connection aborted",
                            "remote disconnected",
                            "network is unreachable",
                            "network error",
                            "temporary failure",
                        )
                    )
                    or re.search(r"\b5\d{2}\b", error_text)
                )
            )
        ):
            return "temporary_unavailability"

        if status is not None and 400 <= status < 500:
            return "invalid_request"

    return None


def _is_transient_error(error):
    """Return whether a known provider failure is safe to retry/fallback."""

    return _classify_provider_error(error) == "temporary_unavailability"


def _format_provider_error(
    provider,
    error=None,
    *,
    error_type=None,
    model_id=None,
):
    """Format categorized provider failures without exposing raw errors."""

    error_type = error_type or (
        _classify_provider_error(error)
        if error is not None
        else None
    )

    if error_type == "authentication_configuration":
        return (
            f"🔐 {provider} authentication or configuration failed. "
            "Check the configured API key and model access."
        )

    if error_type == "invalid_model":
        model_label = f" ({model_id})" if model_id else ""
        return (
            f"⚠️ The {provider} model{model_label} is invalid or unavailable. "
            "Check the model configuration and access."
        )

    if error_type == "invalid_request":
        return (
            f"⚠️ {provider} rejected this request. "
            "Check the request format and the selected model's supported inputs."
        )

    if error_type == "rate_limited":
        return (
            f"⚠️ {provider} is rate-limited or its quota is exhausted. "
            "Please try again later or switch providers."
        )

    if error_type == "temporary_unavailability":
        return (
            f"⏳ {provider} is temporarily unavailable. "
            "Please try again shortly."
        )

    if error_type == "fallback_exhausted":
        return (
            "⏳ Gemini and its configured fallback providers remained "
            "temporarily unavailable after all attempts. Please try again later."
        )

    if error_type == "unsupported_provider":
        return f"⚠️ Unsupported provider configuration: {provider}."

    return f"⚠️ {provider} could not complete the request."


def _provider_result(
    answer,
    provider,
    model_id,
    *,
    status="success",
    error_type=None,
    fallback_used=False,
    attempts=1,
):
    return {
        "answer": answer,
        "provider": provider,
        "model_id": model_id,
        "status": status,
        "error_type": error_type,
        "fallback_used": fallback_used,
        "attempts": attempts,
    }


def _attempt_provider(call):
    """Run a provider call, re-raising failures outside known API classes."""

    try:
        return True, call(), None, None
    except Exception as error:
        error_type = _classify_provider_error(error)

        if error_type is None:
            raise

        return False, None, error, error_type


def ask_provider(
    provider,
    model_id,
    prompt,
    history=None,
    image_bytes=None,
    mime_type=None,
    return_metadata=False,
):
    """
    Send a request to the selected provider.

    By default this returns the answer string for compatibility. Set
    return_metadata=True to also receive the provider/model that responded.
    """

    def deliver(result):
        return result if return_metadata else result["answer"]

    def failure(
        failed_provider,
        failed_model,
        error,
        error_type,
        *,
        fallback_used,
        attempts,
    ):
        return deliver(
            _provider_result(
                _format_provider_error(
                    failed_provider,
                    error,
                    error_type=error_type,
                    model_id=failed_model,
                ),
                failed_provider,
                failed_model,
                status="error",
                error_type=error_type,
                fallback_used=fallback_used,
                attempts=attempts,
            )
        )

    def success(
        answer,
        successful_provider,
        successful_model,
        *,
        fallback_used,
        attempts,
    ):
        return deliver(
            _provider_result(
                answer,
                successful_provider,
                successful_model,
                fallback_used=fallback_used,
                attempts=attempts,
            )
        )

    # ========================================================
    # GEMINI
    # ========================================================

    if provider == "Gemini":
        gemini_config = get_model("Gemini")
        attempts = 1
        fallback_used = False

        success_flag, answer, error, error_type = _attempt_provider(
            lambda: ask_gemini(
                model_id=model_id,
                prompt=prompt,
                history=history,
                image_bytes=image_bytes,
                mime_type=mime_type,
            )
        )

        if success_flag:
            return success(
                answer, "Gemini", model_id,
                fallback_used=fallback_used, attempts=attempts,
            )

        if error_type != "temporary_unavailability":
            return failure(
                "Gemini", model_id, error, error_type,
                fallback_used=fallback_used, attempts=attempts,
            )

        # Retry the selected Gemini model once after a transient failure.
        attempts += 1
        success_flag, answer, error, error_type = _attempt_provider(
            lambda: ask_gemini(
                model_id=model_id,
                prompt=prompt,
                history=history,
                image_bytes=image_bytes,
                mime_type=mime_type,
            )
        )

        if success_flag:
            return success(
                answer, "Gemini", model_id,
                fallback_used=fallback_used, attempts=attempts,
            )

        if error_type != "temporary_unavailability":
            return failure(
                "Gemini", model_id, error, error_type,
                fallback_used=fallback_used, attempts=attempts,
            )

        # The registry keeps these models internal to provider fallback.
        for fallback_model in gemini_config.get("fallback_models", []):
            fallback_used = True
            attempts += 1
            success_flag, answer, error, error_type = _attempt_provider(
                lambda fallback_model=fallback_model: ask_gemini(
                    model_id=fallback_model,
                    prompt=prompt,
                    history=history,
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                )
            )

            if success_flag:
                return success(
                    answer, "Gemini", fallback_model,
                    fallback_used=fallback_used, attempts=attempts,
                )

            if error_type != "temporary_unavailability":
                return failure(
                    "Gemini", fallback_model, error, error_type,
                    fallback_used=fallback_used, attempts=attempts,
                )

        fallback_provider = gemini_config.get("fallback_provider")

        if not fallback_provider:
            return deliver(
                _provider_result(
                    _format_provider_error(
                        "Gemini", error_type="fallback_exhausted"
                    ),
                    "Gemini",
                    model_id,
                    status="error",
                    error_type="fallback_exhausted",
                    fallback_used=fallback_used,
                    attempts=attempts,
                )
            )

        fallback_config = get_model(fallback_provider)
        fallback_model = fallback_config["model_id"]
        fallback_used = True
        attempts += 1

        fallback_call = {
            "Groq": ask_groq,
            "Gemini": ask_gemini,
        }.get(fallback_provider)

        if fallback_call is None:
            raise ValueError(
                f"Unsupported fallback provider configured: {fallback_provider}"
            )

        success_flag, answer, error, error_type = _attempt_provider(
            lambda: fallback_call(
                model_id=fallback_model,
                prompt=prompt,
                history=history,
                image_bytes=image_bytes,
                mime_type=mime_type,
            )
        )

        if success_flag:
            return success(
                answer, fallback_provider, fallback_model,
                fallback_used=fallback_used, attempts=attempts,
            )

        if error_type != "temporary_unavailability":
            return failure(
                fallback_provider, fallback_model, error, error_type,
                fallback_used=fallback_used, attempts=attempts,
            )

        return deliver(
            _provider_result(
                _format_provider_error(
                    fallback_provider,
                    error,
                    error_type="fallback_exhausted",
                    model_id=fallback_model,
                ),
                fallback_provider,
                fallback_model,
                status="error",
                error_type="fallback_exhausted",
                fallback_used=fallback_used,
                attempts=attempts,
            )
        )

    # ========================================================
    # GROQ
    # ========================================================

    if provider == "Groq":
        success_flag, answer, error, error_type = _attempt_provider(
            lambda: ask_groq(
                model_id=model_id,
                prompt=prompt,
                history=history,
                image_bytes=image_bytes,
                mime_type=mime_type,
            )
        )

        if success_flag:
            return success(
                answer, "Groq", model_id,
                fallback_used=False, attempts=1,
            )

        return failure(
            "Groq", model_id, error, error_type,
            fallback_used=False, attempts=1,
        )

    return deliver(
        _provider_result(
            _format_provider_error(
                provider,
                error_type="unsupported_provider",
            ),
            provider,
            model_id,
            status="error",
            error_type="unsupported_provider",
            fallback_used=False,
            attempts=0,
        )
    )
