"""Document metadata, ingestion, replacement, preview and deletion."""

from pathlib import PurePath
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from starlette.concurrency import run_in_threadpool
from backend.auth.middleware import require_permission
from backend.auth.workspaces import resolve_workspace
from backend.auth.models import Document, Chunk, get_session_factory
from backend.auth.audit import log_action
from backend.rag.documents import ingest_document
from backend.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: str | None = None,
    background: bool = False,
    user=Depends(require_permission("upload_documents")),
):
    workspace_id = resolve_workspace(user.id, workspace_id)
    name = file.filename or "upload.txt"
    if len(name) > 200 or PurePath(name).name != name or "\\" in name or "\x00" in name:
        raise HTTPException(400, "Invalid filename")
    if PurePath(name).suffix.lower() not in {".txt", ".md", ".pdf"}:
        raise HTTPException(415, "Supported formats: .txt, .md, .pdf")
    data = bytearray()
    while block := await file.read(65536):
        data.extend(block)
        if len(data) > settings.max_upload_bytes:
            raise HTTPException(413, "File exceeds upload limit")
    if background:
        from backend.rag.jobs import enqueue

        return enqueue(user.id, workspace_id, name, bytes(data))
    result = await run_in_threadpool(
        ingest_document, user.id, workspace_id, name, bytes(data)
    )
    log_action(user.id, "document.ingest", result["id"])
    return result


@router.get("/list")
def list_documents(
    workspace_id: str | None = None, user=Depends(require_permission("chat"))
):
    workspace_id = resolve_workspace(user.id, workspace_id)
    with get_session_factory()() as db:
        docs = (
            db.query(Document)
            .filter_by(workspace_id=workspace_id)
            .order_by(Document.created_at.desc())
            .all()
        )
        return {
            "workspace_id": workspace_id,
            "total_chunks": db.query(Chunk)
            .filter_by(workspace_id=workspace_id)
            .count(),
            "documents": [
                {
                    "id": d.id,
                    "name": d.name,
                    "version": d.version,
                    "status": d.status,
                    "sha256": d.sha256,
                    "owner_id": d.owner_id,
                }
                for d in docs
            ],
        }


@router.get("/jobs/{job_id}")
def job_status(job_id: str, user=Depends(require_permission("chat"))):
    from backend.auth.models import DocumentJob
    import json

    with get_session_factory()() as db:
        job = db.get(DocumentJob, job_id)
        if not job or job.user_id != user.id:
            raise HTTPException(404, "Job not found")
        resolve_workspace(user.id, job.workspace_id)
        return {
            "job_id": job.id,
            "status": job.status,
            "result": json.loads(job.result) if job.result else None,
        }


@router.get("/{document_id}")
def preview(document_id: str, user=Depends(require_permission("chat"))):
    with get_session_factory()() as db:
        doc = db.get(Document, document_id)
        if not doc:
            raise HTTPException(404, "Document not found")
        resolve_workspace(user.id, doc.workspace_id)
        return {
            "id": doc.id,
            "name": doc.name,
            "content": doc.content,
            "version": doc.version,
            "sha256": doc.sha256,
        }


@router.delete("/{document_id}")
def delete(document_id: str, user=Depends(require_permission("upload_documents"))):
    with get_session_factory()() as db:
        doc = db.get(Document, document_id)
        if not doc:
            raise HTTPException(404, "Document not found")
        resolve_workspace(user.id, doc.workspace_id)
        if doc.owner_id != user.id:
            raise HTTPException(403, "Only the owner can delete this document")
        db.query(Chunk).filter_by(document_id=doc.id).delete()
        db.delete(doc)
        db.commit()
    log_action(user.id, "document.delete", document_id)
    return {"status": "deleted"}
