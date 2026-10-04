"""
CircuitSnap — Main Application

The app controller owns:
- Streamlit page configuration
- session state
- conversation history
- model selection
- user input
- image handling

UI presentation lives in ui.py.
AI orchestration lives in engine.py.
AI communication lives in providers.py.
Model configuration lives in models.py.
AI behavior lives in prompts.py.
"""

import streamlit as st

from models import get_model, get_model_names, get_default_model
from engine import run_engine
from prompts import WELCOME_MESSAGE_TEMPLATE
from ui import (
    load_styles,
    render_header,
    render_hero,
    render_quick_actions,
    render_chat_composer,
    render_footer,
)


# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="CircuitSnap",
    page_icon="🔧",
    layout="centered",
)


# ============================================================
# Load UI
# ============================================================

load_styles()


# ============================================================
# Session state
# ============================================================

def initialize_state():
    defaults = {
        "messages": [],
        "selected_model": get_default_model(),
        "name": "",
        "onboarded": False,
        "pending_prompt": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_state()


# ============================================================
# Conversation helpers
# ============================================================

def add_message(role, content, kind="text"):
    """
    Store a provider-independent conversation message.
    """
    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
            "kind": kind,
        }
    )


def get_text_history():
    """
    Return only textual conversation history.

    Images are displayed by CircuitSnap but the current image
    is sent separately to the engine/provider.
    """

    history = []

    for message in st.session_state.messages:

        if message.get("kind") != "text":
            continue

        role = message.get("role")
        content = message.get("content")

        if role not in {"user", "assistant"}:
            continue

        if not content:
            continue

        history.append(
            {
                "role": role,
                "content": content,
            }
        )

    return history


def render_conversation():
    """
    Render the conversation stored by CircuitSnap.
    """

    for message in st.session_state.messages:

        role = message.get("role")
        kind = message.get("kind", "text")
        content = message.get("content")

        with st.chat_message(role):

            if kind == "image":
                st.image(
                    content,
                    use_container_width=True,
                )

            else:
                st.markdown(content)


# ============================================================
# Prompt helpers
# ============================================================

def build_prompt(user_text, image_present=False):
    """
    Build the current user request.

    Quick actions are starter instructions, not permanent modes.
    """

    pending_prompt = st.session_state.get("pending_prompt")

    if user_text:

        prompt = user_text.strip()

        if pending_prompt:
            prompt = (
                f"{pending_prompt}\n\n"
                f"User's question:\n{prompt}"
            )

        return prompt

    if image_present:

        if pending_prompt:
            return pending_prompt

        return (
            "Analyze this electronics image.\n\n"
            "Identify what can be reliably identified, "
            "explain its function and working, and clearly "
            "distinguish confirmed observations from uncertain ones."
        )

    if pending_prompt:
        return pending_prompt

    return ""


def clear_pending_prompt():
    st.session_state.pending_prompt = None


# ============================================================
# Onboarding
# ============================================================

if not st.session_state.onboarded:

    render_header()

    st.markdown(
        """
        <div class="cs-onboard-wrap">
            <h1>Welcome to CircuitSnap</h1>
            <p>
                Understand components, circuits, schematics,
                and electronics concepts with AI.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("onboarding_form"):

        name = st.text_input(
            "Your name",
            placeholder="Enter your name",
        )

        submitted = st.form_submit_button(
            "Let's start 🚀",
            use_container_width=True,
        )

        if submitted:

            if not name.strip():

                st.warning("Please enter your name.")

            else:

                st.session_state.name = name.strip()
                st.session_state.onboarded = True

                add_message(
                    "assistant",
                    WELCOME_MESSAGE_TEMPLATE.format(
                        name=st.session_state.name
                    ),
                )

                st.rerun()

    st.stop()


# ============================================================
# Main header
# ============================================================

selected_model_name = st.session_state.selected_model

render_header(selected_model_name)


# ============================================================
# Model configuration
# ============================================================

model_names = get_model_names()

selected_model_name = st.session_state.selected_model
selected_model = get_model(selected_model_name)


# ============================================================
# Empty state / quick actions
# ============================================================

if not st.session_state.messages:

    render_hero()

    quick_prompt = render_quick_actions()

    if quick_prompt:

        st.session_state.pending_prompt = quick_prompt

        st.rerun()


# ============================================================
# Conversation
# ============================================================

else:

    render_conversation()


# ============================================================
# Chat composer
# ============================================================

submitted, user_input, uploaded_file, selected_model_name = (
    render_chat_composer(
        model_names=model_names,
        current_model=st.session_state.selected_model,
    )
)

st.session_state.selected_model = selected_model_name

selected_model = get_model(selected_model_name)


# ============================================================
# Handle request
# ============================================================

if submitted:

    text = user_input.strip()

    if not text and uploaded_file is None:
     st.warning("Please enter a question or upload an image.")
     st.stop()

    # --------------------------------------------------------
    # Current image
    # --------------------------------------------------------

    image_bytes = None
    image_mime_type = None

    if uploaded_file is not None:

        image_bytes = uploaded_file.getvalue()
        image_mime_type = uploaded_file.type

        add_message(
            role="user",
            content=image_bytes,
            kind="image",
        )

    # --------------------------------------------------------
    # Build current request
    # --------------------------------------------------------

    prompt = build_prompt(
        user_text=text,
        image_present=image_bytes is not None,
    )

    # --------------------------------------------------------
    # Store current user message
    # --------------------------------------------------------

    add_message(
        role="user",
        content=text,
        kind="text",
    )

    # --------------------------------------------------------
    # Previous conversation
    # --------------------------------------------------------

    history = get_text_history()

    # Current user message is handled separately by engine.py.
    if history and history[-1]["role"] == "user":
        history = history[:-1]

    clear_pending_prompt()

    # --------------------------------------------------------
    # Engine → Provider
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            f"Analyzing with {selected_model_name}... 🔍"
        ):

            result = run_engine(
                provider=selected_model["provider"],
                model_id=selected_model["model_id"],
                user_text=prompt,
                conversation_history=history,
                image_bytes=image_bytes,
                mime_type=image_mime_type,
            )

            answer = result["answer"]

        st.markdown(answer)

    # --------------------------------------------------------
    # Store assistant response
    # --------------------------------------------------------

    add_message(
        role="assistant",
        content=answer,
        kind="text",
    )

    st.rerun()


# ============================================================
# Footer
# ============================================================

render_footer()