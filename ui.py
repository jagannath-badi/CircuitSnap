"""
CircuitSnap — UI Components

Responsive presentation layer for CircuitSnap.

This file handles:
- Header
- Hero
- Quick actions
- Model selector
- Image upload
- Status cards
- Footer

Application state and AI communication remain outside this file.
"""

import html

import streamlit as st


# ============================================================
# Styling
# ============================================================

def load_styles():
    """Load the central CircuitSnap stylesheet."""

    try:
        with open("styles.css", "r", encoding="utf-8") as file:
            css = file.read()

        st.html(f"<style>{css}</style>")

    except FileNotFoundError:
        st.warning(
            "CircuitSnap stylesheet could not be loaded."
        )


# ============================================================
# Header
# ============================================================

def render_header():
    """Render the workspace identity without duplicating composer controls."""
    st.html(
        """
        <header class="cs-header">
            <div class="cs-header-left">
                <div class="cs-logo" aria-hidden="true">CS</div>
                <div class="cs-brand-copy">
                    <div class="cs-header-title">
                        CircuitSnap
                    </div>
                    <div class="cs-header-subtitle">
                        Electronics workspace
                    </div>
                </div>
            </div>
        </header>
        """
    )


# ============================================================
# Hero
# ============================================================

def render_hero(name=None):
    """Render the main empty-state hero."""

    greeting = (
        f"Welcome, {html.escape(str(name))}."
        if name
        else "Your electronics workspace."
    )

    st.html(
        f"""
        <section class="cs-hero">
           <div class="cs-eyebrow">CIRCUITSNAP · AI VISION FOR ECE</div>
<p class="cs-hero-greeting">{greeting}</p>
<h1 class="cs-hero-title">
    See it. Understand it. Build it.
</h1>
<p class="cs-hero-text">
    Upload a photo of a component, circuit, schematic, PCB, or lab setup.
    CircuitSnap analyzes what it can see, explains the electronics behind it,
    and clearly separates confirmed observations from uncertainty.
</p>
        </section>
        """
    )


# ============================================================
# Quick actions
# ============================================================

QUICK_ACTIONS = {
    "Identify a component": {
        "prompt": (
            "Identify the main electronic component in this image. "
            "Explain what it does and mention anything important "
            "that can or cannot be confirmed."
        ),
    },
    "Explain a circuit": {
        "prompt": (
            "Analyze this circuit and explain its main function "
            "and how the visible components work together. "
            "Only describe connections that can be supported by "
            "the image."
        ),
    },
    "Debug my lab setup": {
        "prompt": (
            "Analyze this electronics lab setup and identify "
            "any clearly visible connection or component issues. "
            "Separate confirmed observations from uncertain ones."
        ),
    },
    "Learn an ECE concept": {
        "prompt": (
            "Explain this electronics concept in a clear, "
            "ECE-student-friendly way. Start with the core idea "
            "and add technical detail where useful."
        ),
    },
}


def render_quick_actions():
    """
    Render starter prompts.

    Returns:
        str | None:
            The selected starter prompt.
    """

    st.markdown(
        '<div class="cs-section-label">Start with</div>',
        unsafe_allow_html=True,
    )

    columns = st.columns(2)

    selected_prompt = None

    for index, (title, action) in enumerate(
        QUICK_ACTIONS.items()
    ):
        with columns[index % 2]:
            if st.button(
                title,
                key=f"quick_action_{index}",
                width="stretch",
            ):
                selected_prompt = action["prompt"]

    return selected_prompt


# ============================================================
# Model selector
# ============================================================

def render_model_selector(
    model_names,
    current_model,
):
    """Render the model selector."""

    if not model_names:
        return current_model

    try:
        default_index = model_names.index(
            current_model
        )
    except ValueError:
        default_index = 0

    return st.selectbox(
        "AI model",
        options=model_names,
        index=default_index,
        label_visibility="collapsed",
        key="selected_model",
        help="Choose the provider for your next request.",
    )


# ============================================================
# Image uploader
# ============================================================

def render_image_uploader():
    """Render the electronics image uploader."""

    return st.file_uploader(
        "Upload an electronics image",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp",
        ],
        label_visibility="collapsed",
        key="circuit_image",
    )

# ============================================================
# Chat composer
# ============================================================

def render_chat_composer(
    model_names,
    current_model,
    image_key="composer_image",
    input_key="composer_message",
):
    """Render the fixed composer and its independent provider control."""

    with st.container(key="cs-composer-shell"):
        with st.form("chat_composer", clear_on_submit=False):
            col_upload, col_message, col_send = st.columns(
                [0.8, 8.0, 1.2],
                vertical_alignment="center",
            )

            with col_upload:
                uploaded_file = st.file_uploader(
                    "Attach image",
                    type=["png", "jpg", "jpeg", "webp"],
                    label_visibility="collapsed",
                    key=image_key,
                )

            with col_message:
                user_input = st.text_input(
                    "Message",
                    placeholder="Ask about a component, circuit, or concept…",
                    label_visibility="collapsed",
                    key=input_key,
                )

            with col_send:
                submitted = st.form_submit_button(
                    "Send message",
                    width="stretch",
                    help="Send message",
                )

        # Keep this outside the form so provider switches rerun immediately.
        # CSS places this independent control into the same visual row.
        render_model_selector(model_names, current_model)

    return (
        submitted,
        user_input,
        uploaded_file,
    )

def render_image_preview(uploaded_file):
    """Render a preview of the uploaded image."""

    if uploaded_file is None:
        return

    st.markdown(
        '<div class="cs-section-label">Image</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="cs-image-preview">',
        unsafe_allow_html=True,
    )

    st.image(
        uploaded_file,
        width="stretch",
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# Status card
# ============================================================

def render_status_card(
    title,
    message,
    state=None,
):
    """Render a reusable status/confidence card."""

    state_class = ""

    if state in {
        "confirmed",
        "likely",
        "cannot-confirm",
    }:
        state_class = f" cs-{state}"

    safe_title = html.escape(
        str(title)
    )

    safe_message = html.escape(
        str(message)
    )

    st.html(
        f"""
        <div class="cs-card{state_class}">

            <div class="cs-card-title">
                {safe_title}
            </div>

            <div class="cs-card-text">
                {safe_message}
            </div>

        </div>
        """
    )


# ============================================================
# Divider
# ============================================================

def render_divider():
    """Render a subtle responsive divider."""

    st.html(
        '<div class="cs-divider"></div>'
    )


# ============================================================
# Footer
# ============================================================

def render_footer():
    """Render the application footer."""

    st.html(
        """
        <div class="cs-footer">

            <strong>CircuitSnap</strong>
            · AI electronics assistant for ECE students

            <br>

            Verify important engineering decisions with
            datasheets and proper measurements.

        </div>
        """
    )


def render_chat_message(message):
    """Render one conversation message, including provider status metadata."""

    role = message.get("role", "assistant")
    content = message.get("content", "")
    kind = message.get("kind", "text")
    metadata = message.get("metadata") or {}

    author = "You" if role == "user" else "CircuitSnap"
    with st.chat_message(author):
        author_class = "cs-message-user" if role == "user" else "cs-message-assistant"
        st.markdown(
            f'<div class="cs-message-author {author_class}">{author}</div>',
            unsafe_allow_html=True,
        )

        if kind == "image":
            st.image(content, width="stretch")
        elif metadata.get("status") == "error":
            st.error(content)
        else:
            st.markdown(content)

        if metadata.get("fallback_used"):
            actual_provider = html.escape(
                str(metadata.get("provider") or "another provider")
            )
            st.caption(f"Fallback response · {actual_provider}")
