"""Top-k retrieval with citation support over the ingested knowledge base."""

from __future__ import annotations

from backend.config import settings


def _get_store():
    if settings.rag_backend == "pgvector":
        from backend.rag.pgvector_store import PGVectorStore

        return PGVectorStore()
    from backend.rag import store

    return store


def retrieve(query_text: str, top_k: int = 3) -> list[dict]:
    backend = _get_store()
    results = backend.query(query_text, top_k=top_k)
    for i, r in enumerate(results, start=1):
        r["citation"] = f"[{i}] {r.get('source', 'unknown')}"
    return results
