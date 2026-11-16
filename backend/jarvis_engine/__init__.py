"""
J.A.R.V.I.S. Local Intelligence Engine for CircuitSnap
Sub-20ms offline multi-discipline engineering cognitive architecture.
"""

from .orchestrator import process_jarvis_query, get_cognitive_trace_steps, detect_response_style
from .eng_math_solver import evaluate_eng_math
from .mech_thermo_solver import evaluate_mech_thermo
from .cs_digital_solver import evaluate_cs_digital
from .universal_eng_solver import evaluate_universal_engineering
from .ece_math_solver import evaluate_ece_math
from .datasheet_kb import lookup_component, decode_color_bands, decode_smd_code
from .vision_inspector import inspect_circuit_image
from .knowledge_vault import search_vault, ingest_document, ingest_user_taught_concept, get_vault_stats

__all__ = [
    "process_jarvis_query",
    "get_cognitive_trace_steps",
    "detect_response_style",
    "evaluate_eng_math",
    "evaluate_mech_thermo",
    "evaluate_cs_digital",
    "evaluate_universal_engineering",
    "evaluate_ece_math",
    "lookup_component",
    "decode_color_bands",
    "decode_smd_code",
    "inspect_circuit_image",
    "search_vault",
    "ingest_document",
    "ingest_user_taught_concept",
    "get_vault_stats",
]
