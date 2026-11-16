import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.database import init_db
from backend.routers import analyze, auth, chat, learn, vault, voice
from backend.schemas import HealthResponse, ModelOption, ModelsResponse


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


DEFAULT_MODEL_ROSTER: list[ModelOption] = [
    ModelOption(
        id="jarvis-auto",
        label="Auto (J.A.R.V.I.S. Smart Router)",
        provider="J.A.R.V.I.S. Core",
        specialty="Smart router across all engineering branches",
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
]


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        models={
            "default": "jarvis-auto",
            "model_id": "jarvis-auto",
            "provider": "J.A.R.V.I.S. Core",
        },
    )


@app.get("/api/models", response_model=ModelsResponse)
async def get_models() -> ModelsResponse:
    return ModelsResponse(
        models=DEFAULT_MODEL_ROSTER,
        default_model="jarvis-auto",
    )
