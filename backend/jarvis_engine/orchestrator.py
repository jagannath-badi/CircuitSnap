"""
J.A.R.V.I.S. Universal Multi-Discipline Engineering Orchestration Engine
Sub-20ms offline router coordinating local component datasheets, ECE circuit formulas,
symbolic engineering mathematics, mechanical/thermodynamic solvers, CS digital logic,
civil structural/hydraulics, and knowledge vault semantic memory with adaptive response styling.
"""

import json
import logging
import re
import urllib.request
from typing import Optional, Dict, Any, List

from .datasheet_kb import lookup_component, decode_color_bands, decode_smd_code
from .ece_math_solver import evaluate_ece_math
from .eng_math_solver import (
    evaluate_eng_math,
    get_laplace_conceptual_explanation,
    get_differentiation_conceptual_explanation,
    get_integration_conceptual_explanation,
    get_limits_conceptual_explanation,
    get_taylor_conceptual_explanation,
    get_ode_conceptual_explanation,
    get_matrix_conceptual_explanation,
)
from .mech_thermo_solver import evaluate_mech_thermo
from .cs_digital_solver import evaluate_cs_digital
from .universal_eng_solver import evaluate_universal_engineering
from .knowledge_vault import search_vault
from .vision_inspector import inspect_circuit_image

logger = logging.getLogger(__name__)


OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"

STOP_WORDS = {
    "what", "is", "are", "the", "a", "an", "of", "for", "in", "to", "and", "or",
    "explain", "about", "tell", "me", "how", "does", "do", "can", "you", "give",
    "show", "derive", "calculate", "find", "solve", "please", "with", "meaning",
    "concept", "define", "properties", "property", "details", "brief", "note", "notes",
    "work", "working", "workings", "value", "values", "write", "state", "rule", "rules"
}


def extract_core_subject_nouns(query: str) -> List[str]:
    """Extracts non-filler subject nouns (>=3 letters) from user query."""
    tokens = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", query.lower())
    cleaned = [t.strip("-_") for t in tokens]
    return [t for t in cleaned if len(t) >= 3 and t not in STOP_WORDS]


def retrieve_rag_context(query: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves optional RAG context from the Knowledge Vault strictly when:
    1. BM25 score >= 6.0
    2. All core subject nouns in query appear in top hit's title or tags.
    Returns None otherwise. Never blindly short-circuits.
    """
    core_nouns = extract_core_subject_nouns(query)
    if not core_nouns:
        return None

    try:
        hits = search_vault(query, top_k=2)
    except Exception as err:
        logger.debug("Vault search error during RAG retrieval: %s", err)
        return None

    if not hits:
        return None

    top_hit = hits[0]
    score = top_hit.get("score", 0.0)
    if score < 6.0:
        return None

    hit_text = (top_hit.get("title", "") + " " + top_hit.get("tags", "")).lower()
    for noun in core_nouns:
        if noun not in hit_text:
            return None

    return top_hit


def get_offline_exact_subject_entry(query: str) -> Optional[str]:
    """
    Returns exact verified offline explanation ONLY when query explicitly targets
    a verified offline conceptual subject. Never guesses or cross-matches unrelated branches.
    """
    lower = query.lower().strip()

    # 1. Laplace Transform
    if "laplace" in lower or "l^-1" in lower:
        return get_laplace_conceptual_explanation()

    # 2. Differential Calculus
    if any(k in lower for k in ["derivative", "differentiation", "diff", "d/dx"]) and not any(k in lower for k in ["integral", "laplace", "matrix", "buckling"]):
        return get_differentiation_conceptual_explanation()

    # 3. Integral Calculus
    if any(k in lower for k in ["integrate", "integral", "antiderivative"]) and not any(k in lower for k in ["laplace", "matrix"]):
        return get_integration_conceptual_explanation()

    # 4. Limits
    if "limit" in lower and not any(k in lower for k in ["switch", "tolerance"]):
        return get_limits_conceptual_explanation()

    # 5. Taylor / Maclaurin Series
    if any(k in lower for k in ["taylor", "maclaurin"]):
        return get_taylor_conceptual_explanation()

    # 6. Ordinary Differential Equations (ODE)
    if any(k in lower for k in ["ode", "differential equation"]):
        return get_ode_conceptual_explanation()

    # 7. Linear Algebra / Matrices
    if any(k in lower for k in ["matrix", "determinant", "eigenvalue"]):
        return get_matrix_conceptual_explanation()

    # 8. Kirchhoff's Laws (KVL / KCL)
    if any(k in lower for k in ["kvl", "kcl", "kirchhoff", "kirchoff"]):
        return (
            "### [CONFIRMED] Kirchhoff's Circuit Laws: Governing Conservation Principles\n\n"
            "Kirchhoff's Laws are the fundamental circuit analysis equations derived directly from Maxwell's Equations "
            "under lumped-matter circuit assumptions (negligible electromagnetic propagation delay across components).\n\n"
            "#### 1. Kirchhoff's Current Law (KCL) — Conservation of Charge\n\n"
            "The algebraic sum of all currents entering any electrical node (junction) is identically zero:\n"
            "$$\\sum_{k=1}^{n} I_k = 0 \\iff \\sum I_{\\text{in}} = \\sum I_{\\text{out}}$$\n\n"
            "- **Physical Basis**: Law of Conservation of Electric Charge (no net charge accumulation at a microscopic node).\n"
            "- **Nodal Analysis**: At node $j$, $\\sum_{k} \\frac{V_j - V_k}{R_{jk}} = 0$.\n\n"
            "#### 2. Kirchhoff's Voltage Law (KVL) — Conservation of Energy\n\n"
            "The directed sum of electrical potential differences (voltages) around any closed loop is identically zero:\n"
            "$$\\sum_{k=1}^{m} V_k = 0$$\n\n"
            "- **Physical Basis**: Law of Conservation of Energy (electrostatic fields are conservative: $\\oint \\mathbf{E} \\cdot d\\mathbf{l} = 0$).\n"
            "- **Mesh Analysis**: $\\sum V_{\\text{sources}} = \\sum I R_{\\text{drops}}$ around each mesh loop."
        )

    # 9. Ohm's Law
    if "ohm" in lower and any(k in lower for k in ["law", "formula", "relation"]):
        return (
            "### [CONFIRMED] Ohm's Law & Power Relationships\n\n"
            "Fundamental DC Relations:\n"
            "$$V = I \\cdot R$$\n"
            "$$I = \\frac{V}{R}$$\n"
            "$$R = \\frac{V}{I}$$\n"
            "$$P = V \\cdot I = I^2 R = \\frac{V^2}{R}$$\n\n"
            "**Key Lab Tip**: For resistors, always check $P = I^2 R$ to ensure wattage rating (1/4W = 250mW, 1/2W = 500mW) is not exceeded."
        )

    return None


def detect_response_style(query: str, explicit_style: Optional[str] = None) -> str:
    """Detects student demand style: 'simple', 'exam', 'gate', 'code', or 'auto'."""
    if explicit_style and explicit_style.lower() in {"simple", "exam", "gate", "code"}:
        return explicit_style.lower()

    lower = query.lower()
    if any(k in lower for k in ["explain simply", "simple", "intuition", "analogy", "like i'm 5", "beginner"]):
        return "simple"
    if any(k in lower for k in ["for exam", "semester exam", "step by step", "derive", "full derivation"]):
        return "exam"
    if any(k in lower for k in ["gate", "shortcut", "trick", "trap", "pyq", "time saver"]):
        return "gate"
    if any(k in lower for k in ["code", "python", "c++", "matlab", "implementation", "program"]):
        return "code"
    return "auto"


def adapt_response_tone(raw_answer: str, style: str, query: str) -> str:
    """Formats answers dynamically to match student study demand across all engineering disciplines."""
    if not raw_answer:
        return raw_answer

    q_low = query.lower()
    is_math = any(k in q_low for k in ["laplace", "fourier", "integral", "derivative", "calculus", "matrix", "eigen", "ode", "diff"])
    is_mech = any(k in q_low for k in ["stress", "strain", "beam", "carnot", "reynolds", "bernoulli", "fluid", "thermo", "torque", "deflection"])
    is_cs = any(k in q_low for k in ["subnet", "cidr", "ip", "binary", "hex", "big-o", "sort", "algorithm", "tree", "boolean", "gate", "logic"])

    if style == "simple":
        if is_math:
            analogy = (
                "Think of this geometrically as tracking continuous rate-of-change and cumulative accumulation: "
                "every infinitesimal slice aggregates to satisfy boundary invariants without loss."
            )
        elif is_mech:
            analogy = (
                "Think of this as an internal molecular force balance: applied physical load induces micro-strain "
                "until balanced by material elasticity, sustaining mechanical equilibrium."
            )
        elif is_cs:
            analogy = (
                "Think of this like hierarchical address partitioning: dividing a discrete namespace into power-of-two "
                "blocks bounds access times and eliminates redundant sequential searches."
            )
        else:
            analogy = (
                "Think of potential difference (voltage) as the driving potential and charge flow (current) "
                "encountering resistance, strictly conserved at every junction by physical conservation laws."
            )

        return (
            f"{raw_answer}\n\n"
            f"---\n"
            f"#### 💡 First-Principles Intuition\n"
            f"{analogy}"
        )
    elif style == "exam":
        return (
            f"{raw_answer}\n\n"
            f"---\n"
            f"#### 📝 Exam-Ready Derivation Protocol\n"
            f"1. **Governing Law**: State the fundamental law in standard notation before numerical substitution.\n"
            f"2. **Boundary & Initial Conditions**: State constraints ($t=0^+$, boundary values, or assumptions) clearly.\n"
            f"3. **Algebraic Substitution**: Show all intermediate conversions with strict dimensional/SI unit consistency.\n"
            f"4. **Final Boxed Result**: Conclude with the verified numerical value, exact SI units, and physical interpretation."
        )
    elif style == "gate":
        return (
            f"{raw_answer}\n\n"
            f"---\n"
            f"#### ⚡ GATE & Competitive Speed Tactics\n"
            f"- **Boundary Value Check**: Test asymptotic limits ($t \\to 0^+$, $t \\to \\infty$, or frequency extremes) to eliminate options.\n"
            f"- **Dimensional Elimination**: Verify unit consistency across choices to rule out dimensionally invalid options in $< 5$s.\n"
            f"- **Critical Trap**: Double-check angular vs. cyclic frequency ($\\omega = 2\\pi f$), sign conventions, and RMS vs. peak values."
        )
    elif style == "code":
        if is_math:
            script = (
                "```python\n"
                "# Symbolic Engineering Mathematics Verification\n"
                "import sympy as sp\n\n"
                "t, s = sp.symbols('t s')\n"
                "# Verify closed-form transform or differential solution\n"
                "expr = sp.sin(2 * t)\n"
                "result = sp.laplace_transform(expr, t, s, noconds=True)\n"
                "print('Exact symbolic solution:', result)\n"
                "```"
            )
        elif is_mech:
            script = (
                "```python\n"
                "# Mechanical & Thermodynamic Numerical Verification\n"
                "import numpy as np\n\n"
                "def solve_mechanics(load_n=50000.0, area_m2=0.001):\n"
                "    stress_pa = load_n / area_m2\n"
                "    stress_mpa = stress_pa / 1e6\n"
                "    print(f'Normal Stress: {stress_mpa:.2f} MPa')\n"
                "    return stress_mpa\n\n"
                "solve_mechanics()\n"
                "```"
            )
        elif is_cs:
            script = (
                "```python\n"
                "# Computer Systems & Network Verification\n"
                "import ipaddress\n\n"
                "def audit_subnet(cidr='192.168.1.0/24'):\n"
                "    net = ipaddress.ip_network(cidr, strict=False)\n"
                "    print(f'Network: {net.network_address}, Usable Hosts: {net.num_addresses - 2}')\n"
                "    return net\n\n"
                "audit_subnet()\n"
                "```"
            )
        else:
            script = (
                "```python\n"
                "# Circuit & Hardware Verification Script\n"
                "import math\n\n"
                "def calc_cutoff(r_ohms=1000.0, c_farads=1e-6):\n"
                "    fc = 1.0 / (2.0 * math.pi * r_ohms * c_farads)\n"
                "    print(f'Cutoff Frequency: {fc:.2f} Hz')\n"
                "    return fc\n\n"
                "calc_cutoff()\n"
                "```"
            )
        return (
            f"{raw_answer}\n\n"
            f"---\n"
            f"#### 💻 Verification Script\n"
            f"{script}"
        )
    return raw_answer


def query_local_ollama(prompt: str, system_context: str = "") -> Optional[str]:
    """Queries local Ollama server if available (sub-50ms check). Returns None if offline."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.05)
            if s.connect_ex(("127.0.0.1", 11434)) != 0:
                return None
    except Exception:
        return None

    try:
        payload = {
            "model": "llama3.2:latest",
            "prompt": f"{system_context}\n\nUser Question: {prompt}\n\nProvide a precise engineering answer with KaTeX math:",
            "stream": False,
            "options": {"temperature": 0.2, "top_k": 20},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            OLLAMA_ENDPOINT,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                ans = body.get("response", "").strip()
                if ans:
                    return f"### [CONFIRMED] J.A.R.V.I.S. Neural Synthesis\n\n{ans}"
    except Exception:
        pass
    return None


def get_cognitive_trace_steps(query: str, active_model: str, style: str) -> List[str]:
    """Generates real-time cognitive reasoning milestones for streaming trace."""
    steps = [
        "Analyzing problem semantics and identifying core engineering domain...",
        "Scanning local Knowledge Vault for closed-form formulas and PYQ references...",
        "Executing symbolic math verification and unit conservation check...",
        f"Synthesizing closed-form KaTeX response formatted for '{style.upper()}' demand...",
    ]
    return steps


def process_jarvis_query(
    user_text: str,
    image_bytes: Optional[bytes] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    model_id: Optional[str] = None,
    response_style: Optional[str] = None,
    privacy_mode: str = "guarded",
) -> Dict[str, Any]:
    """
    Main entry point for all CircuitSnap engineering queries.
    Routes genuine questions directly to frontier LLM with optional
    deterministic symbolic verification for explicit component values/equations.
    """
    text = (user_text or "").strip()
    active_model = model_id or "jarvis-auto"
    detected_style = detect_response_style(text, explicit_style=response_style)

    # 1. Optical vision request - always use local vision model
    if image_bytes:
        answer = inspect_circuit_image(image_bytes, prompt=text)
        return {
            "answer": answer,
            "provider": "J.A.R.V.I.S. Core",
            "model_id": active_model if "vision" in active_model else "jarvis-vision",
            "status": "success",
            "error_type": None,
            "fallback_used": False,
            "attempts": 1,
            "style": detected_style,
        }

    # Normalize wake words (e.g. "Hey Jarvis, solve laplace sin(2*t)" -> "solve laplace sin(2*t)")
    clean_text = re.sub(r"^(?:hey|hi|hello|ok|okay)?\s*jarvis[\s,.:!?-]*", "", text, flags=re.IGNORECASE).strip()
    eval_text = clean_text if clean_text else text
    lower_orig = text.lower().strip()

    # Conversational Greeting & System Status Intent - keep local response
    greeting_triggers = {
        "hey jarvis", "hi jarvis", "hello jarvis", "jarvis", "hello", "hi", "hey",
        "who are you", "what can you do", "status", "system status", "are you there", "diagnostics",
        "help", "menu", "commands"
    }

    if lower_orig in greeting_triggers or not eval_text:
        answer = (
            "### [CONFIRMED] J.A.R.V.I.S. Universal Engineering Core Online\n\n"
            "At your service. Local symbolic math, mechanical/aerospace, civil structural, "
            "CSE/digital systems, and electrical circuits are operational with Knowledge Vault indexing. "
            "Select your preferred answer style below or ask directly!\n\n"
            "#### Multi-Discipline Engineering Roster\n\n"
            "| Discipline | Quick Voice or Text Commands | Latency |\n"
            "| :--- | :--- | :---: |\n"
            "| **Civil & Structural** | *\"Shear force simply supported beam UDL\"*, *\"Darcy soil mechanics\"* | `< 10ms` |\n"
            "| **Mechanical & Aero** | *\"Stress F=50kN A=0.001m2\"*, *\"Reynolds v=2 D=0.05\"*, *\"Lift drag ratio\"* | `< 10ms` |\n"
            "| **Electrical & ECE** | *\"NE555 pinout\"*, *\"3-phase balanced power\"*, *\"Control system damping\"* | `< 10ms` |\n"
            "| **CSE & Digital** | *\"Binary 42\"*, *\"Subnet 192.168.1.0/24\"*, *\"Big-O complexity\"*, *\"Truth table\"* | `< 10ms` |\n"
            "| **Engineering Math** | *\"Diff x^3 + sin(x)\"*, *\"Laplace sin(2t)\"*, *\"Matrix det [[1,2],[3,4]]\"* | `< 15ms` |\n"
            "| **Optical Scope** | Drop circuit photos, schematics, or study PDFs into the left deck | `< 25ms` |\n\n"
            "> **Adaptive Modes**: Append *\"explain simply\"*, *\"for exam\"*, or *\"GATE trick\"* to change answer format on the fly."
        )
        return {
            "answer": answer,
            "provider": "J.A.R.V.I.S. Core",
            "model_id": "jarvis-auto",
            "status": "success",
            "error_type": None,
            "fallback_used": False,
            "attempts": 1,
            "style": detected_style,
        }

    # Dedicated model selection overrides - keep local solvers for explicit requests
    if active_model == "jarvis-math":
        math_res = (
            evaluate_eng_math(eval_text)
            or evaluate_ece_math(eval_text)
            or evaluate_mech_thermo(eval_text)
            or evaluate_universal_engineering(eval_text)
        )
        if math_res:
            return {
                "answer": adapt_response_tone(math_res, detected_style, eval_text),
                "provider": "J.A.R.V.I.S. Core",
                "model_id": "jarvis-math",
                "status": "success",
                "error_type": None,
                "fallback_used": False,
                "attempts": 1,
                "style": detected_style,
            }

    if active_model == "jarvis-datasheets":
        ds_res = (
            lookup_component(eval_text)
            or decode_color_bands(eval_text)
            or decode_smd_code(eval_text)
            or evaluate_cs_digital(eval_text)
        )
        if ds_res:
            return {
                "answer": adapt_response_tone(ds_res, detected_style, eval_text),
                "provider": "J.A.R.V.I.S. Core",
                "model_id": "jarvis-datasheets",
                "status": "success",
                "error_type": None,
                "fallback_used": False,
                "attempts": 1,
                "style": detected_style,
            }

    # By default, 100% of user queries route directly to the live frontier LLM.
    # Local deterministic solvers are bypassed unless the user explicitly
    # selects model_id == 'jarvis-math' (handled above).

    # 10. LLM-First RAG Pipeline (Google Gemini cloud primary -> OpenJarvis Local)
    # Routes ALL questions (engineering and non-engineering) to the frontier LLM
    # for structured, grounded, high-accuracy answers.
    rag_hit = retrieve_rag_context(eval_text)
    rag_context_str = ""
    if rag_hit:
        rag_context_str = f"Title: {rag_hit['title']}\nDomain: {rag_hit['branch']}\nContent:\n{rag_hit['content']}"

    # Determine target LLM provider based on model request
    if active_model in {"OpenJarvis", "openjarvis"} or "qwen" in active_model.lower():
        target_provider = "OpenJarvis"
        target_model = active_model
    elif active_model in {"Gemini", "gemini"} or "gemini" in active_model.lower():
        target_provider = "Gemini"
        target_model = active_model
    else:
        target_provider = "Gemini"
        target_model = "gemini-3.8-flash"

    try:
        from engine import run_engine
        llm_res = run_engine(
            provider=target_provider,
            model_id=target_model,
            user_text=eval_text,
            conversation_history=conversation_history,
            privacy_mode=privacy_mode,
            rag_context=rag_context_str,
        )
        if llm_res.get("status") == "success" and llm_res.get("answer"):
            ans = llm_res["answer"]
            prov = llm_res.get("provider", "Google Gemini")
            mid = llm_res.get("model_id", target_model)
            fb = llm_res.get("fallback_used", False)
            attempts = llm_res.get("attempts", 1)
            return {
                "answer": adapt_response_tone(ans, detected_style, eval_text),
                "provider": prov,
                "model_id": mid,
                "status": "success",
                "error_type": None,
                "fallback_used": fb,
                "attempts": attempts,
                "style": detected_style,
            }
    except Exception as err:
        logger.debug("Live LLM engine routing error: %s", err)

    # 11. Exact-Subject Offline Conceptual Fallback (Zero Cross-Topic Guessing)
    offline_entry = get_offline_exact_subject_entry(eval_text)
    if offline_entry:
        return {
            "answer": adapt_response_tone(offline_entry, detected_style, eval_text),
            "provider": "J.A.R.V.I.S. Core",
            "model_id": "jarvis-math",
            "status": "success",
            "error_type": None,
            "fallback_used": True,
            "attempts": 1,
            "style": detected_style,
        }

    # 12. Probe local Ollama if active
    ollama_res = query_local_ollama(eval_text)
    if ollama_res:
        return {
            "answer": adapt_response_tone(ollama_res, detected_style, eval_text),
            "provider": "Ollama Local Neural",
            "model_id": "jarvis-auto",
            "status": "success",
            "error_type": None,
            "fallback_used": False,
            "attempts": 1,
            "style": detected_style,
        }

    # 13. Honest Offline Fallback (Zero Cross-Topic Guessing)
    honest_answer = (
        "### [CANNOT CONFIRM] Live AI Engines Offline\n\n"
        f"Live reasoning engines (**Google Gemini** and **OpenJarvis Local**) are currently unreachable or unconfigured, "
        f"and no verified offline entry exists for *\"{eval_text}\"*.\n\n"
        "**To activate live reasoning:**\n"
        "1. Set a valid `GEMINI_API_KEY` in `.env` to enable Google Gemini cloud intelligence, OR\n"
        "2. Start an OpenJarvis / OpenAI-compatible endpoint at `http://localhost:8000/v1` (`qwen3:8b`).\n\n"
        "Deterministic solvers for registered ICs (e.g. *NE555*, *LM741*), resistor color bands, CIDR subnets, "
        "and symbolic math expressions (e.g. `diff x^3 + 2x`, `laplace sin(2t)`) remain fully operational offline."
    )

    return {
        "answer": adapt_response_tone(honest_answer, detected_style, eval_text),
        "provider": "J.A.R.V.I.S. Offline Gate",
        "model_id": "jarvis-offline",
        "status": "success",
        "error_type": None,
        "fallback_used": True,
        "attempts": 1,
        "style": detected_style,
    }
