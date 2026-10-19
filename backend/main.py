import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import models
import providers
from backend.routers import analyze, chat
from backend.schemas import HealthResponse, ModelOption, ModelsResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="CircuitSnap API",
    description="API for CircuitSnap's electronics assistant.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Register routers
app.include_router(chat.router)
app.include_router(analyze.router)


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    default_name = models.get_default_model()
    config = models.get_model(default_name)

    return HealthResponse(
        status="healthy",
        models={
            "default": default_name,
            "model_id": config.get("model_id"),
            "provider": config.get("provider"),
        },
    )


@app.get("/api/models", response_model=ModelsResponse)
async def get_models() -> ModelsResponse:
    has_gemini = bool(providers._get_api_key("GEMINI_API_KEY"))
    has_groq = bool(providers._get_api_key("GROQ_API_KEY"))

    available: list[ModelOption] = [
        ModelOption(
            id="auto",
            label="Auto (Smart Router)",
            provider="auto",
            supports_vision=True,
        )
    ]

    if has_gemini:
        available.append(
            ModelOption(
                id="gemini-2.5-flash",
                label="Gemini 2.5 Flash",
                provider="gemini",
                supports_vision=True,
            )
        )

    if has_groq:
        available.append(
            ModelOption(
                id="llama-3.3-70b-versatile",
                label="Groq Llama 3.3 70B",
                provider="groq",
                supports_vision=False,
            )
        )

    return ModelsResponse(
        models=available,
        default_model="auto",
    )