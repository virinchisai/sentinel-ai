"""PGVector-backed vector store for production deployments.

Requires PostgreSQL with the pgvector extension and the `asyncpg` driver.
Used when RAG_BACKEND=pgvector is set; otherwise the Chroma store is used.

This module provides the same interface as store.py (add_documents, query)
so the retriever can use either backend transparently.
"""

from __future__ import annotations

from typing import Any

from backend.config import settings

COLLECTION_TABLE = "document_embeddings"
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dimension


def _get_embedding_fn():
    from chromadb.utils import embedding_functions

    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")


def _embed(texts: list[str]) -> list[list[float]]:
    fn = _get_embedding_fn()
    return fn(texts)


class PGVectorStore:
    """Sync PGVector store using psycopg2 (falls back gracefully in demo)."""

    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn or settings.database_url.replace("sqlite:///", "")

    def _connect(self):
        import psycopg2

        return psycopg2.connect(self._dsn)

    def init_table(self) -> None:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {COLLECTION_TABLE} (
                id TEXT PRIMARY KEY,
                document TEXT NOT NULL,
                metadata JSONB DEFAULT '{{}}',
                embedding vector({EMBEDDING_DIM})
            );
        """)
        conn.commit()
        cur.close()
        conn.close()

    def add_documents(self, ids: list[str], texts: list[str], metadatas: list[dict]) -> None:
        embeddings = _embed(texts)
        conn = self._connect()
        cur = conn.cursor()
        for doc_id, text, meta, emb in zip(ids, texts, metadatas, embeddings):
            import json

            cur.execute(
                f"""
                INSERT INTO {COLLECTION_TABLE} (id, document, metadata, embedding)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET document=EXCLUDED.document, metadata=EXCLUDED.metadata, embedding=EXCLUDED.embedding;
                """,
                (doc_id, text, json.dumps(meta), emb),
            )
        conn.commit()
        cur.close()
        conn.close()

    def query(self, text: str, top_k: int = 3) -> list[dict]:
        embedding = _embed([text])[0]
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT document, metadata, embedding <-> %s::vector AS distance
            FROM {COLLECTION_TABLE}
            ORDER BY distance
            LIMIT %s;
            """,
            (embedding, top_k),
        )
        results = []
        for row in cur.fetchall():
            import json

            meta = json.loads(row[1]) if isinstance(row[1], str) else row[1]
            results.append({"text": row[0], "source": meta.get("source", "unknown"), "distance": row[2]})
        cur.close()
        conn.close()
        return results
