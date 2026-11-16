"""
CircuitSnap — Knowledge Vault & Learning API Router
Allows students to upload PDFs/notes, save formulas, and inspect vault telemetry.
"""

from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from backend.jarvis_engine.knowledge_vault import (
    get_vault_stats,
    ingest_document,
    ingest_user_taught_concept,
    search_vault,
)

router = APIRouter(prefix="/api/learn", tags=["Knowledge Vault"])


class FeedbackRequest(BaseModel):
    text: str
    branch: Optional[str] = "ALL"
    title: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    branch: Optional[str] = None
    top_k: Optional[int] = 3


@router.post("/ingest")
async def ingest_study_material(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    branch: str = Form("ALL"),
    title: Optional[str] = Form(None),
):
    """
    Ingests study material (PDF, TXT, Markdown, or raw text) into the Knowledge Vault.
    Indexed with BM25 semantic retrieval and tagged by engineering branch.
    """
    if file:
        content = await file.read()
        filename = file.filename or "uploaded_notes.txt"
        res = ingest_document(filename=filename, file_bytes=content, branch=branch)
        if res.get("status") == "error":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("message"))
        return res
    elif text and text.strip():
        res = ingest_user_taught_concept(text=text.strip(), branch=branch, title=title)
        return res
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either an uploaded file or text content to ingest.",
        )


@router.post("/feedback")
def save_concept_feedback(payload: FeedbackRequest):
    """
    Saves a user-taught concept, formula, or starred assistant explanation to the Knowledge Vault.
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Concept text cannot be empty.")

    res = ingest_user_taught_concept(
        text=payload.text.strip(),
        branch=payload.branch or "ALL",
        title=payload.title,
    )
    return res


@router.get("/stats")
def vault_telemetry():
    """
    Returns active Knowledge Vault metrics: total chunks, total documents, and branch breakdown.
    """
    return get_vault_stats()


@router.post("/search")
def search_vault_endpoint(payload: SearchRequest):
    """
    Performs BM25 semantic search over the Knowledge Vault.
    """
    hits = search_vault(query=payload.query, branch=payload.branch, top_k=payload.top_k or 3)
    return {"query": payload.query, "results": hits, "count": len(hits)}
