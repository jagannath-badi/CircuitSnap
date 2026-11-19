
# CircuitSnap — Mark 85 Multi-Discipline Engineering OS 🔧

> AI-powered multi-discipline engineering command center and diagnostic assistant.

CircuitSnap (powered by the **Mark 85 Cognitive OS**) is a full-stack engineering assistant designed for Mathematics, Mechanics & Thermodynamics, Electronics & Communication (ECE), Civil, Chemical, and Computing workflows.

It combines **LLM-first RAG intelligence**, **deterministic symbolic/numerical solvers**, **voice interaction**, and **optical schematic/hardware inspection** in a single unified HUD:

**See → Derive → Verify → Master**

---

## ✨ Core Capabilities

### 🧠 Multi-Discipline Engineering Intelligence

Ask conceptual, analytical, or design questions across core engineering domains with automatic response adaptation:

- **Applied Mathematics**: Calculus, differential equations, linear algebra, Laplace & Z-transforms, and boundary-value derivations.
- **Mechanics & Thermodynamics**: Statics, dynamics, fluid mechanics, heat transfer, and structural equilibrium.
- **Computing & Digital Logic**: Algorithms, complexity analysis, computer architecture, subnetting, and digital systems.
- **Circuits & Systems**: Analog/digital electronics, network theorems, signals & systems, control loops, and hardware diagnostics.
- **Adaptive Output Modes**: `Auto`, `Simple`, `Exam Steps`, `GATE Trick`, and `Code`.

### 🔬 Optical Scope & Hardware Diagnostics

Upload schematics, circuit photos, breadboard layouts, free-body diagrams, or lab notes for evidence-graded visual analysis:

- Distinguishes strictly between **`CONFIRMED`** (directly visible/verified), **`LIKELY`** (reasonable engineering inference), and **`CANNOT CONFIRM`** (insufficient visual or measurement evidence).
- Never fabricates part numbers, pinouts, electrical continuity, or unverified datasheet ratings.

### ⚡ Deterministic Symbolic & Numerical Solvers

- **SymPy & NumPy Gate**: Explicit mathematical expressions and numerical physics inputs route directly to deterministic offline solvers for exact closed-form derivations and SI-unit verification.
- **Strict Expression Gate**: Conversational prose is blocked from entering symbolic math parsers, preventing variable-scrambling errors.

### 🎙️ Mark 85 Voice & Telemetry HUD

- **Voice Pipeline**: Faster-Whisper speech-to-text, `"Hey Jarvis"` wake-word detection, and Sonia Neural TTS with automatic Markdown/LaTeX speech sanitization.
- **Privacy Guard**: Switchable `Strict` (100% offline), `Guarded` (client-side PII/secret redaction), and `Relaxed` routing modes.

---

## 🤖 Available AI Models & Routing

CircuitSnap routes queries through an **LLM-First RAG Pipeline** backed by deterministic solvers and a gated SQLite BM25 Knowledge Vault:

| Engine / Model                                    | Provider / Runtime               | Vision | Role                                                      |
| :------------------------------------------------ | :------------------------------- | :----: | :-------------------------------------------------------- |
| **Gemini (`gemini-3.8-flash` / `3.1-flash-lite`)** | Google GenAI (Cloud)             |   ✅   | Primary multi-discipline reasoning & optical scope vision |
| **OpenJarvis (`qwen3:8b`)**               | Local OpenAI-Compatible Endpoint |   ❌   | Offline/local LLM fallback                                |
| **J.A.R.V.I.S. Deterministic Core**         | Local Python (SymPy / NumPy)     |   ❌   | Exact symbolic math, numerical physics & datasheet lookup |

---

## 🧩 System Architecture

```text
                       React + Vite HUD (frontend/)
      TopCommandBar │ AiCoreVisualizer │ DiagnosticFeed │ OpticalScope
                                   │
                            REST / SSE Stream
                                   │
                                   ▼
                      FastAPI Backend (backend/main.py)
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
     routers/chat.py       routers/analyze.py     routers/voice.py
            │                      │                      │
            └──────────────────────┼──────────────────────┘
                                   ▼
                jarvis_engine/orchestrator.py + engine.py
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
   Deterministic Solvers   Gated Knowledge Vault      providers.py
  (SymPy / NumPy / KB)    (BM25 RAG Context >= 6.0)   ┌────┴────┐
                                                      ▼         ▼
                                                   Gemini   OpenJarvis
```
