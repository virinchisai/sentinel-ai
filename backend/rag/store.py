"""Chroma vector store wrapper using a local sentence-transformers embedding model.

Embeddings are computed with sentence-transformers (not the chat LLM provider)
so RAG ingestion/retrieval works regardless of which LLM provider is configured
and without spending API tokens on embeddings.
"""

from __future__ import annotations

import chromadb
from chromadb.utils import embedding_functions

from backend.config import settings

COLLECTION_NAME = "enterprise_kb"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)

_client: chromadb.ClientAPI | None = None


def get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def get_collection():
    return get_client().get_or_create_collection(
        name=COLLECTION_NAME, embedding_function=_embedding_fn
    )


def add_documents(ids: list[str], texts: list[str], metadatas: list[dict]) -> None:
    collection = get_collection()
    collection.upsert(ids=ids, documents=texts, metadatas=metadatas)


def query(text: str, top_k: int = 3) -> list[dict]:
    collection = get_collection()
    results = collection.query(query_texts=[text], n_results=top_k)
    out = []
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        out.append({"text": doc, "source": meta.get("source", "unknown"), "distance": dist})
    return out
