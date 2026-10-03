# CircuitSnap — Model Registry
# Keeps provider/model information in one place.

MODELS = {
    # -------------------------
    # Google Gemini
    # -------------------------
    "Gemini 3.8 Flash": {
        "provider": "Gemini",
        "model_id": "gemini-3.8-flash",
        "vision": True,
        "reasoning": True,
        "status": "Recommended",
    },

    # -------------------------
    # Groq
    # -------------------------
    "Qwen 3.8 27B": {
        "provider": "Groq",
        "model_id": "qwen/qwen3.8-27b",
        "vision": True,
        "reasoning": True,
        "status": "Fast",
    },

    # -------------------------
    # Sarvam AI
    # -------------------------
    "Gemma 4": {
        "provider": "Sarvam",
        "model_id": "gemma4",
        "vision": True,
        "reasoning": False,
        "status": "Vision",
    },

    "GLM 5.3": {
        "provider": "Sarvam",
        "model_id": "glm5.3",
        "vision": False,
        "reasoning": True,
        "status": "Reasoning",
    },

    "DeepSeek V4 Flash": {
        "provider": "Sarvam",
        "model_id": "deepseekv4-flash",
        "vision": False,
        "reasoning": True,
        "status": "Reasoning",
    },

    "Sarvam 105B": {
        "provider": "Sarvam",
        "model_id": "sarvam-105b",
        "vision": False,
        "reasoning": False,
        "status": "General",
    },
}


def get_model(name):
    """Return configuration for a selected model."""
    return MODELS[name]


def get_vision_models():
    """Return models that support image input."""
    return {
        name: config
        for name, config in MODELS.items()
        if config["vision"]
    }


def get_text_models():
    """Return all models that can handle text."""
    return MODELS