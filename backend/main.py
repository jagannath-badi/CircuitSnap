import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from providers import (
    OPENJARVIS_BASE_URL,
    OPENJARVIS_MODEL,
    is_openjarvis_available,
    load_dotenv,
)

# Ensure .env is loaded before router initialization
load_dotenv(override=True)

from backend.database import init_db
from backend.routers import analyze, auth, chat, learn, operations, telemetry, vault, voice
from backend.schemas import HealthResponse, ModelOption, ModelsResponse
from models import get_default_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="CircuitSnap J.A.R.V.I.S. API",
    description="Sub-50ms offline intelligence API for CircuitSnap's ECE workstation.",
    version="2.0.0",
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
app.include_router(voice.router)
app.include_router(learn.router)
app.include_router(telemetry.router)
app.include_router(operations.router)


DEFAULT_MODEL_ROSTER: list[ModelOption] = [
    ModelOption(
        id="jarvis-auto",
        label="Auto (J.A.R.V.I.S. Smart Router)",
        provider="J.A.R.V.I.S. Core",
        specialty="Smart router across all engineering branches",
        supports_vision=True,
    ),
    ModelOption(
        id="gemini-3.8-flash",
        label="Google Gemini 3.8 Flash",
        provider="Google Gemini",
        specialty="Fast multimodal cloud reasoning & KaTeX synthesis",
        supports_vision=True,
    ),
    ModelOption(
        id="gemini-3.1-flash-lite",
        label="Google Gemini 3.1 Flash Lite",
        provider="Google Gemini",
        specialty="Deep analytical derivations, complex circuits & proofs",
        supports_vision=True,
    ),
    ModelOption(
        id="jarvis-math",
        label="J.A.R.V.I.S. Math Engine",
        provider="J.A.R.V.I.S. Core",
        specialty="Symbolic calculus, Laplace, circuits & mechanics math",
        supports_vision=False,
    ),
    ModelOption(
        id="jarvis-vision",
        label="J.A.R.V.I.S. Optical Vision",
        provider="J.A.R.V.I.S. Core",
        specialty="Scan diagrams, circuits, lab setups & handwritten notes",
        supports_vision=True,
    ),
    ModelOption(
        id="jarvis-datasheets",
        label="J.A.R.V.I.S. Datasheet Archive",
        provider="J.A.R.V.I.S. Core",
        specialty="IC pinouts, Big-O tables, material & thermo constants",
        supports_vision=False,
    ),
    ModelOption(
        id="openjarvis-qwen3:8b",
        label="OpenJarvis Local (qwen3:8b)",
        provider="OpenJarvis",
        specialty="Local private neural inference with zero cloud telemetry",
        supports_vision=False,
    ),
]


@app.get("/api/health", response_model=HealthResponse)
def health_check():
    oj_status = {
        "available": is_openjarvis_available(),
        "base_url": OPENJARVIS_BASE_URL,
        "model": OPENJARVIS_MODEL,
    }
    return HealthResponse(
        status="healthy",
        models={
            "default": "Gemini",
            "model_id": get_default_model(),
            "provider": "J.A.R.V.I.S. Core",
            "openjarvis_local": oj_status,
        },
    )


@app.get("/api/models", response_model=ModelsResponse)
def get_models() -> ModelsResponse:
    oj_status = {
        "available": is_openjarvis_available(),
        "base_url": OPENJARVIS_BASE_URL,
        "model": OPENJARVIS_MODEL,
    }
    models = list(DEFAULT_MODEL_ROSTER)
    if is_openjarvis_available():
        models.insert(
            1,
            ModelOption(
                id=f"openjarvis-{OPENJARVIS_MODEL}",
                label=f"OpenJarvis Local ({OPENJARVIS_MODEL})",
                provider="OpenJarvis",
                specialty="Local private neural inference with zero cloud telemetry",
                supports_vision=False,
            ),
        )
    return ModelsResponse(
        models=models,
        default_model="jarvis-auto",
        openjarvis_local=oj_status,
    )


@app.get("/api/skills")
def get_skills():
    from backend.skill_loader import list_loaded_skills
    skills = list_loaded_skills()
    return {"skills": skills, "count": len(skills)}
