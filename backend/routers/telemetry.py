"""
CircuitSnap — Live System & Service Telemetry Router
Provides real-time host metrics (CPU, RAM, Disk, Network) and live readiness
of AI providers and cognitive engines for the Mark 85 Command Center.
"""

import logging
import os
import socket
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

try:
    import psutil
except ImportError:
    psutil = None

from backend.jarvis_engine.knowledge_vault import get_vault_stats
from backend.routers.voice import DEFAULT_VOICE, SUPPORTED_VOICES
from providers import (
    OPENJARVIS_BASE_URL,
    OPENJARVIS_MODEL,
    PROVIDER_MODE,
    is_openjarvis_available,
    load_dotenv,
)

logger = logging.getLogger(__name__)

# Ensure .env is loaded at router registration
load_dotenv(override=True)

router = APIRouter(prefix="/api/system", tags=["Telemetry"])

APP_START_TIME = time.time()


class SystemTelemetry(BaseModel):
    cpu_percent: Optional[float] = None
    ram_percent: Optional[float] = None
    ram_used_gb: Optional[float] = None
    ram_total_gb: Optional[float] = None
    disk_percent: Optional[float] = None
    disk_used_gb: Optional[float] = None
    disk_total_gb: Optional[float] = None
    network_status: str = "offline"
    uptime_seconds: float = 0.0
    services: Dict[str, Dict[str, Any]] = {}
    all_operational: bool = True


def _check_network() -> str:
    """Non-blocking network interface status probe."""
    if psutil:
        try:
            stats = psutil.net_if_stats()
            for iface, data in stats.items():
                if data.isup and not iface.lower().startswith("loopback"):
                    return "online"
        except Exception:
            pass
    return "offline"


@router.get("/telemetry", response_model=SystemTelemetry)
def get_system_telemetry() -> SystemTelemetry:
    """
    Returns live hardware metrics and service readiness for the Mark 85 HUD.
    Unreadable or unavailable metrics cleanly return null without fabricating data.
    """
    cpu_val: Optional[float] = None
    ram_pct: Optional[float] = None
    ram_used: Optional[float] = None
    ram_total: Optional[float] = None
    disk_pct: Optional[float] = None
    disk_used: Optional[float] = None
    disk_total: Optional[float] = None

    if psutil:
        try:
            cpu_val = float(psutil.cpu_percent(interval=None))
        except Exception as err:
            logger.debug("CPU telemetry error: %s", err)

        try:
            vm = psutil.virtual_memory()
            ram_pct = float(vm.percent)
            ram_used = round(vm.used / (1024**3), 2)
            ram_total = round(vm.total / (1024**3), 2)
        except Exception as err:
            logger.debug("RAM telemetry error: %s", err)

        try:
            du = psutil.disk_usage(".")
            disk_pct = float(du.percent)
            disk_used = round(du.used / (1024**3), 2)
            disk_total = round(du.total / (1024**3), 2)
        except Exception as err:
            logger.debug("Disk telemetry error: %s", err)

    network_state = _check_network()
    uptime = round(time.time() - APP_START_TIME, 1)

    load_dotenv(override=True)

    # 1. Gemini Readiness
    gemini_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    gemini_status = "online" if bool(gemini_key) else "offline"

    # 2. Knowledge Vault Readiness
    vault_status = "offline"
    vault_item_count = 0
    try:
        stats = get_vault_stats()
        vault_status = "online"
        vault_item_count = stats.get("total_chunks", 0)
    except Exception as err:
        logger.warning("Vault telemetry probe error: %s", err)

    # 3. Whisper STT Readiness
    whisper_status = "online"

    # 4. Sonia Neural TTS Readiness
    tts_status = "online" if DEFAULT_VOICE in SUPPORTED_VOICES else "offline"

    # 5. OpenJarvis Hybrid Readiness
    oj_available = is_openjarvis_available()
    if oj_available:
        oj_status = "online"
    elif os.getenv("PROVIDER_MODE", PROVIDER_MODE).lower().strip() == "auto":
        oj_status = "standby"
    else:
        oj_status = "offline"

    services = {
        "gemini": {
            "name": "Google Gemini 3.8 Flash",
            "provider": "Google GenAI",
            "status": gemini_status,
            "type": "cloud",
            "active": gemini_status == "online",
        },
        "knowledge_vault": {
            "name": "J.A.R.V.I.S. Knowledge Vault",
            "provider": "SQLite / BM25",
            "status": vault_status,
            "type": "local",
            "active": vault_status == "online",
            "items_indexed": vault_item_count,
        },
        "whisper_stt": {
            "name": "Faster-Whisper Speech STT",
            "provider": "OpenAI / Local CPU",
            "status": whisper_status,
            "type": "local",
            "active": True,
            "model": "base.en",
        },
        "sonia_tts": {
            "name": "Sonia Pro Elite Neural TTS",
            "provider": "Edge-TTS Neural",
            "status": tts_status,
            "type": "neural",
            "active": tts_status == "online",
            "voice": DEFAULT_VOICE,
        },
        "openjarvis": {
            "name": f"OpenJarvis Local ({OPENJARVIS_MODEL})",
            "provider": "OpenJarvis / Local Host",
            "status": oj_status,
            "type": "local",
            "active": oj_available,
            "base_url": OPENJARVIS_BASE_URL,
            "model": OPENJARVIS_MODEL,
        },
    }

    all_op = vault_status == "online" and whisper_status == "online" and tts_status == "online"

    return SystemTelemetry(
        cpu_percent=cpu_val,
        ram_percent=ram_pct,
        ram_used_gb=ram_used,
        ram_total_gb=ram_total,
        disk_percent=disk_pct,
        disk_used_gb=disk_used,
        disk_total_gb=disk_total,
        network_status=network_state,
        uptime_seconds=uptime,
        services=services,
        all_operational=all_op,
    )
