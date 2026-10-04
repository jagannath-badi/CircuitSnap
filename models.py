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
        "gemini-3.7-flash",
    ],
    "fallback_provider": "Groq",
    "vision": True,
    "reasoning": True,
    "status": "Recommended",
},

    "Groq": {
        "provider": "Groq",
        "model_id": "qwen/qwen3.8-27b",
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


def get_vision_models() -> dict:
    """Return models that support image input."""

    return {
        name: config
        for name, config in MODELS.items()
        if config["vision"]
    }


def get_default_model() -> str:
    """Return the default model used when CircuitSnap starts."""

    return "Gemini"
