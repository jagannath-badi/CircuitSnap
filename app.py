import time
import streamlit as st
from google import genai
from google.genai import types

from models import MODELS, get_model
from providers import ask_provider

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT,
)


# -----------------------------
# Page configuration
# -----------------------------

st.set_page_config(
    page_title="CircuitSnap",
    page_icon="🔧",
    layout="centered",
)


# -----------------------------
# UI theme (CSS only — no backend logic lives here)
#
# NOTE on selectors: a few rules below target Streamlit's internal
# data-testid attributes (e.g. [data-testid="stChatMessage"]) purely as
# styling hooks. These are not a public/stable Streamlit API — if a
# future Streamlit version renames these attributes, the affected rule
# will simply stop applying (the app keeps working, just less styled).
# Each such selector is kept isolated below so it's easy to find and
# update if that happens.
# -----------------------------

CIRCUITSNAP_CSS = """
<style>
:root {
    --cs-bg-primary: #0B0F14;
    --cs-bg-secondary: #10151C;
    --cs-surface-card: #151B23;
    --cs-surface-elev: #1B222C;
    --cs-border: #252D38;
    --cs-text-primary: #F5F7FA;
    --cs-text-secondary: #9AA5B1;
    --cs-text-muted: #6F7A87;
    --cs-accent: #38BDF8;
    --cs-accent-2: #22D3EE;
    --cs-success: #22C55E;
    --cs-warning: #F59E0B;
    --cs-error: #EF4444;
    --cs-radius-sm: 6px;
    --cs-radius-md: 10px;
    --cs-radius-lg: 14px;
}

/* Reduced-motion: disable all custom animation/transition globally */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.001ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.001ms !important;
    }
}

/* -------- App shell -------- */
.stApp {
    background: var(--cs-bg-primary);
    background-image:
        linear-gradient(var(--cs-bg-primary), var(--cs-bg-primary)),
        repeating-linear-gradient(
            0deg,
            rgba(56, 189, 248, 0.025) 0px,
            rgba(56, 189, 248, 0.025) 1px,
            transparent 1px,
            transparent 64px
        ),
        repeating-linear-gradient(
            90deg,
            rgba(56, 189, 248, 0.025) 0px,
            rgba(56, 189, 248, 0.025) 1px,
            transparent 1px,
            transparent 64px
        );
    background-blend-mode: normal;
}

.block-container {
    max-width: 760px;
    padding-top: 1.5rem;
    padding-bottom: 7rem;
}

body, .stApp, p, span, div, li {
    color: var(--cs-text-primary);
}

/* -------- Header -------- */
.cs-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 14px 18px;
    margin-bottom: 1.25rem;
    background: var(--cs-surface-card);
    border: 1px solid var(--cs-border);
    border-radius: var(--cs-radius-lg);
    animation: cs-fade-in-up 260ms ease-out;
}

.cs-header-left {
    display: flex;
    align-items: center;
    gap: 12px;
}

.cs-logo {
    width: 36px;
    height: 36px;
    flex-shrink: 0;
}

.cs-header-title {
    font-size: 1.05rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: var(--cs-text-primary);
    line-height: 1.15;
}

.cs-header-subtitle {
    font-size: 0.78rem;
    color: var(--cs-text-secondary);
    line-height: 1.1;
}

.cs-status {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 0.74rem;
    color: var(--cs-text-secondary);
    white-space: nowrap;
}

.cs-status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--cs-success);
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.55);
    animation: cs-pulse 2.2s ease-in-out infinite;
}

@keyframes cs-pulse {
    0%   { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.45); }
    70%  { box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
    100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
}

@keyframes cs-fade-in-up {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* -------- Welcome / empty state -------- */
.cs-hero {
    text-align: center;
    padding: 2.4rem 1.2rem 1.6rem;
    animation: cs-fade-in-up 320ms ease-out;
}

.cs-hero h1 {
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.015em;
    margin-bottom: 0.35rem;
    color: var(--cs-text-primary);
}

.cs-hero p {
    font-size: 0.95rem;
    color: var(--cs-text-secondary);
    margin-bottom: 1.4rem;
}

.cs-chip-row {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
    margin-bottom: 1.4rem;
}

.cs-chip {
    font-size: 0.8rem;
    color: var(--cs-text-secondary);
    background: var(--cs-surface-card);
    border: 1px solid var(--cs-border);
    border-radius: 999px;
    padding: 6px 14px;
    transition: border-color 150ms ease, color 150ms ease;
}

.cs-chip:hover {
    border-color: var(--cs-accent);
    color: var(--cs-text-primary);
}

.cs-hero-hint {
    font-size: 0.82rem;
    color: var(--cs-text-muted);
}

/* -------- Onboarding card -------- */
.cs-onboard-wrap {
    text-align: center;
    padding: 1.2rem 1rem 0.4rem;
    animation: cs-fade-in-up 300ms ease-out;
}

.cs-onboard-wrap h1 {
    font-size: 1.7rem;
    font-weight: 700;
    letter-spacing: -0.015em;
    margin-bottom: 0.3rem;
}

.cs-onboard-wrap p {
    color: var(--cs-text-secondary);
    font-size: 0.95rem;
    margin-bottom: 0.4rem;
}

/* Streamlit form container -> styled as a card */
div[data-testid="stForm"] {
    background: var(--cs-surface-card);
    border: 1px solid var(--cs-border);
    border-radius: var(--cs-radius-lg);
    padding: 1.4rem 1.4rem 1rem;
}

/* -------- Native chat messages (styling hook only) -------- */
div[data-testid="stChatMessage"] {
    background: var(--cs-surface-card);
    border: 1px solid var(--cs-border);
    border-radius: var(--cs-radius-lg);
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.7rem;
    animation: cs-fade-in-up 220ms ease-out;
}

/* Technical markdown inside assistant/user bubbles */
div[data-testid="stChatMessage"] h1,
div[data-testid="stChatMessage"] h2,
div[data-testid="stChatMessage"] h3 {
    font-size: 0.92rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--cs-accent);
    border-bottom: 1px solid var(--cs-border);
    padding-bottom: 0.3rem;
    margin: 0.9rem 0 0.5rem;
}

div[data-testid="stChatMessage"] h1:first-child,
div[data-testid="stChatMessage"] h2:first-child,
div[data-testid="stChatMessage"] h3:first-child {
    margin-top: 0;
}

div[data-testid="stChatMessage"] strong {
    color: var(--cs-text-primary);
}

div[data-testid="stChatMessage"] code {
    background: var(--cs-surface-elev);
    border: 1px solid var(--cs-border);
    border-radius: 4px;
    padding: 0.1rem 0.35rem;
    font-size: 0.85em;
    color: var(--cs-accent-2);
}

div[data-testid="stChatMessage"] ul,
div[data-testid="stChatMessage"] ol {
    margin-left: 0.2rem;
}

div[data-testid="stChatMessage"] li {
    margin-bottom: 0.25rem;
    color: var(--cs-text-secondary);
}

div[data-testid="stChatMessage"] p {
    color: var(--cs-text-secondary);
    line-height: 1.55;
}

/* -------- Uploaded / displayed images (styling hook only) -------- */
div[data-testid="stChatMessage"] div[data-testid="stImage"] img {
    border-radius: var(--cs-radius-md);
    border: 1px solid var(--cs-border);
    max-width: 100%;
}

/* -------- AI model selector -------- */
div[data-testid="stSelectbox"] {
    margin-bottom: 0.15rem;
}

div[data-testid="stSelectbox"] label {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--cs-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.25rem;
}

div[data-testid="stSelectbox"] > div > div {
    min-height: 2.4rem;
}

div[data-testid="stCaptionContainer"] {
    margin-top: -0.15rem;
    margin-bottom: 0.35rem;
}


/* -------- Chat input (styling hook only) -------- */
div[data-testid="stChatInput"] {
    background: var(--cs-surface-elev);
    border: 1px solid var(--cs-border);
    border-radius: var(--cs-radius-md);
    transition: border-color 160ms ease, box-shadow 160ms ease;
}

div[data-testid="stChatInput"]:focus-within {
    border-color: var(--cs-accent);
    box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.15);
}

div[data-testid="stChatInput"] textarea {
    color: var(--cs-text-primary) !important;
}

/* -------- Buttons -------- */
.stButton > button,
button[kind="formSubmit"] {
    background: var(--cs-accent);
    color: #0B0F14;
    border: none;
    border-radius: var(--cs-radius-sm);
    font-weight: 600;
    padding: 0.5rem 1.1rem;
    transition: filter 150ms ease, transform 150ms ease;
}

.stButton > button:hover,
button[kind="formSubmit"]:hover {
    filter: brightness(1.08);
    transform: translateY(-1px);
}

/* -------- Text input (onboarding name field) -------- */
div[data-testid="stTextInput"] input {
    background: var(--cs-surface-elev);
    border: 1px solid var(--cs-border);
    border-radius: var(--cs-radius-sm);
    color: var(--cs-text-primary);
}

div[data-testid="stTextInput"] input:focus {
    border-color: var(--cs-accent);
    box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.15);
}

/* Hide default Streamlit chrome for a cleaner demo surface */
#MainMenu, footer {
    visibility: hidden;
}
</style>
"""

st.markdown(CIRCUITSNAP_CSS, unsafe_allow_html=True)


CS_LOGO_SVG = '<svg class="cs-logo" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="1" y="1" width="34" height="34" rx="9" fill="#151B23" stroke="#252D38"/><circle cx="11" cy="11" r="2.1" fill="#38BDF8"/><circle cx="25" cy="25" r="2.1" fill="#22D3EE"/><path d="M11 13.1V18H25V22.9" stroke="#38BDF8" stroke-width="1.6" stroke-linecap="round"/><circle cx="18" cy="18" r="1.6" fill="#F5F7FA"/></svg>'


def render_header(subtitle):
    st.markdown(
        f'<div class="cs-header">'
        f'<div class="cs-header-left">'
        f'{CS_LOGO_SVG}'
        f'<div>'
        f'<div class="cs-header-title">CircuitSnap</div>'
        f'<div class="cs-header-subtitle">{subtitle}</div>'
        f'</div>'
        f'</div>'
        f'<div class="cs-status">'
        f'<span class="cs-status-dot"></span>'
        f'Multi-Model Vision Ready'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# -----------------------------
# Gemini configuration
# -----------------------------

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

MODEL_NAME = "gemini-3.8-flash"


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


# -----------------------------
# Helper functions
# -----------------------------

def ask_gemini(parts):
    max_attempts = 2

    for attempt in range(max_attempts):
        try:
            response = st.session_state.chat.send_message(parts)
            return response.text

        except Exception as error:
            error_text = str(error)

            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
            ):
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue

                # Fallback to a lower-latency Gemini model
                try:
                    fallback_chat = gemini_client.chats.create(
                        model="gemini-3.5-flash-lite",
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            thinking_config=types.ThinkingConfig(
                                thinking_level="low"
                            ),
                            max_output_tokens=1200,
                        ),
                    )

                    fallback_response = fallback_chat.send_message(parts)
                    return fallback_response.text

                except Exception:
                    return (
                        "⚠️ Gemini is temporarily unavailable. "
                        "Please try again in a few seconds."
                    )

            if "401" in error_text or "UNAUTHENTICATED" in error_text:
                return (
                    "🔐 There is a problem authenticating with Gemini. "
                    "Please check the API configuration."
                )

            return (
                "⚠️ I couldn't process that request right now. "
                "Please try again."
            )


def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])

        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):
    message = {
        "role": role,
        "kind": kind,
        "content": content,
    }

    st.session_state.messages.append(message)
    render_message(message)


# -----------------------------
# Onboarding
# -----------------------------

if "onboarded" not in st.session_state:

    render_header("AI Electronics Vision Assistant")

    st.markdown(
        """
        <div class="cs-onboard-wrap">
            <h1>Welcome to CircuitSnap</h1>
            <p>Your AI-powered electronics lab partner.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("onboarding_form"):

        name = st.text_input(
            "Your name"
        )

        submitted = st.form_submit_button(
            "Let's start 🚀"
        )

        if submitted:

            if not name.strip():
                st.warning("Please enter your name.")

            else:
                st.session_state.name = name.strip()
                st.session_state.chat = gemini_client.chats.create(
                    model=MODEL_NAME,
                    config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    thinking_config=types.ThinkingConfig(
                    thinking_level="low"
                        ),
                        max_output_tokens=1200,
                    ),
                )

                st.session_state.messages = []
                st.session_state.onboarded = True

                st.rerun()

    st.stop()


# -----------------------------
# Main application
# -----------------------------

render_header(f"Welcome, {st.session_state.name} — upload an image or ask a question")


# -----------------------------
# Display conversation history
# -----------------------------

if not st.session_state.messages:

    st.markdown(
        """
        <div class="cs-hero">
            <h1>Understand electronics from a picture.</h1>
            <p>Upload a component, circuit, schematic, or lab setup — or just ask a question.</p>
            <div class="cs-chip-row">
                <span class="cs-chip">Component</span>
                <span class="cs-chip">Circuit</span>
                <span class="cs-chip">Schematic</span>
                <span class="cs-chip">Lab Setup</span>
            </div>
            <div class="cs-hero-hint">Attach a photo or type a question below to get started.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(
            name=st.session_state.name
        ),
    )

else:

    for message in st.session_state.messages:
        render_message(message)

# -----------------------------
# AI model selector
# -----------------------------

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "Gemini 3.8 Flash"

selected_model_name = st.selectbox(
    "AI Model",
    options=list(MODELS.keys()),
    index=list(MODELS.keys()).index(
        st.session_state.selected_model
    ),
)

st.session_state.selected_model = selected_model_name

selected_model = get_model(selected_model_name)

st.caption(
    f"🏢 {selected_model['provider']}  •  "
    f"{'👁️ Vision' if selected_model['vision'] else '💬 Text'}  •  "
    f"{selected_model['status']}"
)


# -----------------------------
# Chat input
# -----------------------------

user_input = st.chat_input(
    "Ask about a component, circuit, schematic, or upload an image...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)


if user_input:

    photo = (
        user_input.files[0]
        if user_input.files
        else None
    )

    text = user_input.text

    parts = []

    # Data used by Groq/Sarvam providers
    provider_prompt = ""
    photo_bytes = None
    photo_mime_type = None


    # Handle image

    if photo is not None:

        photo_bytes = photo.getvalue()
        photo_mime_type = photo.type

        add_message(
            "user",
            "image",
            photo_bytes,
        )

        parts.append(
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type=photo.type,
            )
        )


    # Handle text

    if text:

        add_message(
            "user",
            "text",
            text,
        )

        provider_prompt = (
            text
            + "\n\n"
            + "Answer this as a concise electronics assistant. "
            + "For this simple question, use no more than 80 words. "
            + "Give only the essential explanation. "
            + "Do not add a table, detailed classifications, formulas, "
            + "applications, or extended examples unless specifically asked."
        )

        parts.append(provider_prompt)


    # Image without a question

    elif photo is not None:

        provider_prompt = """
        Analyze this electronics image.

        Identify the component, circuit, schematic,
        or setup if possible.

        Explain what it is, its function, how it
        works, and important connections.
        """

        parts.append(provider_prompt)


    # Ask selected AI model

    with st.spinner(
        f"Analyzing with {selected_model_name}... 🔍"
    ):

        if selected_model["provider"] == "Gemini":

            answer = ask_gemini(parts)

        else:

            if photo is not None and not selected_model["vision"]:

                answer = (
                    f"⚠️ {selected_model_name} does not support "
                    "image analysis. Please select a vision model."
                )

            else:

                answer = ask_provider(
                    provider=selected_model["provider"],
                    model_id=selected_model["model_id"],
                    prompt=provider_prompt,
                    image_bytes=photo_bytes,
                    mime_type=photo_mime_type,
                )


    add_message(
        "assistant",
        "text",
        answer,
    )