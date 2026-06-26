"""Top-k retrieval over the ingested knowledge base."""

from rag.store import query


def retrieve(query_text: str, top_k: int = 3) -> list[dict]:
    return query(query_text, top_k=top_k)
