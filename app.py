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
from engine import run_engine, select_request_image_context
from prompts import WELCOME_MESSAGE_TEMPLATE
from ui import (
    load_styles,
    render_header,
    render_hero,
    render_quick_actions,
    render_chat_composer,
    render_chat_message,
    render_footer,
)


# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="CircuitSnap",
    page_icon="🔌",
    layout="wide",
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
        "image_context": None,
        "composer_image_version": 0,
        "composer_input_version": 0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_state()


# ============================================================
# Conversation helpers
# ============================================================

def add_message(role, content, kind="text", metadata=None):
    """
    Store a conversation message with optional response metadata.
    """
    message = {
        "role": role,
        "content": content,
        "kind": kind,
    }

    if metadata is not None:
        message["metadata"] = metadata

    st.session_state.messages.append(message)


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
        render_chat_message(message)


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
            "label relevant image-derived claims CONFIRMED, LIKELY, "
            "or CANNOT CONFIRM. Use CONFIRMED for clear markings or "
            "bands and an unambiguous nominal decoded value; otherwise "
            "use LIKELY. Do not infer measurements or unseen ratings."
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
            <div class="cs-eyebrow">A bench-side workspace for ECE</div>
            <h1>Make sense of what’s on your bench.</h1>
            <p>Ask about a component, trace a circuit, or work through a lab question.</p>
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
            "Open workspace",
            width="stretch",
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
# Model configuration
# ============================================================

model_names = get_model_names()

# The selector is independent of the submission form. Its keyed state is
# updated before Streamlit reruns, so the header reflects no-send switches.
selected_model_name = st.session_state.selected_model
render_header()

submitted, user_input, uploaded_file = (
    render_chat_composer(
        model_names=model_names,
        current_model=selected_model_name,
        image_key=f"composer_image_{st.session_state.composer_image_version}",
        input_key=f"composer_input_{st.session_state.composer_input_version}",
    )
)

selected_model_name = st.session_state.selected_model
selected_model = get_model(selected_model_name)


# ============================================================
# Empty state / quick actions
# ============================================================

has_user_messages = any(
    message.get("role") == "user"
    for message in st.session_state.messages
)

is_first_submission = submitted and (
    bool(user_input.strip()) or uploaded_file is not None
)

if not has_user_messages and not is_first_submission:

    render_hero(st.session_state.name)

    quick_prompt = render_quick_actions()

    if quick_prompt:

        st.session_state.pending_prompt = quick_prompt

        st.rerun()

    if st.session_state.pending_prompt:
        st.markdown(
            '<div class="cs-prompt-hint">Starter selected · Add an image or type your question below.</div>',
            unsafe_allow_html=True,
        )

# ============================================================
# Conversation
# ============================================================

else:

    render_conversation()


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

    uploaded_image_bytes = None
    uploaded_image_mime_type = None

    if uploaded_file is not None:

        uploaded_image_bytes = uploaded_file.getvalue()
        uploaded_image_mime_type = uploaded_file.type

        st.session_state.image_context = {
            "image_bytes": uploaded_image_bytes,
            "mime_type": uploaded_image_mime_type,
        }

        add_message(
            role="user",
            content=uploaded_image_bytes,
            kind="image",
        )

    image_bytes, image_mime_type = select_request_image_context(
        user_text=text,
        current_image_bytes=uploaded_image_bytes,
        current_mime_type=uploaded_image_mime_type,
        previous_image_context=st.session_state.image_context,
    )

    reusing_previous_image = (
        uploaded_image_bytes is None
        and image_bytes is not None
        and st.session_state.image_context is not None
    )
    previous_visual_context = None
    if reusing_previous_image:
        previous_visual_context = (
            st.session_state.image_context.get("visual_context")
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

    if uploaded_image_bytes is not None:
        render_chat_message(
            {
                "role": "user",
                "content": uploaded_image_bytes,
                "kind": "image",
            }
        )

    if text:
        render_chat_message(
            {
                "role": "user",
                "content": text,
                "kind": "text",
            }
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

    with st.spinner(
        f"Analyzing with {selected_model_name}..."
    ):
        result = run_engine(
            provider=selected_model["provider"],
            model_id=selected_model["model_id"],
            user_text=prompt,
            conversation_history=history,
            image_bytes=image_bytes,
            mime_type=image_mime_type,
            previous_visual_context=previous_visual_context,
        )

    answer = result["answer"]
    provider_metadata = {
        "provider": result.get("provider", selected_model["provider"]),
        "model_id": result.get("model_id", selected_model["model_id"]),
        "status": result.get("status", "success"),
        "error_type": result.get("error_type"),
        "fallback_used": result.get("fallback_used", False),
        "attempts": result.get("attempts", 1),
    }

    if uploaded_file is not None and st.session_state.image_context:
        engine_context = result.get("context")
        visual_context = {
            "input_type": getattr(
                engine_context,
                "input_type",
                "unknown",
            ),
            "workflow": getattr(
                engine_context,
                "workflow",
                "general_electronics",
            ),
        }
        if provider_metadata["status"] == "success":
            visual_context["summary"] = answer

        st.session_state.image_context["visual_context"] = visual_context

    render_chat_message(
        {
            "role": "assistant",
            "content": answer,
            "kind": "text",
            "metadata": provider_metadata,
        }
    )

    # --------------------------------------------------------
    # Store assistant response
    # --------------------------------------------------------

    add_message(
        role="assistant",
        content=answer,
        kind="text",
        metadata=provider_metadata,
    )

    st.session_state.composer_input_version += 1

    if uploaded_file is not None:
        st.session_state.composer_image_version += 1

    st.rerun()


# ============================================================
# Footer
# ============================================================

render_footer()
