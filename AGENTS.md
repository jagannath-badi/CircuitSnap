# CircuitSnap — AI Coding Agent Guidelines & Operating Manual

This document provides mandatory operational instructions, verified commands, architectural boundaries, and implementation patterns for AI coding agents working on the **CircuitSnap** codebase.

---

## 1. Project Architecture & Dual-Stack Preservation

CircuitSnap is an AI-powered electronics assistant for Electronics and Communication Engineering (ECE) students. The repository is actively executing a migration from a monolithic Streamlit application to a decoupled **FastAPI backend** and **React + TypeScript + Vite frontend** on branch `migration/fastapi-react`.

### Critical Invariance Rule
- **Preserve the Streamlit Application**: The legacy Streamlit application (`app.py`, `ui.py`, `styles.css`, `.streamlit/`) is operational and **must remain untouched and fully working**.
- **Shared Python Core**: The files `engine.py`, `models.py`, `prompts.py`, and `providers.py` constitute the shared reasoning and provider core used by **both** Streamlit and FastAPI. Any modifications to these files must maintain strict backward compatibility with both runtimes.

---

## 2. Project Directory Structure

```text
CircuitSnap/
├── app.py                      # Streamlit application entry point & session state
├── ui.py                       # Streamlit UI component rendering
├── styles.css                  # Streamlit CSS custom styling
├── engine.py                   # Shared intelligence orchestration & ECE workflow engine
├── models.py                   # Shared model registry (Gemini default, Groq)
├── prompts.py                  # Shared system prompt, adaptive calibration & prompt templates
├── providers.py                # Shared AI client layer (Google GenAI SDK, Groq SDK)
├── requirements.txt            # Python dependencies (Streamlit, google-genai, groq, pillow)
├── backend/                    # FastAPI Backend Application
│   ├── main.py                 # FastAPI app entry point, CORS middleware, /api/health
│   ├── schemas.py              # Pydantic v2 request & response models
│   └── routers/
│       ├── chat.py             # POST /api/chat router (multi-turn text chat)
│       └── analyze.py          # POST /api/analyze router (multipart image analysis)
├── frontend/                   # React + TypeScript + Vite Frontend Application
│   ├── index.html              # HTML shell
│   ├── package.json            # Scripts: dev, build, lint, preview
│   ├── vite.config.ts          # Vite config with React, Tailwind v4 plugin, and /api proxy
│   ├── tsconfig.json           # Project references config
│   ├── tsconfig.app.json       # App TypeScript configuration
│   └── src/
│       ├── main.tsx            # React root, index.css, and katex.min.css imports
│       ├── App.tsx             # Two-Column Workbench layout, DUT state, AST badge plugin
│       ├── TelemetryHeader.tsx # Pinned header with health LED, telemetry chips, bench reset
│       ├── api.ts              # Fetch client wrappers for health, chat, and analyze
│       ├── index.css           # Tailwind v4 import, custom scrollbars, KaTeX overrides
│       └── assets/             # Static graphics
└── docs/                       # Project documentation
    └── ARCHITECTURE.md         # Detailed architectural specification
```

---

## 3. Verified Development & Verification Commands

All agents must use the following exact commands for running and verifying the application:

### Python & Streamlit / FastAPI
- **Virtual Environment**: Located at `.\venv\` on Windows (`.\venv\Scripts\python.exe`).
- **Run Streamlit (Port 8501)**:
  ```powershell
  .\venv\Scripts\python.exe -m streamlit run app.py
  ```
- **Run FastAPI Backend (Port 8000)**:
  ```powershell
  .\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
  ```

### Frontend (React + Vite)
Run from the `frontend/` directory (`cd frontend` or set working directory):
- **Development Server (Port 5173)**:
  ```powershell
  npm run dev
  ```
- **Static Linter (`oxlint`)**:
  ```powershell
  npm run lint
  ```
- **TypeScript Typecheck & Production Build (`tsc -b && vite build`)**:
  ```powershell
  npm run build
  ```
- **Production Preview**:
  ```powershell
  npm run preview
  ```

---

## 4. Backend Endpoints, Schemas & Vite Proxy

### Vite Dev Proxy (`frontend/vite.config.ts`)
The Vite server (port `5173`) proxies all `/api` traffic directly to `http://127.0.0.1:8000` with `changeOrigin: true`. Frontend fetch calls must strictly use relative paths (`/api/health`, `/api/chat`, `/api/analyze`).

### FastAPI Endpoints (`backend/`)
1. **`GET /api/health`**
   - Returns: `HealthResponse` (`{ status: "healthy", models: { default: "Gemini", model_id: "gemini-3.8-flash", provider: "Gemini" } }`)
2. **`POST /api/chat`**
   - Accepts JSON `ChatRequest`:
     - `message`: `str` (1 to 20,000 characters, required)
     - `history`: `list[ChatMessage]` (`role`: `"user"` | `"assistant"`, `content`: `str`)
     - `provider`: `str | None`
     - `model_id`: `str | None`
     - `previous_visual_context`: `dict[str, Any] | None`
   - Returns `ChatResponse`:
     - `answer`: `str`
     - `provider`: `str`
     - `model_id`: `str`
     - `status`: `"success"` | `"error"`
     - `error_type`: `str | None`
     - `fallback_used`: `bool`
     - `attempts`: `int`
3. **`POST /api/analyze`**
   - Accepts `multipart/form-data`:
     - `file`: `UploadFile` (MIME types: `image/jpeg`, `image/png`, `image/webp`, `image/gif`; max 10 MB)
     - `prompt`: `str` (form field, default provided)
     - `provider`: `str | None`
     - `model_id`: `str | None`
   - Returns `ChatResponse`.

---

## 5. Security, Secrets & Provider Isolation

1. **Zero Secret Exposure**:
   - Never read, grep, log, or disclose `.env`, `.streamlit/secrets.toml`, or environment API keys.
   - Do NOT log raw authorization headers or credentials.
2. **Key Resolution Order**:
   - `providers._get_api_key(name)` checks `os.environ.get(name)` first, then falls back to `st.secrets[name]`.
   - In FastAPI mode, keys are read from the execution environment.
   - In Streamlit mode, keys are loaded from `.streamlit/secrets.toml` or environment.
3. **Provider Failover**:
   - `providers.py` and `engine.py` manage automatic provider and model fallback (e.g., Gemini primary failing over to Groq/Qwen, or model degradation). Agents must not circumvent or strip the fallback logic.

---

## 6. Frontend DUT State & Object URL Lifecycle

In `frontend/src/App.tsx`, image handling relies on two separate state tracks to ensure both persistent inspection and clean memory disposal:

1. **Draft Composer Attachment (`attachedFile`, `imagePreview`)**:
   - Represents the pending file attached to the input bar.
   - Cleared immediately upon sending a message (`removeAttachedFile()`) so subsequent follow-up text queries in the conversation do not re-upload the image payload.
2. **Persistent Active DUT (`activeDutImage`, `activeDutName`)**:
   - Represents the active **Device Under Test** mounted in the Left Optical Scope.
   - Pinned into state via `handleFileSelect(file)` (triggered by drop, file browse, or global clipboard paste <kbd>Ctrl+V</kbd>).
   - Persists in the Left Scope across multi-turn chat iterations even after `attachedFile` is cleared.
3. **Lifecycle & Cleanup Methods**:
   - **`activeObjectUrlsRef`**: A `useRef<Set<string>>(new Set())` tracking every generated `URL.createObjectURL(file)`.
   - **`removeAttachedFile()`**: Clears draft state; revokes `imagePreview` *only* if it does not match `activeDutImage`.
   - **`handleEjectDut()`**: Resets `activeDutImage` and `activeDutName` to `null` and returns the Left Scope to the standby reticle.
   - **`handleClearChat()` (Reset Bench)**: Revokes all URLs in `activeObjectUrlsRef`, clears messages, unmounts the active DUT, and resets error state.
   - **Unmount Hook**: An unmount `useEffect` revokes all active URLs in `activeObjectUrlsRef`.

---

## 7. Markdown, KaTeX & Single-Pill Badges

Before modifying formatting or rendering components in `frontend/src/App.tsx`, inspect the current pipeline:

### Unified Markdown Pipeline
```tsx
<ReactMarkdown
  remarkPlugins={[remarkMath]}
  rehypePlugins={[rehypeKatex, rehypeConfidenceBadges]}
  components={markdownComponents}
>
  {msg.content}
</ReactMarkdown>
```

### 1. Single-Pill Confidence Badges (`rehypeConfidenceBadges`)
- **AST-Level Processing**: Replaces confidence tokens directly inside HTML Abstract Syntax Tree (HAST) text nodes to prevent duplicate or triple-nested borders.
- **Tokens Caught**:
  - `CONFIRMED` (with optional `[]`, `:`, or `—`) $\rightarrow$ emerald badge (`bg-emerald-500/15 text-emerald-400 border border-emerald-500/30`).
  - `LIKELY` (with optional `[]`, `:`, or `—`) $\rightarrow$ amber badge (`bg-amber-500/15 text-amber-400 border border-amber-500/30`).
  - `CANNOT CONFIRM` (with optional `[]`, `:`, or `—`) $\rightarrow$ rose badge (`bg-rose-500/15 text-rose-400 border border-rose-500/30`).
- **Safety Boundaries**: Skips `<code>`, `<pre>`, and nodes containing `.katex` classes to prevent corrupting code snippets or formulas.
- **Rule**: Never reintroduce badge parsing into parent wrappers (`li`, `p`, `span`, `strong`).

### 2. KaTeX Math Notation
- **Dependencies**: `katex`, `remark-math`, `rehype-katex`, with stylesheet `katex/dist/katex.min.css` imported in `frontend/src/main.tsx`.
- **Supported Syntax**:
  - Inline math: `$f_c = \frac{1}{2\pi R C}$`
  - Display blocks: `$$A_v = -\frac{R_f}{R_{in}}$$`
- **Styling Overrides** (`frontend/src/index.css`):
  - `.katex-display`: Horizontally scrollable on small screens (`overflow-x: auto`), overflow-y hidden, with `padding: 0.35rem 0`.
  - `.katex`: Scaled to `1.05em` with `text-rendering: auto`.

---

## 8. Verification Protocol & Git Discipline

Before marking any task as complete:
1. **Lint Check**: Run `npm run lint` inside `frontend/` (0 warnings, 0 errors).
2. **Build Check**: Run `npm run build` inside `frontend/` (`tsc -b && vite build` exit code 0).
3. **Git Diff Review**: Check `git status` and `git diff` to ensure no unexpected or destructive changes were made.
4. **Git Authorization Rule**: **Never** run `git commit`, `git push`, `git reset`, or `git checkout --` without explicit user instruction.

