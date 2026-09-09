"""Durable ingestion queue for the single-worker pilot deployment."""

import asyncio
import base64
import json
import uuid
from starlette.concurrency import run_in_threadpool
from backend.auth.models import DocumentJob, get_session_factory
from backend.auth.workspaces import resolve_workspace
from backend.auth.audit import log_action
from backend.rag.documents import ingest_document


def enqueue(user_id, workspace_id, name, data):
    with get_session_factory()() as db:
        from fastapi import HTTPException

        if (
            db.query(DocumentJob)
            .filter(
                DocumentJob.user_id == user_id,
                DocumentJob.status.in_(["queued", "running"]),
            )
            .count()
            >= 5
        ):
            raise HTTPException(429, "Wait for existing uploads to finish")
        job = DocumentJob(
            id=str(uuid.uuid4()),
            user_id=user_id,
            workspace_id=workspace_id,
            name=name,
            payload=base64.b64encode(data).decode(),
        )
        db.add(job)
        db.commit()
        return {"job_id": job.id, "status": "queued"}


def process_one():
    with get_session_factory()() as db:
        job = (
            db.query(DocumentJob)
            .filter_by(status="queued")
            .order_by(DocumentJob.created_at)
            .first()
        )
        if not job:
            return False
        changed = (
            db.query(DocumentJob)
            .filter_by(id=job.id, status="queued")
            .update({"status": "running"}, synchronize_session=False)
        )
        if changed != 1:
            db.rollback()
            return False
        identifier, uid, wid, name, payload = (
            job.id,
            job.user_id,
            job.workspace_id,
            job.name,
            job.payload,
        )
        db.commit()
    try:
        resolve_workspace(uid, wid)
        result = ingest_document(uid, wid, name, base64.b64decode(payload))
        status = "completed"
        log_action(uid, "document.ingest", result["id"])
    except Exception as error:
        result = {
            "error": "Document processing failed. Check format, model availability, and workspace access.",
            "error_type": type(error).__name__,
        }
        status = "failed"
    with get_session_factory()() as db:
        db.query(DocumentJob).filter_by(id=identifier).update(
            {"status": status, "result": json.dumps(result), "payload": ""}
        )
        db.commit()
    return True


async def worker():
    # A previous process may have died after committing a document. Do not
    # silently retry ambiguous jobs; users can explicitly replace the document.
    with get_session_factory()() as db:
        db.query(DocumentJob).filter_by(status="running").update(
            {"status": "interrupted", "payload": ""}
        )
        db.commit()
    while True:
        if not await run_in_threadpool(process_one):
            await asyncio.sleep(1)
