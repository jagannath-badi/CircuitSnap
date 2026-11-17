import asyncio
import logging
import os
import re
import tempfile
from typing import Dict, Optional

import edge_tts
from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Voice"])

_whisper_model = None


def get_whisper_model():
    """Lazy singleton initializer for faster-whisper on CPU with int8 quantization."""
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        # Use base.en for high-accuracy local ECE transcription
        _whisper_model = WhisperModel("base.en", device="cpu", compute_type="int8")
    return _whisper_model


def filter_hallucinations(text: str) -> str:
    """Filters out degenerate hallucination loops (e.g. repeated words or silence noise artefacts)."""
    if not text or len(text.strip()) < 2:
        return ""
    words = re.findall(r"\b\w+\b", text.lower())
    # Check for 3+ consecutive identical words (e.g., "highloud highloud highloud")
    for i in range(len(words) - 2):
        if words[i] == words[i + 1] == words[i + 2]:
            return ""
    # Check for degenerate loops where text is mostly 1 or 2 repeated words across 4+ tokens
    if len(words) >= 4 and len(set(words)) <= 2:
        return ""
    return text.strip()


def normalize_ece_speech(text: str) -> str:
    """
    Phonetic normalizer for Electronics & Communication Engineering (ECE) terminology.
    Corrects common speech recognition errors for components, pinouts, and units.
    """
    if not text:
        return ""
    t = text.strip()

    # Wake-word normalization (e.g. "hey divers", "hey service", "a jarvis", "hi divers")
    t = re.sub(
        r"\b(?:(?:hey|hi|hello|ok|okay|a)\s+(?:service|job\s*is|travis|divers)|(?:(?:hey|hi|hello|ok|okay|a)\s+)?jarvis)\b",
        "hey jarvis",
        t,
        flags=re.IGNORECASE,
    )

    # IC Part Numbers
    t = re.sub(r"\b(?:any|ne|n e|any\s*time)\s*555\b", "NE555", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:lm|l m)\s*741\b", "LM741", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:lm|l m)\s*358\b", "LM358", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:tl|t l)\s*072\b", "TL072", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:lm|l m)\s*7805\b", "LM7805", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:bc|b c)\s*547\b", "BC547", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:2n|2 n)\s*2222\b", "2N2222", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:irfz|irf z|ir f z)\s*44n?\b", "IRFZ44N", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:1n|1 n)\s*4007\b", "1N4007", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:1n|1 n)\s*4148\b", "1N4148", t, flags=re.IGNORECASE)

    # Electrical units & values
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(?:oms|homes?|ohms?)\b", r"\1 ohms", t, flags=re.IGNORECASE)
    t = re.sub(r"\boms\b", "ohms", t, flags=re.IGNORECASE)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(?:kilo\s*(?:ohms?|homes?)|k\s*ohms?|kilo)\b", r"\1kΩ", t, flags=re.IGNORECASE)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(?:mega\s*(?:ohms?|homes?)|m\s*ohms?)\b", r"\1MΩ", t, flags=re.IGNORECASE)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(?:micro\s*farads?|u\s*farads?|microfarads?|uf)\b", r"\1uF", t, flags=re.IGNORECASE)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(?:nano\s*farads?|n\s*farads?|nanofarads?|nf)\b", r"\1nF", t, flags=re.IGNORECASE)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(?:pico\s*farads?|p\s*farads?|picofarads?|pf)\b", r"\1pF", t, flags=re.IGNORECASE)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(?:milli\s*henries?|mh)\b", r"\1mH", t, flags=re.IGNORECASE)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(?:micro\s*henries?|uh)\b", r"\1uH", t, flags=re.IGNORECASE)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(?:kilo\s*hertz|khz)\b", r"\1kHz", t, flags=re.IGNORECASE)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(?:mega\s*hertz|mhz)\b", r"\1MHz", t, flags=re.IGNORECASE)

    # Multi-Discipline Engineering terms
    t = re.sub(r"\b(?:la\s*place)\b", "Laplace", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:reynolds?|raynolds?)\s*(?:number)?\b", "Reynolds number", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:car\s*no|carnot)\b", "Carnot", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:big\s*o)\b", "Big-O", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:youngs?|young's)\s*modulus\b", "Young's modulus", t, flags=re.IGNORECASE)

    # Clean whitespace & punctuation
    t = re.sub(r"\s+", " ", t).strip()
    return t


def clean_tts_text(raw: str) -> str:
    """Strips markdown formatting, tables, and LaTeX math into natural spoken units for edge-tts."""
    if not raw or not raw.strip():
        return "Specifications and calculations are displayed on screen."

    text = raw
    # Pronounce "Jarvis" as a single cohesive word
    text = re.sub(r"J\.A\.R\.V\.I\.S\.?", "Jarvis", text, flags=re.IGNORECASE)
    text = re.sub(r"\bJARVIS\b", "Jarvis", text)

    # Strip code blocks and inline code
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Strip markdown tables completely
    text = re.sub(r"^\s*\|.*\|\s*$", " ", text, flags=re.MULTILINE)
    text = re.sub(r"\|[^\n]+\|", " ", text)

    # Strip headers and badges
    text = re.sub(r"(?:^|\n)\s*#{1,6}\s*", " ", text)
    text = re.sub(r"\[\s*(?:CONFIRMED|LIKELY|CANNOT CONFIRM)\s*\]\s*[:\-\u2013\u2014]?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:CONFIRMED|CANNOT CONFIRM)\b\s*[:\-\u2013\u2014]?", "", text, flags=re.IGNORECASE)

    # LaTeX math conversion
    text = re.sub(r"\$\$([\s\S]*?)\$\$", r" \1 ", text)
    text = re.sub(r"\$([^$]+)\$", r" \1 ", text)
    text = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"\1 over \2", text)
    text = re.sub(r"\\sqrt\{([^}]+)\}", r"square root of \1", text)
    text = re.sub(r"\\cdot|\\times", " times ", text)
    text = re.sub(r"\\approx", " approximately ", text)
    text = re.sub(r"\\pi", "pi", text)
    text = re.sub(r"\\mu", "micro", text)
    text = re.sub(r"\\Omega", "ohms", text)
    text = re.sub(r"\\mathbf\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\text\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+", " ", text)

    # Spoken electrical units
    text = re.sub(r"(\d+(?:\.\d+)?)\s*MΩ", r"\1 mega-ohms", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*kΩ", r"\1 kilo-ohms", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*Ω", r"\1 ohms", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*µF", r"\1 microfarads", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*uF", r"\1 microfarads", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*nF", r"\1 nanofarads", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*pF", r"\1 picofarads", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*mH", r"\1 millihenries", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*µH", r"\1 microhenries", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*uH", r"\1 microhenries", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*kHz", r"\1 kilohertz", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*MHz", r"\1 megahertz", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*GHz", r"\1 gigahertz", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*Hz", r"\1 hertz", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*mA", r"\1 milliamps", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*mV", r"\1 millivolts", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*V(?![a-zA-Z])", r"\1 volts", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*W(?![a-zA-Z])", r"\1 watts", text)

    # Strip Markdown bullets & symbols
    text = re.sub(r"[*_~`>]+", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) < 12:
        return "Specifications and calculations are displayed on screen."

    # Cap spoken text to ~480 characters at a clean sentence boundary
    if len(text) > 480:
        cut = text[:480]
        # Look for sentence boundary between 240 and 480
        match = list(re.finditer(r"[.!?](?:\s|$)", cut))
        if match and match[-1].end() >= 220:
            text = cut[: match[-1].end()].strip()
        else:
            text = cut.rsplit(" ", 1)[0].rstrip(",;:-") + "."

    return text


SUPPORTED_VOICES: Dict[str, Dict[str, str]] = {
    "en-GB-SoniaNeural": {
        "name": "Sonia — J.A.R.V.I.S. Pro Elite Female",
        "default_pitch": "+2Hz",
        "default_rate": "+4%",
        "gender": "female",
        "accent": "British",
    },
    "en-US-AriaNeural": {
        "name": "Aria — Studio Female",
        "default_pitch": "+0Hz",
        "default_rate": "+3%",
        "gender": "female",
        "accent": "American",
    },
    "en-US-JennyNeural": {
        "name": "Jenny — Warm Tutor",
        "default_pitch": "+0Hz",
        "default_rate": "+2%",
        "gender": "female",
        "accent": "American",
    },
    "en-GB-RyanNeural": {
        "name": "Ryan — Classic British Male",
        "default_pitch": "-4Hz",
        "default_rate": "+5%",
        "gender": "male",
        "accent": "British",
    },
}
DEFAULT_VOICE = "en-GB-SoniaNeural"


class STTResponse(BaseModel):
    text: str


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = DEFAULT_VOICE
    rate: Optional[str] = "+4%"
    pitch: Optional[str] = "+2Hz"


@router.get("/voices")
def list_voices():
    """Returns supported neural voice personas and their defaults."""
    return {
        "default": DEFAULT_VOICE,
        "personas": [
            {
                "id": k,
                "name": v["name"],
                "default_pitch": v["default_pitch"],
                "default_rate": v["default_rate"],
                "gender": v["gender"],
                "accent": v["accent"],
            }
            for k, v in SUPPORTED_VOICES.items()
        ],
    }


def _transcribe_file(file_path: str) -> str:
    """Runs faster-whisper transcription synchronously inside worker thread."""
    try:
        model = get_whisper_model()
        segments, _ = model.transcribe(
            file_path,
            beam_size=1,
            vad_filter=True,
            no_speech_threshold=0.6,
            condition_on_previous_text=False,
            initial_prompt=(
                "Jarvis, CircuitSnap, Laplace, eigenvalue, Reynolds number, Bernoulli, "
                "stress, strain, Young's modulus, Carnot, binary, hexadecimal, subnet, CIDR, "
                "Big-O, truth table, NE555, LM741, LM358, TL072, LM7805, BC547, "
                "IRFZ44N, MOSFET, BJT, resistor, capacitor, inductor, diode, "
                "ohms, kilo-ohms, microfarads, astable, cutoff frequency"
            ),
            language="en",
        )
        raw_text = " ".join([seg.text for seg in segments]).strip()
        filtered = filter_hallucinations(raw_text)
        if not filtered:
            return ""
        return normalize_ece_speech(filtered)
    except Exception as err:
        logger.warning("Whisper transcription error: %s", err)
        return ""


@router.post("/stt", response_model=STTResponse)
async def speech_to_text(file: UploadFile = File(...)) -> STTResponse:
    """
    Sub-200ms local speech-to-text using faster-whisper and ECE phonetic normalizer.
    Accepts raw audio blob from VAD recorder (webm/wav/ogg).
    """
    content = await file.read()
    if len(content) < 512:
        return STTResponse(text="")

    suffix = ".webm"
    if file.filename and "." in file.filename:
        suffix = f".{file.filename.rsplit('.', 1)[-1]}"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            tmp.write(content)

        clean_text = await asyncio.to_thread(_transcribe_file, tmp_path)
        return STTResponse(text=clean_text)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


async def _fetch_tts_bytes(communicate: edge_tts.Communicate) -> bytes:
    """Streams audio chunks from edge-tts and aggregates into a complete MP3 buffer."""
    chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
    return b"".join(chunks)


@router.post("/tts")
async def text_to_speech(payload: TTSRequest):
    """
    Neural Text-to-Speech using edge-tts with selectable persona (default: en-GB-SoniaNeural).
    Streams MP3 audio with 8.0s timeout safety to eliminate hanging connections.
    """
    cleaned_text = clean_tts_text(payload.text)
    if not cleaned_text:
        cleaned_text = "Specifications and calculations are displayed on screen."

    voice = payload.voice if payload.voice in SUPPORTED_VOICES else DEFAULT_VOICE
    profile = SUPPORTED_VOICES[voice]
    rate = payload.rate or profile["default_rate"]
    pitch = payload.pitch or profile["default_pitch"]

    communicate = edge_tts.Communicate(
        text=cleaned_text,
        voice=voice,
        rate=rate,
        pitch=pitch,
    )

    try:
        audio_bytes = await asyncio.wait_for(_fetch_tts_bytes(communicate), timeout=8.0)
    except asyncio.TimeoutError:
        logger.warning("TTS generation timed out after 8.0s for voice %s", voice)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Neural TTS synthesis timed out after 8.0 seconds.",
        )
    except Exception as err:
        logger.error("TTS generation error: %s", err)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Neural TTS synthesis failed: {str(err)}",
        )

    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Neural TTS returned empty audio payload.",
        )

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Length": str(len(audio_bytes)),
            "Cache-Control": "no-cache",
        },
    )
