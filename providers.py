"""
CircuitSnap — AI Provider Layer

Handles communication with the AI providers used by CircuitSnap.

The provider layer is intentionally independent from the UI.
CircuitSnap owns the conversation history and passes it here,
allowing the user to switch providers without losing context.
"""

import base64
import http.client
import json
import logging
import os
import re
import time
import urllib.parse
from pathlib import Path
from typing import Optional

# from google import genai
# from google.genai import types

from models import get_model
from prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def load_dotenv(dotenv_path: str | Path | None = None, override: bool = True) -> None:
    """
    Safely reads environment variables from .env.
    """
    from dotenv import load_dotenv as _lib_load_dotenv

    # Target project root explicitly
    root_env = Path(__file__).resolve().parent / ".env"

    if root_env.is_file():
        _lib_load_dotenv(dotenv_path=str(root_env), override=override)
    elif dotenv_path and Path(dotenv_path).is_file():
        _lib_load_dotenv(dotenv_path=str(dotenv_path), override=override)
    else:
        # Fallback to current working directory
        _lib_load_dotenv(dotenv_path=".env", override=override)


# Auto-load .env immediately at startup
load_dotenv(override=True)

# ============================================================
# OPENJARVIS HYBRID LOCAL / CLOUD CONFIGURATION
# ============================================================

OPENJARVIS_BASE_URL = os.getenv("OPENJARVIS_BASE_URL", "http://localhost:8000/v1").rstrip("/")
OPENJARVIS_MODEL = os.getenv("OPENJARVIS_MODEL", "qwen3:8b")
PROVIDER_MODE = os.getenv("PROVIDER_MODE", "auto").lower().strip()

_OPENJARVIS_CACHE = {"status": None, "timestamp": 0.0}


def is_openjarvis_available(force_refresh: bool = False) -> bool:
    """
    Fast 0.35s HTTP GET probe to {OPENJARVIS_BASE_URL}/models.
    Cached for 15 seconds so per-request routing latency is 0ms.
    Uses direct http.client to bypass Windows proxy lookup latency.
    """
    now = time.time()
    if not force_refresh and _OPENJARVIS_CACHE["status"] is not None:
        if (now - _OPENJARVIS_CACHE["timestamp"]) < 15.0:
            return bool(_OPENJARVIS_CACHE["status"])

    base_url = os.getenv("OPENJARVIS_BASE_URL", OPENJARVIS_BASE_URL).rstrip("/")
    parsed = urllib.parse.urlparse(base_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = (parsed.path or "").rstrip("/") + "/models"

    available = False
    conn = None
    try:
        if parsed.scheme == "https":
            conn = http.client.HTTPSConnection(host, port, timeout=0.35)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=0.35)
        conn.request("GET", path, headers={"User-Agent": "CircuitSnap-Probe"})
        resp = conn.getresponse()
        available = (200 <= resp.status < 300)
    except Exception:
        available = False
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    _OPENJARVIS_CACHE["status"] = available
    _OPENJARVIS_CACHE["timestamp"] = now
    return available


def ask_openjarvis(
    prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.55,
    model: str | None = None,
    history: list[dict] | None = None,
    timeout: float = 30.0,
) -> tuple[str, str]:
    """
    Calls {OPENJARVIS_BASE_URL}/chat/completions using OpenAI-compatible JSON payload.
    Returns (response_text, f"OpenJarvis ({model})").
    """
    base_url = os.getenv("OPENJARVIS_BASE_URL", OPENJARVIS_BASE_URL).rstrip("/")
    target_model = model or os.getenv("OPENJARVIS_MODEL", OPENJARVIS_MODEL)

    messages = []
    sys_content = system_prompt or SYSTEM_PROMPT
    if sys_content:
        messages.append({"role": "system", "content": sys_content})

    if history:
        for message in history:
            role = message.get("role", "user")
            content = message.get("content", "")
            if content and role in {"user", "assistant"}:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": target_model,
        "messages": messages,
        "temperature": temperature,
    }

    req_data = json.dumps(payload).encode("utf-8")
    parsed = urllib.parse.urlparse(base_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = (parsed.path or "").rstrip("/") + "/chat/completions"

    conn = None
    try:
        if parsed.scheme == "https":
            conn = http.client.HTTPSConnection(host, port, timeout=timeout)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=timeout)
        conn.request(
            "POST",
            path,
            body=req_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "CircuitSnap-OpenJarvis-Client",
            },
        )
        resp = conn.getresponse()
        resp_data = resp.read().decode("utf-8")
        if not (200 <= resp.status < 300):
            raise RuntimeError(f"OpenJarvis HTTP error ({resp.status}): {resp.reason}")
        body = json.loads(resp_data)
        choices = body.get("choices", [])
        if choices and "message" in choices[0]:
            content = choices[0]["message"].get("content", "")
            return content, f"OpenJarvis ({target_model})"
        return "", f"OpenJarvis ({target_model})"
    except Exception as err:
        if "HTTP error" in str(err):
            raise
        raise ConnectionError(f"OpenJarvis connection failed: {err}") from err
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def ask_groq(
    prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.55,
    model: str | None = None,
    history: list[dict] | None = None,
    timeout: float = 20.0,
) -> tuple[str, str]:
    """
    Calls Groq OpenAI-compatible endpoint.
    Returns (response_text, f"Groq ({model})").
    """
    import urllib.request

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise KeyError("GROQ_API_KEY")

    target_model = model or "llama-3.3-70b-versatile"

    messages = []
    sys_content = system_prompt or SYSTEM_PROMPT
    if sys_content:
        messages.append({"role": "system", "content": sys_content})

    if history:
        for message in history:
            role = message.get("role", "user")
            content = message.get("content", "")
            if content and role in {"user", "assistant"}:
                messages.append({"role": role, "content": redact_secrets(str(content))})

    messages.append({"role": "user", "content": redact_secrets(prompt)})

    payload = {
        "model": target_model,
        "messages": messages,
        "temperature": temperature,
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=req_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "CircuitSnap-Groq-Client",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp_data = resp.read().decode("utf-8")
            body = json.loads(resp_data)
            choices = body.get("choices", [])
            if choices and "message" in choices[0]:
                content = choices[0]["message"].get("content", "")
                return content, f"Groq ({target_model})"
            return "", f"Groq ({target_model})"
    except urllib.error.HTTPError as err:
        raise RuntimeError(f"Groq HTTP error ({err.code}): {err.read().decode('utf-8')}") from err
    except Exception as err:
        raise ConnectionError(f"Groq connection failed: {err}") from err


# ============================================================
# CLIENTS
# ============================================================

_CLIENT_CACHE = {}


def _get_api_key(name: str) -> Optional[str]:
    """Retrieve API key from os.environ with aliasing and whitespace trimming."""
    val = os.environ.get(name)
    if not val and name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        val = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    return val.strip() if val else None


def get_gemini_client():
    """Create and cache the Gemini client with a hard 25s HTTP timeout."""
    from google import genai
    from google.genai import types

    api_key = _get_api_key("GEMINI_API_KEY")
    if not api_key:
        raise KeyError("GEMINI_API_KEY")

    if "gemini" not in _CLIENT_CACHE or _CLIENT_CACHE.get("gemini_key") != api_key:
        _CLIENT_CACHE["gemini"] = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=25000),
        )
        _CLIENT_CACHE["gemini_key"] = api_key

    return _CLIENT_CACHE["gemini"]


# ============================================================
# IMAGE HELPERS
# ============================================================

def image_to_data_url(image_bytes, mime_type):
    """
    Convert image bytes to a base64 data URL.
    """

    encoded = base64.b64encode(image_bytes).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"



# ============================================================
# GEMINI
# ============================================================

def ask_gemini(
    model_id,
    prompt,
    history=None,
    image_bytes=None,
    mime_type=None,
    temperature: float = 0.55,
):
    """
    Send a request to Gemini with a clean, fast config (no tools, no thinking).
    Conversation history is supplied by CircuitSnap rather than
    relying on a provider-specific chat session.
    Returns the answer text.
    """
    from google import genai
    from google.genai import types

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
    # Request - clean config, no tools/thinking
    # --------------------------------------------------------

    response = client.models.generate_content(
        model=model_id,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=temperature,
            max_output_tokens=4096,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )

    answer_text = getattr(response, "text", "") or ""

    return answer_text


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
                ("google.genai", "openai", "httpx", "httpcore", "requests", "urllib3")
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

        # Rate limiting / quota exhaustion takes precedence over
        # authentication hints: a 429 with "billing" or "plan" in the
        # message is a quota failure, not a credential problem.
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

        missing_secret = (
            isinstance(current_error, KeyError)
            and str(current_error).strip("'\" ").upper()
            in {"GEMINI_API_KEY", "GOOGLE_API_KEY"}
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


def _is_fallback_eligible(error_type):
    """Return whether a known provider failure is safe to retry/fallback."""

    return error_type in {"temporary_unavailability", "rate_limited", "invalid_model"}


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


def redact_secrets(text: str) -> str:
    """
    Sanitizes sensitive credentials, private API keys, bearer tokens,
    passwords, and personal emails before cloud transmission.
    """
    if not text:
        return ""
    t = text
    t = re.sub(r"\bAIza[0-9A-Za-z-_]{30,40}\b", "[REDACTED_API_KEY]", t)
    t = re.sub(r"\bgsk_[0-9A-Za-z]{30,}\b", "[REDACTED_API_KEY]", t)
    t = re.sub(r"\bsk-[0-9A-Za-z-_]{20,}\b", "[REDACTED_API_KEY]", t)
    t = re.sub(r"\bBearer\s+[A-Za-z0-9_\-\.]{20,}\b", "Bearer [REDACTED_TOKEN]", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(password|secret|passwd|pass|token|apikey)\s*[:=]\s*([^\s,;]+)", r"\1: [REDACTED]", t, flags=re.IGNORECASE)
    t = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED_EMAIL]", t)
    return t


def ask_provider(
    provider,
    model_id,
    prompt,
    history=None,
    image_bytes=None,
    mime_type=None,
    return_metadata=False,
    temperature: float = 0.55,
    privacy_mode: str = "guarded",
):
    """
    Send a request to the selected provider with privacy guard enforcement.

    - "strict": Answer exclusively from offline J.A.R.V.I.S. Core without external cloud APIs.
    - "guarded": Pre-flight credential & PII redaction before external API calls.
    - "relaxed": Standard external cloud routing.
    """

    def deliver(result):
        return result if return_metadata else result["answer"]

    def failure(
        failed_provider,
        failed_model,
        error,
        error_type,
    ):
        # Raise instead of returning error text so callers can handle it
        raise RuntimeError(f"{failed_provider} ({failed_model}) failed: {error_type} - {error}")

    active_mode = os.getenv("PROVIDER_MODE", PROVIDER_MODE).lower().strip()
    oj_model = os.getenv("OPENJARVIS_MODEL", OPENJARVIS_MODEL)
    local_fallback_triggered = False

    # --------------------------------------------------------
    # STRICT PRIVACY / LOCAL MODE ROUTING (Zero Cloud APIs)
    # --------------------------------------------------------
    if privacy_mode == "strict" or active_mode == "local" or provider in {"OpenJarvis", "openjarvis"}:
        target_oj_model = model_id if provider in {"OpenJarvis", "openjarvis"} and model_id else oj_model
        if is_openjarvis_available():
            success_flag, answer_tuple, error, error_type = _attempt_provider(
                lambda: ask_openjarvis(
                    prompt=prompt,
                    system_prompt=SYSTEM_PROMPT,
                    temperature=temperature,
                    model=target_oj_model,
                    history=history,
                )
            )
            if success_flag and answer_tuple:
                text, provider_label = answer_tuple
                return deliver(
                    _provider_result(
                        text,
                        provider_label,
                        target_oj_model,
                        status="success",
                        fallback_used=False,
                        attempts=1,
                    )
                )

        # If strict privacy or local mode, fall back to offline J.A.R.V.I.S. Core (never call cloud APIs)
        if privacy_mode == "strict" or active_mode == "local":
            try:
                from backend.jarvis_engine.orchestrator import process_jarvis_query
                local_res = process_jarvis_query(
                    user_text=prompt,
                    image_bytes=image_bytes,
                    conversation_history=history,
                    model_id="jarvis-auto",
                )
                return deliver(
                    _provider_result(
                        local_res.get("answer", "Processed locally with zero external API transmission."),
                        "J.A.R.V.I.S. Core (Strict Local)",
                        "jarvis-offline",
                        status="success",
                        fallback_used=True,
                        attempts=2,
                    )
                )
            except Exception as err:
                raise RuntimeError(f"J.A.R.V.I.S. Core (jarvis-offline) failed: offline_error - {err}")

        local_fallback_triggered = True

    # --------------------------------------------------------
    # AUTO HYBRID MODE: If local OpenJarvis is available, route to it first
    # --------------------------------------------------------
    if active_mode == "auto" and not image_bytes:
        if is_openjarvis_available():
            success_flag, answer_tuple, error, error_type = _attempt_provider(
                lambda: ask_openjarvis(
                    prompt=prompt,
                    system_prompt=SYSTEM_PROMPT,
                    temperature=temperature,
                    model=oj_model,
                    history=history,
                )
            )
            if success_flag and answer_tuple:
                text, provider_label = answer_tuple
                return deliver(
                    _provider_result(
                        text,
                        provider_label,
                        oj_model,
                        status="success",
                        fallback_used=False,
                        attempts=1,
                    )
                )
            local_fallback_triggered = True

    if privacy_mode == "guarded":
        prompt = redact_secrets(prompt)
        if history:
            history = [
                {"role": m.get("role", "user"), "content": redact_secrets(str(m.get("content", "")))}
                for m in history
            ]

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
                fallback_used=fallback_used or local_fallback_triggered,
                attempts=attempts + (1 if local_fallback_triggered else 0),
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
                temperature=temperature,
            )
        )

        if success_flag:
            return success(
                answer, "Gemini", model_id,
                fallback_used=fallback_used, attempts=attempts,
            )

        if not _is_fallback_eligible(error_type):
            raise RuntimeError(f"Gemini ({model_id}) failed: {error_type} - {error}")

        # Retry the selected Gemini model once if temporary unavailability (not if rate-limited).
        if error_type == "temporary_unavailability":
            attempts += 1
            success_flag, answer, error, error_type = _attempt_provider(
                lambda: ask_gemini(
                    model_id=model_id,
                    prompt=prompt,
                    history=history,
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                    temperature=temperature,
                )
            )

            if success_flag:
                return success(
                    answer, "Gemini", model_id,
                    fallback_used=fallback_used, attempts=attempts,
                )

            if not _is_fallback_eligible(error_type):
                raise RuntimeError(f"Gemini ({model_id}) failed: {error_type} - {error}")

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
                    temperature=temperature,
                )
            )

            if success_flag:
                return success(
                    answer, "Gemini", fallback_model,
                    fallback_used=fallback_used, attempts=attempts,
                )

            if not _is_fallback_eligible(error_type):
                raise RuntimeError(f"Gemini ({fallback_model}) failed: {error_type} - {error}")

        fallback_provider = gemini_config.get("fallback_provider")

        if not fallback_provider:
            raise RuntimeError("Gemini fallback exhausted - no fallback provider configured")

        # Groq as an intermediate cloud fallback before OpenJarvis
        if image_bytes is None and os.environ.get("GROQ_API_KEY") and fallback_provider != "Groq" and privacy_mode != "strict":
            groq_fallback_config = get_model("Groq")
            groq_fallback_model = groq_fallback_config["model_id"]
            fallback_used = True
            attempts += 1
            success_flag, answer, error, error_type = _attempt_provider(
                lambda: ask_groq(
                    prompt=prompt,
                    system_prompt=SYSTEM_PROMPT,
                    temperature=temperature,
                    model=groq_fallback_model,
                    history=history,
                )[0]
            )
            if success_flag:
                return success(
                    answer, "Groq", groq_fallback_model,
                    fallback_used=fallback_used, attempts=attempts,
                )
            if not _is_fallback_eligible(error_type):
                raise RuntimeError(f"Groq ({groq_fallback_model}) failed: {error_type} - {error}")

        fallback_config = get_model(fallback_provider)
        fallback_model = fallback_config["model_id"]
        fallback_used = True
        attempts += 1

        if fallback_provider == "OpenJarvis":
            fallback_call = lambda model_id, prompt, history, image_bytes, mime_type, temperature: ask_openjarvis(
                prompt, history=history, temperature=temperature, model=fallback_model
            )[0]
        elif fallback_provider == "Gemini":
            fallback_call = ask_gemini
        elif fallback_provider == "Groq":
            fallback_call = lambda model_id, prompt, history, image_bytes, mime_type, temperature: ask_groq(
                prompt=prompt, system_prompt=SYSTEM_PROMPT, temperature=temperature, model=fallback_model, history=history
            )[0]
        else:
            fallback_call = None

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
                temperature=temperature,
            )
        )

        if success_flag:
            return success(
                answer, fallback_provider, fallback_model,
                fallback_used=fallback_used, attempts=attempts,
            )

        if not _is_fallback_eligible(error_type):
            raise RuntimeError(f"{fallback_provider} ({fallback_model}) failed: {error_type} - {error}")

        raise RuntimeError(f"Gemini fallback exhausted: {fallback_provider} ({fallback_model}) failed: {error_type} - {error}")

    # ========================================================
    # OPENJARVIS (Fallback when local unavailable)
    # ========================================================
    if provider in {"OpenJarvis", "openjarvis"}:
        oj_config = get_model("OpenJarvis")
        fallback_provider = oj_config.get("fallback_provider", "Gemini")
        fallback_config = get_model(fallback_provider)
        fallback_model = fallback_config["model_id"]
        fallback_call = ask_gemini

        success_flag, answer, error, error_type = _attempt_provider(
            lambda: fallback_call(
                model_id=fallback_model,
                prompt=prompt,
                history=history,
                image_bytes=image_bytes,
                mime_type=mime_type,
                temperature=temperature,
            )
        )
        if success_flag:
            return success(
                answer, fallback_provider, fallback_model,
                fallback_used=True, attempts=2,
            )
        raise RuntimeError(f"{fallback_provider} ({fallback_model}) failed: {error_type} - {error}")

    # ========================================================
    # GROQ (Direct selection)
    # ========================================================
    if provider == "Groq":
        groq_config = get_model("Groq")
        groq_model = groq_config.get("model_id", "llama-3.3-70b-versatile")

        success_flag, answer_tuple, error, error_type = _attempt_provider(
            lambda: ask_groq(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=temperature,
                model=groq_model,
                history=history,
            )
        )

        if success_flag and answer_tuple:
            text, provider_label = answer_tuple
            return deliver(
                _provider_result(
                    text,
                    provider_label,
                    groq_model,
                    status="success",
                    fallback_used=False,
                    attempts=1,
                )
            )

        if not _is_fallback_eligible(error_type):
            raise RuntimeError(f"Groq ({groq_model}) failed: {error_type} - {error}")

        # Fallback to OpenJarvis
        oj_config = get_model("OpenJarvis")
        fallback_provider = oj_config.get("fallback_provider", "Gemini")
        fallback_config = get_model(fallback_provider)
        fallback_model = fallback_config["model_id"]
        fallback_call = ask_gemini

        success_flag, answer, error, error_type = _attempt_provider(
            lambda: fallback_call(
                model_id=fallback_model,
                prompt=prompt,
                history=history,
                image_bytes=image_bytes,
                mime_type=mime_type,
                temperature=temperature,
            )
        )
        if success_flag:
            return success(
                answer, fallback_provider, fallback_model,
                fallback_used=True, attempts=2,
            )
        raise RuntimeError(f"{fallback_provider} ({fallback_model}) failed: {error_type} - {error}")

    raise RuntimeError(f"Unsupported provider: {provider}")
