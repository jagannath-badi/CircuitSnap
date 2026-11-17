"""
CircuitSnap — Human-in-the-Loop Operations & Task Queue Router
Manages active background study tasks, pending sensitive approvals,
and the Mark 85 Emergency Stop circuit.
"""

import logging
import time
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/operations", tags=["Operations"])

# In-Memory Operations Store
_OPERATIONS_STATE: Dict[str, Any] = {
    "emergency_stop": False,
    "auto_approve": False,
    "tasks": [
        {
            "id": "task-01",
            "title": "Symbolic Equation & Boundary Solver",
            "branch": "MATH",
            "progress": 85,
            "status": "running",
            "eta_seconds": 1.2,
        },
        {
            "id": "task-02",
            "title": "Structural & Equilibrium Verification",
            "branch": "MECHANICS",
            "progress": 62,
            "status": "running",
            "eta_seconds": 2.4,
        },
        {
            "id": "task-03",
            "title": "Dimensional & SI Unit Consistency Audit",
            "branch": "SYSTEMS",
            "progress": 38,
            "status": "running",
            "eta_seconds": 3.8,
        },
    ],
    "approvals": [],
    "recent_activity": [
        {
            "id": "act-01",
            "title": "Multi-Variable System Model Derived",
            "timestamp": "3m ago",
            "status": "completed",
            "result": "State space & transfer function verified",
        },
        {
            "id": "act-02",
            "title": "Boundary & Conservation Check Verified",
            "timestamp": "12m ago",
            "status": "completed",
            "result": "Energy balance & continuity satisfied",
        },
    ],
    "right_now": {
        "recommendation": "Verify governing equations, boundary conditions, and SI unit consistency before finalizing lab calculations.",
        "branch": "CORE",
        "topic": "First-Principles Verification",
        "urgency": "high",
    },
}


class DecisionRequest(BaseModel):
    decision: Literal["approve", "decline"]
    auto_approve: Optional[bool] = False


class OperationsResponse(BaseModel):
    emergency_stop: bool
    auto_approve: bool
    tasks: List[Dict[str, Any]]
    approvals: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    right_now: Dict[str, Any]


@router.get("", response_model=OperationsResponse)
def get_operations() -> OperationsResponse:
    """Returns active tasks, pending approvals, and right-now recommendation."""
    return OperationsResponse(
        emergency_stop=_OPERATIONS_STATE["emergency_stop"],
        auto_approve=_OPERATIONS_STATE["auto_approve"],
        tasks=_OPERATIONS_STATE["tasks"],
        approvals=_OPERATIONS_STATE["approvals"],
        recent_activity=_OPERATIONS_STATE["recent_activity"],
        right_now=_OPERATIONS_STATE["right_now"],
    )


@router.post("/{op_id}/decision")
def record_decision(op_id: str, payload: DecisionRequest):
    """Approves or declines a pending sensitive operation."""
    if _OPERATIONS_STATE["emergency_stop"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Emergency Stop is currently active. Reset bench before approving tasks.",
        )

    for appr in _OPERATIONS_STATE["approvals"]:
        if appr["id"] == op_id:
            appr["status"] = "approved" if payload.decision == "approve" else "declined"
            # Move to recent activity
            _OPERATIONS_STATE["recent_activity"].insert(
                0,
                {
                    "id": f"act-{int(time.time())}",
                    "title": f"{appr['title']} ({payload.decision.upper()})",
                    "timestamp": "Just now",
                    "status": "completed" if payload.decision == "approve" else "declined",
                    "result": f"Action {payload.decision}d by operator",
                },
            )
            # Remove from pending approvals
            _OPERATIONS_STATE["approvals"] = [
                a for a in _OPERATIONS_STATE["approvals"] if a["id"] != op_id
            ]
            return {
                "status": "success",
                "op_id": op_id,
                "decision": payload.decision,
                "remaining_approvals": len(_OPERATIONS_STATE["approvals"]),
            }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Approval operation '{op_id}' not found.",
    )


@router.post("/emergency-stop")
def trigger_emergency_stop():
    """
    Emergency Stop Circuit:
    Immediately halts active background solvers, pauses active fetch streams,
    and disarms automated operations.
    """
    _OPERATIONS_STATE["emergency_stop"] = True
    for task in _OPERATIONS_STATE["tasks"]:
        task["status"] = "aborted"

    logger.warning("🚨 [EMERGENCY STOP]: Activated by operator.")
    return {
        "status": "emergency_stop_activated",
        "message": "All active operations aborted. Workstation state returned to standby.",
        "emergency_stop": True,
    }


@router.post("/reset")
def reset_operations():
    """Restores operations from Emergency Stop state to normal standby."""
    _OPERATIONS_STATE["emergency_stop"] = False
    _OPERATIONS_STATE["tasks"] = [
        {
            "id": "task-01",
            "title": "Symbolic Laplace Transform Derivation",
            "branch": "MATH",
            "progress": 100,
            "status": "standby",
            "eta_seconds": 0.0,
        }
    ]
    return {
        "status": "reset_successful",
        "emergency_stop": False,
        "message": "Operations restored to standby.",
    }
