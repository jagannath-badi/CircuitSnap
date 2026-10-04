"""
CircuitSnap — Intelligence Engine

This is the backend orchestration layer between the UI and AI providers.

The frontend should remain simple.

The engine decides:
    1. What the user is trying to do
    2. What kind of electronics input is involved
    3. Which ECE workflow applies
    4. What evidence/accuracy rules are important
    5. How much technical depth is appropriate
    6. How the selected AI provider should answer

The engine does NOT communicate with Streamlit UI directly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# Supported CircuitSnap concepts
# ============================================================

INPUT_TYPES = {
    "component",
    "circuit_diagram",
    "physical_circuit",
    "electronics_document",
    "unknown",
}


INTENTS = {
    "identify",
    "explain",
    "test",
    "troubleshoot",
    "lab",
    "viva",
    "exam",
    "calculate",
    "compare",
    "summarize",
    "general",
}


WORKFLOWS = {
    "component_identification",
    "component_testing",
    "circuit_analysis",
    "circuit_troubleshooting",
    "concept_learning",
    "lab_assistance",
    "viva_preparation",
    "exam_answer",
    "calculation",
    "comparison",
    "summary",
    "general_electronics",
}


# ============================================================
# Request context
# ============================================================

@dataclass
class RequestContext:
    """
    Internal representation of what CircuitSnap believes
    the current request is about.

    This object is provider-independent.
    """

    user_text: str = ""

    has_image: bool = False

    input_type: str = "unknown"

    intent: str = "general"

    workflow: str = "general_electronics"

    detail_level: str = "normal"

    image_context: str = ""

    conversation_context: str = ""

    evidence_rules: list[str] = field(default_factory=list)


# ============================================================
# Intent detection
# ============================================================

EXAM_MARK_PATTERN = re.compile(r"\b(?:5|10)(?:\s*-\s*|\s+)marks?\b")


def has_exam_mark_request(text: str) -> bool:
    """Recognize 5- or 10-mark exam wording without matching measurements."""

    for match in EXAM_MARK_PATTERN.finditer(text):
        # In phrases such as "5 marks of voltage drop", marks describes a
        # measurement context rather than the requested answer length.
        if re.match(r"\s+of\b", text[match.end():]):
            continue
        return True

    return False


def detect_intent(user_text: str) -> str:
    """
    Detect the user's likely task from their wording.

    This is intentionally lightweight.

    We do not want a separate AI classification request just
    to determine intent.
    """

    text = " ".join(user_text.lower().split())

    if not text:
        return "general"

    def matches_any(terms):
        return any(
            re.search(rf"\b{re.escape(term.strip())}\b", text)
            for term in terms
        )

    # --------------------------------------------------------
    # Exam
    # --------------------------------------------------------

    exam_terms = (
        "exam",
        "write in exam",
        "exam answer",
        "short note",
        "long answer",
        "define and explain",
        "advantages and applications",
    )

    if matches_any(exam_terms) or has_exam_mark_request(text):
        return "exam"

    # --------------------------------------------------------
    # Viva
    # --------------------------------------------------------

    viva_terms = (
        "viva",
        "viva questions",
        "oral questions",
        "what can they ask",
        "questions examiner",
    )

    if matches_any(viva_terms):
        return "viva"

    # --------------------------------------------------------
    # Lab
    # --------------------------------------------------------

    lab_terms = (
        "lab",
        "laboratory",
        "experiment",
        "procedure",
        "aim",
        "observation",
        "precautions",
        "conclusion",
        "lab record",
    )

    if matches_any(lab_terms):
        return "lab"

    # --------------------------------------------------------
    # Troubleshooting
    # --------------------------------------------------------

    troubleshooting_terms = (
        "debug",
        "debugging",
        "not working",
        "doesn't work",
        "doesnt work",
        "not turning on",
        "wrong",
        "fault",
        "faulty",
        "problem",
        "issue",
        "troubleshoot",
        "why isn't",
        "why isnt",
    )

    if matches_any(troubleshooting_terms):
        return "troubleshoot"

    # --------------------------------------------------------
    # Testing
    # --------------------------------------------------------

    testing_terms = (
        "test",
        "testing",
        "multimeter",
        "check whether",
        "check if",
        "measure",
        "measurement",
        "how do i check",
    )

    if matches_any(testing_terms):
        return "test"

    # --------------------------------------------------------
    # Calculation
    # --------------------------------------------------------

    calculation_terms = (
        "calculate",
        "calculation",
        "solve",
        "find the value",
        "find current",
        "find voltage",
        "find resistance",
        "derive",
        "numerical",
    )

    if matches_any(calculation_terms):
        return "calculate"

    # --------------------------------------------------------
    # Comparison
    # --------------------------------------------------------

    comparison_terms = (
        "difference between",
        "compare",
        "comparison",
        "vs ",
        "versus",
        "which is better",
    )

    if matches_any(comparison_terms):
        return "compare"

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary_terms = (
        "summarize",
        "summary",
        "summarise",
        "revision",
        "revise",
        "important points",
    )

    if matches_any(summary_terms):
        return "summarize"

    # --------------------------------------------------------
    # Identification
    # --------------------------------------------------------

    identification_terms = (
        "what is this",
        "what is that",
        "identify",
        "identify this",
        "which component",
        "what component",
        "name this",
        "name the component",
    )

    if matches_any(identification_terms):
        return "identify"

    # --------------------------------------------------------
    # Explanation
    # --------------------------------------------------------

    explain_terms = (
    "explain",
    "explanation",
    "how does",
    "how do",
    "why does",
    "why is",
    "what is ",
    "what are ",
    "define ",
    "meaning of",
)

    if matches_any(explain_terms):
        return "explain"

    return "general"


# ============================================================
# Image context reuse
# ============================================================

IMAGE_CONTEXT_REFERENCE_PATTERNS = (
    r"\b(?:this|that|these|those|it|its|they|them)\b",
    r"\b(?:the|my)\s+(?:image|photo|picture|component|circuit|schematic|board|setup|resistor|capacitor|diode|transistor|sensor|ic)\b",
    r"\b(?:shown|pictured|visible|in the (?:image|photo|picture))\b",
    r"\b(?:pin|terminal)(?:\s+number)?\s+\w+\b",
    r"\b(?:the|its|this|that)\s+(?:value|marking|label|part number|color code)\b",
    r"\bwhat about\b",
)


def references_previous_image(user_text: str) -> bool:
    """Return whether the request explicitly refers to prior visual context."""

    text = " ".join(user_text.lower().split())

    return any(
        re.search(pattern, text)
        for pattern in IMAGE_CONTEXT_REFERENCE_PATTERNS
    )


def select_request_image_context(
    *,
    user_text: str,
    current_image_bytes: Optional[bytes] = None,
    current_mime_type: Optional[str] = None,
    previous_image_context: Optional[dict] = None,
) -> tuple[Optional[bytes], Optional[str]]:
    """Choose a new upload or an explicitly referenced previous image."""

    if current_image_bytes is not None:
        return current_image_bytes, current_mime_type

    if (
        previous_image_context
        and references_previous_image(user_text)
    ):
        return (
            previous_image_context.get("image_bytes"),
            previous_image_context.get("mime_type"),
        )

    return None, None


# ============================================================
# Input classification hints
# ============================================================

def infer_input_type_hint(
    user_text: str,
    has_image: bool,
) -> str:
    """
    Produce a conservative input-type hint.

    For images, the AI provider performs the final visual
    classification.

    This function only provides useful textual hints.
    """

    if not has_image:
        return "unknown"

    text = user_text.lower()

    if any(
        term in text
        for term in (
            "breadboard",
            "wiring",
            "wire",
            "connection",
            "pcb",
            "setup",
            "circuit",
        )
    ):
        return "physical_circuit"

    if any(
        term in text
        for term in (
            "schematic",
            "circuit diagram",
            "circuit diagram",
            "symbol",
            "diagram",
        )
    ):
        return "circuit_diagram"

    if any(
        term in text
        for term in (
            "datasheet",
            "lab sheet",
            "question paper",
            "document",
            "notes",
        )
    ):
        return "electronics_document"

    if any(
        term in text
        for term in (
            "component",
            "resistor",
            "capacitor",
            "diode",
            "transistor",
            "ic",
            "sensor",
        )
    ):
        return "component"

    return "unknown"


# ============================================================
# Workflow selection
# ============================================================

def select_workflow(
    intent: str,
    input_type: str,
) -> str:
    """
    Combine user intent and input type into an ECE workflow.
    """

    if intent == "test":
        return "component_testing"

    if intent == "troubleshoot":
        return "circuit_troubleshooting"

    if intent == "lab":
        return "lab_assistance"

    if intent == "viva":
        return "viva_preparation"

    if intent == "exam":
        return "exam_answer"

    if intent == "calculate":
        return "calculation"

    if intent == "compare":
        return "comparison"

    if intent == "summarize":
        return "summary"

    if intent == "identify":
        return "component_identification"

    if intent == "explain":
        if input_type in {
            "circuit_diagram",
            "physical_circuit",
        }:
            return "circuit_analysis"

        return "concept_learning"

    if input_type == "component":
        return "component_identification"

    if input_type in {
        "circuit_diagram",
        "physical_circuit",
    }:
        return "circuit_analysis"

    return "general_electronics"


# ============================================================
# Contextual follow-up routing
# ============================================================

CONTEXTUAL_FOLLOW_UP_PATTERNS = (
    r"\b(?:go|dig)\s+deeper\b",
    r"\b(?:give|add|provide)\s+(?:me\s+)?(?:some\s+)?(?:more|further)\s+detail\b",
    r"\bmore\s+(?:technical\s+)?detail\b",
    r"\b(?:what about|and what about)\b",
    r"\b(?:in more detail|in more depth)\b",
    r"\b(?:explain|describe)\s+(?:it|that)\s+(?:more\s+)?(?:technically|mathematically)\b",
    r"\bexplain\s+this\s+(?:technically|mathematically)\b",
)


def is_contextual_follow_up(user_text: str) -> bool:
    """Return whether the wording clearly asks to continue a prior topic."""

    text = " ".join(user_text.casefold().split())
    return any(
        re.search(pattern, text)
        for pattern in CONTEXTUAL_FOLLOW_UP_PATTERNS
    )


def infer_previous_workflow(
    conversation_history: Optional[list[dict]],
) -> Optional[str]:
    """Find the most recent substantive user request's workflow."""

    for message in reversed(conversation_history or []):
        if message.get("role") != "user":
            continue

        previous_text = str(message.get("content", "")).strip()
        if not previous_text:
            continue

        previous_intent = detect_intent(previous_text)
        if previous_intent == "general":
            # Continue across earlier generic follow-ups, but stop at an
            # unrelated general request so stale topics are not inherited.
            if is_contextual_follow_up(previous_text):
                continue
            return None

        previous_input_type = infer_input_type_hint(
            user_text=previous_text,
            has_image=True,
        )
        return select_workflow(
            intent=previous_intent,
            input_type=previous_input_type,
        )

    return None


# ============================================================
# Detail level
# ============================================================

def determine_detail_level(user_text: str) -> str:
    """
    Estimate the requested depth without forcing an arbitrary
    word limit.
    """

    text = " ".join(user_text.casefold().split())

    depth_phrases = (
        "technical",
        "technically",
        "technical explanation",
        "technical detail",
        "technical details",
        "detailed",
        "in detail",
        "in depth",
        "in-depth",
        "deep",
        "deeply",
        "deeper",
        "deep dive",
        "advanced",
        "comprehensive",
        "thorough",
        "step by step",
        "step-by-step",
        "everything about",
    )

    if any(
        re.search(rf"\b{re.escape(phrase)}\b", text)
        for phrase in depth_phrases
    ):
        return "detailed"

    if any(
        phrase in text
        for phrase in (
            "briefly",
            "in short",
            "short answer",
            "one line",
            "simple answer",
        )
    ):
        return "concise"

    if any(
        phrase in text
        for phrase in (
            "exam answer",
            "exam",
        )
    ) or has_exam_mark_request(text):
        return "exam"

    return "normal"


# ============================================================
# Evidence rules
# ============================================================

def build_evidence_rules(
    has_image: bool,
) -> list[str]:
    """
    Return the evidence rules relevant to the request.
    """

    if not has_image:
        return [
            "Use established electronics knowledge.",
            "State assumptions when solving numerical problems.",
            "Do not invent measurements or experimental observations.",
        ]

    return [
        "Separate visible evidence from inference.",
        "For relevant image-derived factual claims, explicitly label them CONFIRMED, LIKELY, or CANNOT CONFIRM.",
        "Use CONFIRMED only when markings or color bands and their order are clear; use LIKELY when a candidate is supported but moderately uncertain.",
        "If low resolution, blur, occlusion, or uncertain band count/order prevents a reliable resistor decode, use CANNOT CONFIRM, request a clearer close-up, and do not force a single value.",
        "Use CANNOT CONFIRM for facts that require a measurement, datasheet, or information not visible in the image.",
        "Label uncertain image-derived claims with the explicit uppercase LIKELY label; lowercase 'likely' is not a substitute and uncertain claims must not appear under a CONFIRMED heading.",
        "Apply confidence labels only to image-derived claims, not unrelated technical background.",
        "Never invent a standards name or number, organization, certification, citation, datasheet reference, or other source designation; include one only if explicitly provided in the request/context or known with high confidence and directly relevant.",
        "For resistor color-band analysis, describe the observed bands and decoded nominal value or tolerance; do not add a standards citation unless the user explicitly asks for one.",
        "Do not treat a standards/reference claim in an earlier assistant message as verification.",
        "Do not invent exact part numbers, values, pinouts, ratings, or datasheet specifications.",
        "Do not assume electrical continuity from physical proximity.",
        "Do not claim a circuit is electrically correct unless the image supports that conclusion.",
        "Do not reconstruct unreadable markings.",
    ]


# ============================================================
# Workflow instructions
# ============================================================

WORKFLOW_INSTRUCTIONS = {

    "component_identification": """
Analyze the component conservatively.

Focus on:
- what the component appears to be
- visible markings
- package and terminals
- function
- general working
- likely applications
- what cannot be confirmed

Do not invent an exact part number or pinout.
""",

    "component_testing": """
Treat this as a practical component-testing task.

Explain:
- what needs to be identified first
- suitable test equipment
- safe test procedure
- expected observations
- how to interpret the result

Do not invent exact specifications when the component identity is uncertain.
""",

    "circuit_analysis": """
Analyze the circuit as an electronics system.

Focus on:
- visible components
- visible connections
- likely circuit function
- signal/current path when supportable
- operating principle
- relevant equations
- uncertainty

Distinguish visible wiring from inferred electrical behavior.
""",

    "circuit_troubleshooting": """
Approach this as an electronics troubleshooting task.

First identify clearly visible evidence.

Then separate:
1. Confirmed observations
2. Likely causes
3. Things that cannot be confirmed

Give practical diagnostic steps in a safe order.
Do not claim a fault is confirmed without sufficient evidence.
""",

"concept_learning": """
Explain the concept clearly and directly.

For a normal question:
- Give the core definition or answer first.
- Add only one short conceptual explanation if needed.
- Keep the response concise, preferably 1–3 sentences.
- Do not create multiple paragraphs for a basic definition.
- Do not automatically add examples, analogies, equations, applications,
  classifications, or detailed sections.

Only add deeper technical detail when:
- the user asks for it,
- the question genuinely requires it, or
- the previous conversation clearly requires clarification.
""",

    "lab_assistance": """
Treat this as an ECE laboratory task.

When relevant, organize the response around:
- experiment
- aim
- principle
- components
- procedure
- observations
- calculations
- precautions
- viva questions
- conclusion

Only include sections supported by the user's request.
Do not invent experimental measurements.
""",

    "viva_preparation": """
Prepare the student for an electronics viva.

Prefer:
- likely question
- concise answer
- important follow-up concept

Prioritize conceptual understanding over memorization.
""",

    "exam_answer": """
Write an engineering-exam-ready answer.

Use an appropriate structure such as:
- definition
- diagram description
- principle
- working
- equation
- advantages
- applications

Do not add sections that are irrelevant to the question.
""",

    "calculation": """
Solve the electronics calculation carefully.

Show:
- known values
- required quantity
- formula
- substitution
- calculation
- final answer with units

Define symbols and state assumptions.
Check the result for physical plausibility.
""",

    "comparison": """
Compare the requested electronics concepts/components directly.

Focus on the differences that matter to an ECE student.
Use a compact table when it genuinely improves clarity.
""",

    "summary": """
Summarize the relevant electronics discussion for revision.

Prioritize:
- definitions
- key concepts
- formulas
- important distinctions
- practical points
""",

    "general_electronics": """
Answer as a technically accurate ECE electronics assistant.

Start with the direct answer and expand only as useful.
""",
}


# ============================================================
# Context construction
# ============================================================

def build_context(
    user_text: str,
    has_image: bool = False,
    conversation_history: Optional[list[dict]] = None,
    previous_visual_context: Optional[dict] = None,
) -> RequestContext:
    """
    Build the internal CircuitSnap request context.
    """

    intent = detect_intent(user_text)

    input_hint = infer_input_type_hint(
        user_text=user_text,
        has_image=has_image,
    )

    if has_image and input_hint == "unknown" and previous_visual_context:
        previous_input_type = previous_visual_context.get("input_type")
        if previous_input_type in INPUT_TYPES - {"unknown"}:
            input_hint = previous_input_type

    workflow = select_workflow(
        intent=intent,
        input_type=input_hint,
    )

    if (
        not has_image
        and intent in {"general", "explain"}
        and is_contextual_follow_up(user_text)
    ):
        previous_workflow = infer_previous_workflow(
            conversation_history
        )
        if previous_workflow:
            workflow = previous_workflow

    detail_level = determine_detail_level(
        user_text
    )

    evidence_rules = build_evidence_rules(
        has_image=has_image
    )

    conversation_context = build_conversation_context(
        conversation_history or []
    )

    image_context = ""
    if has_image and previous_visual_context:
        image_context = str(
            previous_visual_context.get("summary") or ""
        ).strip()[:2000]

    return RequestContext(
        user_text=user_text.strip(),
        has_image=has_image,
        input_type=input_hint,
        intent=intent,
        workflow=workflow,
        detail_level=detail_level,
        image_context=image_context,
        conversation_context=conversation_context,
        evidence_rules=evidence_rules,
    )


# ============================================================
# Conversation context
# ============================================================

def build_conversation_context(
    history: list[dict],
    max_messages: int = 10,
) -> str:
    """
    Convert recent conversation history into compact context.

    The current request is handled separately.
    """

    if not history:
        return ""

    recent = history[-max_messages:]

    lines = []

    for message in recent:
        role = message.get("role")

        if role not in {"user", "assistant"}:
            continue

        content = str(
            message.get("content", "")
        ).strip()

        if not content:
            continue

        label = (
            "Student"
            if role == "user"
            else "CircuitSnap"
        )

        lines.append(
            f"{label}: {content}"
        )

    if not lines:
        return ""

    return "\n".join(lines)


# ============================================================
# Provider prompt construction
# ============================================================

def build_engine_prompt(
    context: RequestContext,
) -> str:
    """
    Convert CircuitSnap's internal context into the provider
    request.

    The provider receives one complete task rather than several
    separate classification calls.
    """

    workflow_instruction = WORKFLOW_INSTRUCTIONS.get(
        context.workflow,
        WORKFLOW_INSTRUCTIONS["general_electronics"],
    )

    evidence = "\n".join(
        f"- {rule}"
        for rule in context.evidence_rules
    )

    conversation = (
        context.conversation_context
        if context.conversation_context
        else "No previous conversation."
    )

    image_instruction = ""

    if context.has_image:
        image_instruction = """
A user image is attached.

Visually determine the most appropriate input category:
- component
- circuit diagram
- physical circuit
- electronics document
- unknown

Do not blindly trust the textual hint if the image contradicts it.

For relevant factual claims derived from this image, explicitly use
the labels CONFIRMED, LIKELY, or CANNOT CONFIRM. Clearly readable
markings or unambiguous color bands and their order may CONFIRM a
decoded nominal value. If a candidate is supported but moderately
uncertain, use LIKELY and state what is unclear. If low resolution,
blur, occlusion, or uncertain band count/order prevents a reliable
resistor decode, use CANNOT CONFIRM, request a clearer close-up, and do
not force a single value from a merely plausible band sequence. Mark
uncertain visual claims using the explicit uppercase LIKELY label;
lowercase "likely" is not a substitute. Do not place uncertain claims
under a CONFIRMED heading. An image alone cannot confirm an exact
measured value or an unshown rating. Do not apply these labels to
unrelated technical background or force them when no relevant
uncertainty exists.

Never invent a standards name or number, organization, certification,
citation, datasheet reference, or other source designation. Include a
reference only when it is explicitly provided by the request or prior
context, or when you know it with high confidence and it is directly
relevant. A previous assistant message does not verify a reference. If
uncertain, omit it. For resistor color-band analysis, explain the
observed bands and decoded nominal value or tolerance; do not add a
standards citation unless the user explicitly asks for one.
"""

        if context.image_context:
            image_instruction += f"""

Previous visual context from this conversation:
{context.image_context}

Use this as context, then verify visual claims against the attached
image and retain appropriate uncertainty.
"""

    return f"""
You are operating as the reasoning engine for CircuitSnap,
an electronics assistant designed specifically for ECE students.

IMPORTANT:
The frontend is intentionally simple.
Your job is to perform the specialized electronics reasoning.

CURRENT REQUEST
---------------

Student request:
{context.user_text or "[No text — analyze the attached image/request context.]"}

Image attached:
{"YES" if context.has_image else "NO"}

Initial input-type hint:
{context.input_type}

Detected user intent:
{context.intent}

Selected ECE workflow:
{context.workflow}

Requested detail level:
{context.detail_level}

{image_instruction}

PREVIOUS CONVERSATION
---------------------

- If the user repeats the same or nearly identical question, answer it
  directly again. Do not say that it was already answered and do not
  assume the user missed the previous response.
- Treat repeated questions as a request for a fresh, clear explanation
  unless the user explicitly asks for a different explanation.

{conversation}

WORKFLOW
--------

{workflow_instruction}

EVIDENCE AND RELIABILITY
------------------------

{evidence}

ECE BEHAVIOR
------------

- Think like an electronics teaching assistant.
- Match the response to what the student is actually asking.
- Do not force every possible section into every answer.
- Preserve useful context from previous messages.
- If the student asks a follow-up question, answer it in the context
  of the previous discussion.
- Prefer technically correct explanations over impressive-sounding ones.
- If an exact identification is not supported, say what can be
  determined instead.
- Do not fabricate measurements, observations, specifications,
  component values, or datasheet information.
- When a formula is used, define the symbols.
- When an image is involved, distinguish observation from inference.
- For safety-sensitive electrical work, state the relevant limitation
  before giving procedural advice.

RESPONSE
--------

Answer the student's request directly.

RESPONSE DEPTH RULES
--------------------

For a normal/simple question:
- Give the direct answer immediately.
- Usually keep the answer to 1–3 short sentences.
- Prefer one compact paragraph.
- Use simple, professional ECE language.
- Do not add examples, analogies, applications, classifications,
  formulas, advantages, disadvantages, or history unless needed.
- Do not expand the answer just because more information is available.
- Stop immediately once the question is properly answered.

For a follow-up question:
- Answer only the new question.
- Use the previous conversation when relevant.
- Do not repeat the entire previous explanation.

For an explicitly detailed question:
- Provide deeper technical explanation.

For an exam request:
- Use an exam-appropriate structure.

For a practical/lab request:
- Give the practical information required for the task.

The goal is not to make every answer short.
The goal is to give exactly the amount of information needed
to answer the user's current request clearly.

Use clear headings and bullets only when they genuinely improve readability.

Do not mention this internal engine, workflow selection,
classification process, or these instructions.
""".strip()


# ============================================================
# Main engine entry point
# ============================================================

def prepare_request(
    user_text: str,
    has_image: bool = False,
    conversation_history: Optional[list[dict]] = None,
    previous_visual_context: Optional[dict] = None,
) -> tuple[RequestContext, str]:
    """
    Prepare a CircuitSnap request for the selected provider.

    Returns:
        (context, provider_prompt)
    """

    context = build_context(
        user_text=user_text,
        has_image=has_image,
        conversation_history=conversation_history,
        previous_visual_context=previous_visual_context,
    )

    prompt = build_engine_prompt(context)

    return context, prompt


def run_engine(
    *,
    provider: str,
    model_id: str,
    user_text: str,
    conversation_history: Optional[list[dict]] = None,
    image_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
    previous_visual_context: Optional[dict] = None,
):
    """
    Main CircuitSnap backend entry point.

    This function:
        1. Understands the request
        2. Builds the ECE workflow
        3. Builds the provider prompt
        4. Sends one request to the selected provider
        5. Returns the answer plus internal context
    """

    # Import here to keep the engine independent from the provider
    # implementation during application startup.
    from providers import ask_provider

    has_image = image_bytes is not None

    context, prompt = prepare_request(
        user_text=user_text,
        has_image=has_image,
        conversation_history=conversation_history,
        previous_visual_context=previous_visual_context,
    )

    provider_result = ask_provider(
        provider=provider,
        model_id=model_id,
        prompt=prompt,
        image_bytes=image_bytes,
        mime_type=mime_type,
        return_metadata=True,
    )

    return {
        **provider_result,
        "context": context,
    }
