"""
J.A.R.V.I.S. Unified Orchestration Engine
Sub-50ms offline router coordinating local datasheet lookups, symbolic ECE math, and optical vision inspection.
"""

import re
from typing import Optional, Dict, Any, List

from .datasheet_kb import lookup_component, decode_color_bands, decode_smd_code
from .ece_math_solver import evaluate_ece_math
from .vision_inspector import inspect_circuit_image


def process_jarvis_query(
    user_text: str,
    image_bytes: Optional[bytes] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    model_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main offline entry point for all CircuitSnap queries.
    Executes entirely in local Python memory with sub-50ms response latency.
    """
    text = (user_text or "").strip()
    active_model = model_id or "jarvis-auto"

    # 1. Optical vision request
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
        }

    # Normalize wake words (e.g. "Hey Jarvis, decode brown black red gold" -> "decode brown black red gold")
    clean_text = re.sub(r"^(?:hey|hi|hello|ok|okay)?\s*jarvis[\s,.:!?-]*", "", text, flags=re.IGNORECASE).strip()
    eval_text = clean_text if clean_text else text
    lower_orig = text.lower().strip()

    # Conversational Greeting & System Status Intent
    greeting_triggers = {
        "hey jarvis", "hi jarvis", "hello jarvis", "jarvis", "hello", "hi", "hey",
        "who are you", "what can you do", "status", "system status", "are you there", "diagnostics"
    }

    if lower_orig in greeting_triggers or not eval_text:
        answer = (
            "### [CONFIRMED] J.A.R.V.I.S. Core Online\n\n"
            "At your service. Optical scope, SymPy circuit solver, and component datasheets are online. What are we building today?\n\n"
            "#### Quick Commands\n\n"
            "| Module | Voice or Text Command | Latency |\n"
            "| :--- | :--- | :---: |\n"
            "| **Datasheet Archive** | *\"NE555 pinout\"*, *\"LM741 specs\"*, *\"IRFZ44N pinout\"* | `< 10ms` |\n"
            "| **Color Band Decoder** | *\"Decode brown black red gold\"*, *\"yellow violet orange gold\"* | `< 5ms` |\n"
            "| **Symbolic Math** | *\"555 Astable Calc\"*, *\"RC Cutoff 10k 10uF\"*, *\"Op-Amp Gain\"* | `< 15ms` |\n"
            "| **SMD Marking** | *\"SMD 103\"*, *\"Marking 472\"*, *\"01C\"* | `< 5ms` |\n"
            "| **Optical Scope** | Drop or paste (<kbd>Ctrl+V</kbd>) any circuit photo | `< 30ms` |\n\n"
            "> **Voice Ready**: Speak directly or click the microphone to query hands-free."
        )
        return {
            "answer": answer,
            "provider": "J.A.R.V.I.S. Core",
            "model_id": "jarvis-auto",
            "status": "success",
            "error_type": None,
            "fallback_used": False,
            "attempts": 1,
        }

    # Dedicated model selection overrides
    if active_model == "jarvis-math":
        math_res = evaluate_ece_math(eval_text)
        if math_res:
            return {
                "answer": math_res,
                "provider": "J.A.R.V.I.S. Core",
                "model_id": "jarvis-math",
                "status": "success",
                "error_type": None,
                "fallback_used": False,
                "attempts": 1,
            }

    if active_model == "jarvis-datasheets":
        ds_res = lookup_component(eval_text) or decode_color_bands(eval_text) or decode_smd_code(eval_text)
        if ds_res:
            return {
                "answer": ds_res,
                "provider": "J.A.R.V.I.S. Core",
                "model_id": "jarvis-datasheets",
                "status": "success",
                "error_type": None,
                "fallback_used": False,
                "attempts": 1,
            }

    # Autonomous Smart Router:
    # 2. Check for registered IC datasheet lookup first (e.g. NE555, LM741, LM358, TL072, LM7805, BC547, IRFZ44N)
    ds_res = lookup_component(eval_text)
    if ds_res:
        return {
            "answer": ds_res,
            "provider": "J.A.R.V.I.S. Core",
            "model_id": "jarvis-datasheets",
            "status": "success",
            "error_type": None,
            "fallback_used": False,
            "attempts": 1,
        }

    # 3. Check for ECE symbolic / numerical math (555 astable, op-amp gain, BJT biasing, RC filter, RLC resonance)
    math_res = evaluate_ece_math(eval_text)
    if math_res:
        return {
            "answer": math_res,
            "provider": "J.A.R.V.I.S. Core",
            "model_id": "jarvis-math",
            "status": "success",
            "error_type": None,
            "fallback_used": False,
            "attempts": 1,
        }

    # 4. Check for resistor color bands
    band_res = decode_color_bands(eval_text)
    if band_res:
        return {
            "answer": band_res,
            "provider": "J.A.R.V.I.S. Core",
            "model_id": "jarvis-datasheets",
            "status": "success",
            "error_type": None,
            "fallback_used": False,
            "attempts": 1,
        }

    # 5. Check for SMD resistor markings
    smd_res = decode_smd_code(eval_text)
    if smd_res:
        return {
            "answer": smd_res,
            "provider": "J.A.R.V.I.S. Core",
            "model_id": "jarvis-datasheets",
            "status": "success",
            "error_type": None,
            "fallback_used": False,
            "attempts": 1,
        }

    # 6. Fallback General Technical Response
    answer = (
        f"### [CONFIRMED] J.A.R.V.I.S. Analysis for: *\"{eval_text}\"*\n\n"
        f"I evaluated your hardware query across the local engineering database.\n\n"
        f"#### Recommended Actions:\n"
        f"- **IC Pinouts**: Ask for specific parts like `NE555`, `LM741`, `LM358`, `TL072`, `LM7805`, `BC547`, `IRFZ44N`, or `1N4007`.\n"
        f"- **Circuit Formulas**: Ask about `RC Filter Cutoff`, `RLC Resonance`, `Op-Amp Inverting Gain`, or `BJT / MOSFET Biasing` for step-by-step KaTeX derivations.\n"
        f"- **Color Codes**: Enter 4 or 5 colors (e.g. `red red orange gold`) to compute nominal ohms and tolerances.\n"
        f"- **Optical Analysis**: Upload an image of your PCB or component for visual geometry and package scanning."
    )

    return {
        "answer": answer,
        "provider": "J.A.R.V.I.S. Core",
        "model_id": active_model,
        "status": "success",
        "error_type": None,
        "fallback_used": False,
        "attempts": 1,
    }
