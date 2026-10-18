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
import pathlib

import streamlit as st


# ============================================================
# Styling
# ============================================================

def load_styles():
    """Load the central CircuitSnap stylesheet."""
    css_path = pathlib.Path(__file__).parent / "styles.css"
    try:
        with open(css_path, "r", encoding="utf-8") as file:
            css = file.read()

        st.html(f"<style>{css}</style>")

    except FileNotFoundError:
        st.warning(
            "CircuitSnap stylesheet could not be loaded."
        )


# ============================================================
# Header
# ============================================================

def render_header(show_reset=False):
    """Render the workspace identity with optional session reset."""
    if not show_reset:
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
        return False

    col_title, col_btn = st.columns([8.2, 1.8], vertical_alignment="center")
    with col_title:
        st.html(
            """
            <header class="cs-header" style="margin-bottom:0;border-bottom:none;padding-bottom:0;">
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
    with col_btn:
        return st.button("New Session", key="cs_new_session_btn", help="Clear conversation and reset workspace")


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

ACTIONS = [
    ("Identify a component", "Identify this component, read any visible part numbers or color bands, and explain its pinout and typical function."),
    ("Explain a circuit", "Explain how this circuit works, identify its main sub-circuits, and state the key governing formulas."),
    ("Debug my lab setup", "Debug this circuit setup: check breadboard wiring, identify potential faults, and suggest multimeter measurements."),
    ("Learn an ECE concept", "Explain the working principle, key derivations, and practical electronics applications of this concept: ")
]

QUICK_ACTIONS = {
    label: {"prompt": prompt}
    for label, prompt in ACTIONS
}


def render_quick_actions():
    st.markdown('<p class="cs-section-label">START WITH</p>', unsafe_allow_html=True)
    st.markdown('<p class="cs-section-hint">Use a photo for visual tasks, or start with an electronics question.</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    for i, (label, prompt_template) in enumerate(ACTIONS):
        target_col = col1 if i % 2 == 0 else col2
        with target_col:
            if st.button(label, key=f"quick_action_{i}", use_container_width=True):
                st.session_state["pending_prompt"] = prompt_template
                st.rerun()


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
# Chat composer
# ============================================================

def render_chat_composer(
    model_names,
    current_model,
    image_key="composer_image",
    input_key="composer_message",
):
    """Render the responsive bottom composer with dedicated model control."""

    with st.container(key="cs-composer-shell"):
        with st.form("chat_composer", clear_on_submit=False):
            col_upload, col_input, col_model, col_send = st.columns(
                [1, 6, 1.8, 1],
                vertical_alignment="center",
            )

            with col_upload:
                uploaded_file = st.file_uploader(
                    "Attach",
                    type=["png", "jpg", "jpeg", "webp"],
                    label_visibility="collapsed",
                    key=image_key,
                    help="Attach an electronics image",
                )

            with col_input:
                initial_value = st.session_state.pop("pending_prompt", "")
                if initial_value:
                    st.session_state.pop(input_key, None)

                user_input = st.text_input(
                    "Message",
                    value=initial_value,
                    placeholder="Ask about a component, circuit, or concept…",
                    label_visibility="collapsed",
                    key=input_key,
                )

            with col_model:
                render_model_selector(model_names, current_model)

            with col_send:
                submitted = st.form_submit_button(
                    "Send",
                    use_container_width=True,
                    help="Send message",
                )

    return (
        submitted,
        user_input,
        uploaded_file,
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

            actual_provider = str(
                metadata.get("provider") or "another provider"
            )
            actual_model = str(
                metadata.get("model_id") or ""
            )

            model_labels = {
                "gemini-3.8-flash": "Gemini 3.8 Flash",
                "gemini-3.7-flash": "Gemini 3.7 Flash",
                "qwen/qwen3.8-27b": "Qwen 3.8 27B",
            }

            model_label = model_labels.get(
                actual_model,
                actual_model,
            )

            if actual_provider == "Groq" and model_label:
                fallback_label = (
                    f"Used fallback · Groq {model_label}"
                )
            elif model_label:
                fallback_label = (
                    f"Used fallback · {model_label}"
                )
            else:
                fallback_label = (
                    f"Used fallback · {actual_provider}"
                )

            st.caption(
                html.escape(fallback_label)
            )
