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
from backend.database import init_db
from backend.routers import analyze, auth, chat, vault
from backend.schemas import HealthResponse, ModelOption, ModelsResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
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
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Register routers
app.include_router(chat.router)
app.include_router(analyze.router)
app.include_router(auth.router)
app.include_router(vault.router)


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
    has_groq = bool(providers._get_api_key("GROQ_API_KEY"))

    available: list[ModelOption] = [
        ModelOption(
            id="auto",
            label="Auto (Smart Router)",
            provider="auto",
            specialty="Autonomous Task Routing",
            supports_vision=True,
        ),
        ModelOption(
            id="gemini-3.8-flash",
            label="Gemini 3.8 Flash (Active Default)",
            provider="gemini",
            specialty="Optical Scope & General Telemetry",
            supports_vision=True,
        ),
        ModelOption(
            id="gemini-3.6-flash",
            label="Gemini 3.6 Flash (Circuit Math)",
            provider="gemini",
            specialty="Circuit Math & Formula Derivations",
            supports_vision=True,
        ),
        ModelOption(
            id="gemini-2.5-flash",
            label="Gemini 2.5 Flash (Primary Workhorse)",
            provider="gemini",
            specialty="Precision IC & SMD Marking Recognition",
            supports_vision=True,
        ),
    ]

    if has_groq:
        available.append(
            ModelOption(
                id="llama-3.3-70b-versatile",
                label="Groq Llama 3.3 70B",
                provider="groq",
                specialty="Sub-Second Pinout & Quick Lookups",
                supports_vision=False,
            )
        )

    available.extend([
        ModelOption(
            id="gemini-2.0-flash-thinking-exp",
            label="Gemini 2.0 Thinking (Experimental)",
            provider="gemini",
            specialty="Formula Derivations (Auto Fallback Protected)",
            supports_vision=True,
        ),
        ModelOption(
            id="gemini-1.5-pro",
            label="Gemini 1.5 Pro",
            provider="gemini",
            specialty="Deep Datasheets & Dense Schematics",
            supports_vision=True,
        ),
        ModelOption(
            id="gemini-1.5-flash",
            label="Gemini 1.5 Flash",
            provider="gemini",
            specialty="High-Throughput Quota Fallback",
            supports_vision=True,
        ),
        ModelOption(
            id="gemini-1.5-flash-8b",
            label="Gemini 1.5 Flash-8B",
            provider="gemini",
            specialty="Ultra-Lightweight Verification",
            supports_vision=True,
        ),
    ])

    return ModelsResponse(
        models=available,
        default_model="gemini-3.8-flash",
    )