"""Chroma vector store wrapper using a local sentence-transformers embedding model.

Embeddings are computed with sentence-transformers (not the chat LLM provider)
so RAG ingestion/retrieval works regardless of which LLM provider is configured
and without spending API tokens on embeddings.
"""

from __future__ import annotations

import hashlib

import chromadb
from chromadb.utils import embedding_functions

from backend.config import settings

COLLECTION_NAME = "enterprise_kb"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

_client: chromadb.ClientAPI | None = None
_embedding_fn = None


class FallbackEmbeddingFunction:
    """Cheap deterministic embedding fallback when local ML deps are unavailable."""

    dimension = 64

    @staticmethod
    def name() -> str:
        return "default"

    @staticmethod
    def is_legacy() -> bool:
        return False

    @staticmethod
    def default_space() -> str:
        return "cosine"

    @staticmethod
    def supported_spaces() -> list[str]:
        return ["cosine"]

    def __call__(self, input: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in input:
            vector = [0.0] * self.dimension
            for token in text.lower().split():
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                bucket = digest[0] % self.dimension
                vector[bucket] += 1.0
            norm = sum(v * v for v in vector) ** 0.5 or 1.0
            vectors.append([v / norm for v in vector])
        return vectors

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)


def get_embedding_function():
    global _embedding_fn
    if _embedding_fn is not None:
        return _embedding_fn

    try:
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
    except Exception:
        _embedding_fn = FallbackEmbeddingFunction()
    return _embedding_fn


def get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def get_collection():
    return get_client().get_or_create_collection(
        name=COLLECTION_NAME, embedding_function=get_embedding_function()
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
