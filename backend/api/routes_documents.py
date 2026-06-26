"""Document upload and management routes."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile

from backend.auth.middleware import require_permission
from backend.auth.models import User
from backend.rag.ingest import ingest

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("upload_documents")),
) -> dict:
    if file.filename and not file.filename.endswith((".md", ".pdf", ".txt")):
        return {"error": "Unsupported file type. Supported: .md, .pdf, .txt"}

    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir) / (file.filename or "upload.md")
        content = await file.read()
        dest.write_bytes(content)
        count = ingest(Path(tmpdir))

    return {"status": "ingested", "filename": file.filename, "chunks": count}


@router.get("/list")
async def list_documents(
    current_user: User = Depends(require_permission("chat")),
) -> dict:
    from backend.rag.store import get_collection

    collection = get_collection()
    count = collection.count()
    return {"total_chunks": count}
