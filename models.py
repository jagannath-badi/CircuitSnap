"""
CircuitSnap — Model Registry

Keeps user-facing model choices and provider configuration
in one place.

This file does not communicate with any AI provider.
"""

# -------------------------------------------------------------------
# Available models
# -------------------------------------------------------------------

MODELS = {
    "Gemini": {
    "provider": "Gemini",
    "model_id": "gemini-3.8-flash",
    "fallback_models": [
        "gemini-3.6-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
    ],
    "fallback_provider": "Groq",
    "vision": True,
    "reasoning": True,
    "status": "Recommended",
},

    "Groq": {
        "provider": "Groq",
        "model_id": "qwen/qwen3.8-27b",
        "fallback_provider": "Gemini",
        "vision": True,
        "reasoning": True,
        "status": "Fast",
    },
}


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def get_model(name: str) -> dict:
    """
    Return the configuration for a selected model.

    Example:
        get_model("Gemini")
    """

    if name not in MODELS:
        raise ValueError(f"Unsupported model: {name}")

    return MODELS[name]


def get_model_names() -> list[str]:
    """Return the names shown to the user in the model selector."""

    return list(MODELS.keys())


def get_default_model() -> str:
    """Return the default model used when CircuitSnap starts."""

    return "Gemini"
