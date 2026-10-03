# CircuitSnap — AI Provider Layer
# Handles communication with Gemini, Groq, and Sarvam AI.

import base64

import streamlit as st
from google import genai
from google.genai import types
from groq import Groq
from sarvamai import SarvamAI

from prompts import SYSTEM_PROMPT

# =========================================================
# API CLIENTS
# =========================================================

@st.cache_resource
def get_gemini_client():
    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )


@st.cache_resource
def get_groq_client():
    return Groq(
        api_key=st.secrets["GROQ_API_KEY"]
    )


@st.cache_resource
def get_sarvam_client():
    return SarvamAI(
        api_subscription_key=st.secrets["SARVAM_API_KEY"]
    )


# =========================================================
# IMAGE CONVERSION
# =========================================================

def image_to_data_url(image_bytes, mime_type):
    """
    Convert image bytes into a base64 data URL.

    Used by Groq and Sarvam vision models.
    """

    encoded = base64.b64encode(image_bytes).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


# =========================================================
# GEMINI
# =========================================================

def ask_gemini(
    model_id,
    prompt,
    image_bytes=None,
    mime_type=None,
):
    """
    Send a request to Google Gemini.

    Gemini accepts image bytes directly.
    """

    client = get_gemini_client()

    contents = []

    if image_bytes is not None:
        contents.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type,
            )
        )

    contents.append(prompt)

    response = client.models.generate_content(
        model=model_id,
        contents=contents,
        config=types.GenerateContentConfig(
            max_output_tokens=1200,
        ),
    )

    return response.text


# =========================================================
# GROQ
# =========================================================

def ask_groq(
    model_id,
    prompt,
    image_bytes=None,
    mime_type=None,
):
    """
    Send a request to a Groq model.

    Groq vision models receive images as base64 data URLs.
    """

    client = get_groq_client()

    content = [
        {
            "type": "text",
            "text": prompt,
        }
    ]

    if image_bytes is not None:
        content.append(
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

    response = client.chat.completions.create(
    model=model_id,
    messages=[
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": content,
        },
    ],
    max_completion_tokens=1200,
)

    return response.choices[0].message.content


# =========================================================
# SARVAM AI
# =========================================================

def ask_sarvam(
    model_id,
    prompt,
    image_bytes=None,
    mime_type=None,
):
    """
    Send a request to Sarvam AI.

    Sarvam V2 models require beta access for the API key.
    If beta access is unavailable, return a clean user-facing
    message instead of exposing the API traceback.
    """

    client = get_sarvam_client()

    if image_bytes is not None:
        content = [
            {
                "type": "text",
                "text": prompt,
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": image_to_data_url(
                        image_bytes,
                        mime_type,
                    )
                },
            },
        ]
    else:
        content = prompt

    try:
        response = client.chat.completions_v2(
    model=model_id,
    messages=[
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": content,
        },
    ],
    max_tokens=1200,
)

        return response.choices[0].message.content

    except Exception as error:
        error_text = str(error).lower()

        if (
            "beta" in error_text
            or "not available" in error_text
            or "invalid_request_error" in error_text
        ):
            return (
                f"⚠️ {model_id} requires Sarvam beta API access "
                "for this API key.\n\n"
                "Please select Gemini or Groq for this demo, "
                "or request beta access from Sarvam AI."
            )

        if (
            "403" in error_text
            or "api key" in error_text
            or "authentication" in error_text
        ):
            return (
                "🔐 Sarvam authentication failed. "
                "Please check the SARVAM_API_KEY configuration."
            )

        return (
            "⚠️ Sarvam is temporarily unavailable. "
            "Please try again or select another model."
        )

# =========================================================
# UNIFIED PROVIDER FUNCTION
# =========================================================

def ask_provider(
    provider,
    model_id,
    prompt,
    image_bytes=None,
    mime_type=None,
):
    """
    Send a request to the selected AI provider.
    """

    if provider == "Gemini":
        return ask_gemini(
            model_id=model_id,
            prompt=prompt,
            image_bytes=image_bytes,
            mime_type=mime_type,
        )

    if provider == "Groq":
        return ask_groq(
            model_id=model_id,
            prompt=prompt,
            image_bytes=image_bytes,
            mime_type=mime_type,
        )

    if provider == "Sarvam":
        return ask_sarvam(
            model_id=model_id,
            prompt=prompt,
            image_bytes=image_bytes,
            mime_type=mime_type,
        )

    raise ValueError(
        f"Unsupported provider: {provider}"
    )