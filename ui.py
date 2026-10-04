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

def render_header(model_name=None):
    """
    Render the responsive CircuitSnap header.

    Desktop:
        logo + branding              model status

    Mobile:
        compact logo + branding       status dot
    """

    safe_model = html.escape(
        str(model_name)
    ) if model_name else ""

    status_html = ""

    if safe_model:
        status_html = f"""
        <div class="cs-status">
            <span class="cs-status-dot"></span>
            <span>{safe_model}</span>
        </div>
        """

    st.html(
        f"""
        <header class="cs-header">

            <div class="cs-header-left">

                <div class="cs-logo">
                    🔧
                </div>

                <div>
                    <div class="cs-header-title">
                        CircuitSnap
                    </div>

                    <div class="cs-header-subtitle">
                        AI electronics assistant for ECE students
                    </div>
                </div>

            </div>

            {status_html}

        </header>
        """
    )


# ============================================================
# Hero
# ============================================================

def render_hero():
    """Render the main empty-state hero."""

    st.html(
        """
        <section class="cs-hero">

            <div class="cs-hero-icon">
                ⚡
            </div>

            <h1 class="cs-hero-title">
                Understand electronics.
            </h1>

            <p class="cs-hero-text">
                Upload a component, circuit, schematic, or lab setup —
                or simply ask an electronics question.
            </p>

        </section>
        """
    )


# ============================================================
# Quick actions
# ============================================================

QUICK_ACTIONS = {
    "Identify a component": {
        "icon": "🔍",
        "prompt": (
            "Identify the main electronic component in this image. "
            "Explain what it does and mention anything important "
            "that can or cannot be confirmed."
        ),
    },

    "Explain a circuit": {
        "icon": "🔌",
        "prompt": (
            "Analyze this circuit and explain its main function "
            "and how the visible components work together. "
            "Only describe connections that can be supported by "
            "the image."
        ),
    },

    "Debug my lab setup": {
        "icon": "🧪",
        "prompt": (
            "Analyze this electronics lab setup and identify "
            "any clearly visible connection or component issues. "
            "Separate confirmed observations from uncertain ones."
        ),
    },

    "Learn an ECE concept": {
        "icon": "🧠",
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
                f"{action['icon']}  {title}",
                key=f"quick_action_{index}",
                use_container_width=True,
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
        key="model_selector",
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

def render_chat_composer(model_names, current_model):
    """Render the main CircuitSnap chat composer."""

    try:
        default_index = model_names.index(current_model)
    except ValueError:
        default_index = 0

    with st.form("chat_composer", clear_on_submit=True):

        col_upload, col_message, col_model, col_send = st.columns(
            [0.9, 6.8, 1.5, 0.8],
            vertical_alignment="center",
        )

        with col_upload:
            uploaded_file = st.file_uploader(
                "Upload",
                type=["png", "jpg", "jpeg", "webp"],
                label_visibility="collapsed",
                key="composer_image",
            )

        with col_message:
            user_input = st.text_input(
                "Message",
                placeholder="Ask CircuitSnap anything about electronics...",
                label_visibility="collapsed",
            )

        with col_model:
            selected_model = st.selectbox(
                "Model",
                options=model_names,
                index=default_index,
                label_visibility="collapsed",
                key="composer_model",
            )

        with col_send:
            submitted = st.form_submit_button(
                "↑",
                use_container_width=True,
            )

    return (
        submitted,
        user_input,
        uploaded_file,
        selected_model,
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
        use_container_width=True,
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