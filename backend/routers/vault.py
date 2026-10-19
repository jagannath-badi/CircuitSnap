import json
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend import db_models
from backend.auth import require_current_user
from backend.database import get_db
from backend.schemas import SaveSessionRequest, SessionDetail, SessionSummary

router = APIRouter(prefix="/api/vault", tags=["vault"])


def _extract_auto_title(messages: List[dict[str, Any]], fallback: str = "Optical Inspection") -> str:
    """Extracts a concise, readable title from the first user query."""
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = str(msg.get("content", "")).strip()
            if content and not content.startswith("(Optical Inspection"):
                return content[:45] + ("..." if len(content) > 45 else "")
    return fallback


def _safe_parse_messages(messages_json: str) -> List[dict[str, Any]]:
    """Safely parses JSON messages string into a list of dicts."""
    try:
        parsed = json.loads(messages_json)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


@router.get("/sessions", response_model=List[SessionSummary])
def list_sessions(
    current_user: db_models.User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> List[SessionSummary]:
    """Lists all archived diagnostic sessions for the authenticated operator."""
    sessions = (
        db.query(db_models.DiagnosticSession)
        .filter(db_models.DiagnosticSession.user_id == current_user.id)
        .order_by(db_models.DiagnosticSession.updated_at.desc())
        .all()
    )

    summaries = []
    for s in sessions:
        msgs = _safe_parse_messages(s.messages)
        summaries.append(
            SessionSummary(
                id=s.id,
                title=s.title,
                has_dut=bool(s.dut_image),
                message_count=len(msgs),
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
        )
    return summaries


@router.post("/sessions", response_model=SessionDetail)
def save_or_update_session(
    payload: SaveSessionRequest,
    current_user: db_models.User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> SessionDetail:
    """Saves or updates a diagnostic session in the operator's vault."""
    session: Optional[db_models.DiagnosticSession] = None

    if payload.id:
        session = (
            db.query(db_models.DiagnosticSession)
            .filter(
                db_models.DiagnosticSession.id == payload.id,
                db_models.DiagnosticSession.user_id == current_user.id,
            )
            .first()
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diagnostic session '{payload.id}' not found.",
            )

    messages_json = json.dumps(payload.messages)
    title = (payload.title or "").strip()
    if not title:
        title = _extract_auto_title(payload.messages)

    if session:
        session.title = title
        if payload.dut_image is not None:
            session.dut_image = payload.dut_image
        session.messages = messages_json
    else:
        session = db_models.DiagnosticSession(
            user_id=current_user.id,
            title=title,
            dut_image=payload.dut_image,
            messages=messages_json,
        )
        db.add(session)

    db.commit()
    db.refresh(session)

    return SessionDetail(
        id=session.id,
        title=session.title,
        dut_image=session.dut_image,
        messages=_safe_parse_messages(session.messages),
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session_detail(
    session_id: str,
    current_user: db_models.User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> SessionDetail:
    """Fetches full diagnostic session details for restoration."""
    session = (
        db.query(db_models.DiagnosticSession)
        .filter(
            db_models.DiagnosticSession.id == session_id,
            db_models.DiagnosticSession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic session '{session_id}' not found.",
        )

    return SessionDetail(
        id=session.id,
        title=session.title,
        dut_image=session.dut_image,
        messages=_safe_parse_messages(session.messages),
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    current_user: db_models.User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Deletes an archived diagnostic session from the vault."""
    session = (
        db.query(db_models.DiagnosticSession)
        .filter(
            db_models.DiagnosticSession.id == session_id,
            db_models.DiagnosticSession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic session '{session_id}' not found.",
        )

    db.delete(session)
    db.commit()
    return {"status": "deleted", "id": session_id}

