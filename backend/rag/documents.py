"""Workspace-scoped document lifecycle and hybrid retrieval.

Portable storage uses SQLAlchemy. Optional local Ollama embeddings augment
keyword ranking; a failed embedding request is visible as lexical-only mode.
"""

import hashlib
import json
import math
import re
import uuid
import httpx
from fastapi import HTTPException
from backend.auth.models import Document, Chunk, get_session_factory
from backend.config import settings
from backend.rag.chunking import chunk_by_heading


def embed(texts):
    if not settings.embedding_model:
        return [None] * len(texts)
    response = httpx.post(
        settings.ollama_base_url + "/api/embed",
        json={"model": settings.embedding_model, "input": texts},
        timeout=settings.request_timeout,
    )
    response.raise_for_status()
    return response.json()["embeddings"]


def parse(name, content):
    if name.lower().endswith(".pdf"):
        if not content.startswith(b"%PDF-"):
            raise HTTPException(400, "Invalid PDF")
        import pymupdf

        with pymupdf.open(stream=content, filetype="pdf") as doc:
            if len(doc) > 500:
                raise HTTPException(413, "PDF exceeds 500 pages")
            return [(i + 1, page.get_text()) for i, page in enumerate(doc)]
    try:
        return [(1, content.decode("utf-8"))]
    except UnicodeDecodeError:
        raise HTTPException(400, "Text documents must be UTF-8")


def ingest_document(user_id, workspace_id, name, content):
    if settings.document_parser == "docling":
        import tempfile
        from pathlib import Path
        from docling.document_converter import DocumentConverter

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ("input" + Path(name).suffix.lower())
            path.write_bytes(content)
            pages = [
                (1, DocumentConverter().convert(path).document.export_to_markdown())
            ]
    else:
        pages = parse(name, content)
    chunks = [(page, c["text"]) for page, text in pages for c in chunk_by_heading(text)]
    if not chunks:
        raise HTTPException(
            422, "No text extracted; run OCR before uploading scanned documents"
        )
    if len(chunks) > 3000:
        raise HTTPException(413, "Document exceeds 3000 chunks")
    vectors = embed([text for _, text in chunks])
    digest = hashlib.sha256(content).hexdigest()
    with get_session_factory()() as db:
        doc = db.query(Document).filter_by(workspace_id=workspace_id, name=name).first()
        if doc and doc.owner_id != user_id:
            raise HTTPException(403, "Only the document owner can replace it")
        if doc:
            db.query(Chunk).filter_by(document_id=doc.id).delete()
            doc.version += 1
        else:
            doc = Document(
                id=str(uuid.uuid4()),
                owner_id=user_id,
                workspace_id=workspace_id,
                name=name,
            )
            db.add(doc)
        doc.content = "\n\n".join(t for _, t in pages)
        doc.sha256 = digest
        doc.status = "ready"
        db.flush()
        for i, ((page, text), vector) in enumerate(zip(chunks, vectors)):
            db.add(
                Chunk(
                    id=f"{doc.id}:{i}",
                    document_id=doc.id,
                    workspace_id=workspace_id,
                    text=text,
                    page=page,
                    embedding=json.dumps(vector) if vector else None,
                )
            )
        db.flush()
        if db.bind.dialect.name == "postgresql":
            from sqlalchemy import text as sql

            for i, vector in enumerate(vectors):
                if vector and len(vector) == 768:
                    db.execute(
                        sql(
                            "UPDATE chunks SET semantic=CAST(:vector AS vector) WHERE id=:id"
                        ),
                        {"vector": json.dumps(vector), "id": f"{doc.id}:{i}"},
                    )
        db.commit()
        return {
            "id": doc.id,
            "status": "ingested",
            "filename": name,
            "chunks": len(chunks),
            "version": doc.version,
            "search_mode": "hybrid" if any(vectors) else "keyword",
        }


def retrieve(query, workspace_id, top_k=5):
    words = set(re.findall(r"\w+", query.lower()))
    if not words:
        return []
    qv = embed([query])[0]
    with get_session_factory()() as db:
        if db.bind.dialect.name == "postgresql":
            return postgres_retrieve(db, query, qv, workspace_id, top_k)
        rows = (
            db.query(Chunk, Document)
            .join(Document, Chunk.document_id == Document.id)
            .filter(
                Chunk.workspace_id == workspace_id,
                Document.workspace_id == workspace_id,
            )
            .all()
        )
        scored = []
        for chunk, doc in rows:
            terms = re.findall(r"\w+", chunk.text.lower())
            lexical = sum(math.log(1 + terms.count(w)) for w in words) / max(
                1, len(words)
            )
            dense = 0.0
            if qv and chunk.embedding:
                v = json.loads(chunk.embedding)
                if len(v) == len(qv):
                    dense = sum(a * b for a, b in zip(v, qv)) / max(
                        1e-9, math.sqrt(sum(a * a for a in v) * sum(b * b for b in qv))
                    )
            if lexical > 0 or dense > 0.55:
                scored.append(
                    (
                        lexical + max(0, dense),
                        {
                            "text": chunk.text,
                            "source": doc.name,
                            "document_id": doc.id,
                            "page": chunk.page,
                            "version": doc.version,
                            "sha256": doc.sha256,
                            "citation": f"[{doc.name}, p.{chunk.page}]",
                            "url": f"/documents/{doc.id}",
                        },
                    )
                )
        return [
            item
            for _, item in sorted(scored, key=lambda pair: pair[0], reverse=True)[
                : max(1, min(top_k, 10))
            ]
        ]


def postgres_retrieve(db, query, vector, workspace_id, top_k):
    """Rank fusion over permission-filtered PostgreSQL full-text and vector hits."""
    from sqlalchemy import text

    params = {"workspace": workspace_id, "query": query}
    lexical = (
        db.execute(
            text(
                "SELECT id FROM chunks WHERE workspace_id=:workspace AND to_tsvector('english', text) @@ plainto_tsquery('english', :query) ORDER BY ts_rank_cd(to_tsvector('english', text), plainto_tsquery('english', :query)) DESC LIMIT 30"
            ),
            params,
        )
        .scalars()
        .all()
    )
    dense = []
    if vector and len(vector) == 768:
        dense = (
            db.execute(
                text(
                    "SELECT id FROM chunks WHERE workspace_id=:workspace AND semantic IS NOT NULL AND semantic <=> CAST(:vector AS vector) < 0.45 ORDER BY semantic <=> CAST(:vector AS vector) LIMIT 30"
                ),
                {"workspace": workspace_id, "vector": json.dumps(vector)},
            )
            .scalars()
            .all()
        )
    scores = {}
    for ranking in [lexical, dense]:
        for rank, chunk_id in enumerate(ranking, 1):
            scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (60 + rank)
    selected = sorted(scores, key=scores.get, reverse=True)[: max(1, min(top_k, 10))]
    hits = []
    for chunk_id in selected:
        row = (
            db.query(Chunk, Document)
            .join(Document, Chunk.document_id == Document.id)
            .filter(
                Chunk.id == chunk_id,
                Chunk.workspace_id == workspace_id,
                Document.workspace_id == workspace_id,
            )
            .first()
        )
        if row:
            chunk, doc = row
            hits.append(
                {
                    "text": chunk.text,
                    "source": doc.name,
                    "document_id": doc.id,
                    "page": chunk.page,
                    "version": doc.version,
                    "sha256": doc.sha256,
                    "citation": f"[{doc.name}, p.{chunk.page}]",
                    "url": f"/documents/{doc.id}",
                }
            )
    return hits
