"""CLI to chunk and embed the sample enterprise docs into the vector store.

Usage:
    python -m rag.ingest
"""

from __future__ import annotations

from pathlib import Path

from rag.store import add_documents

DOCS_DIR = Path(__file__).parent / "sample_docs"
CHUNK_SIZE = 600  # chars; small docs here fit in one chunk each, kept generic for larger docs
CHUNK_OVERLAP = 100


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def ingest() -> int:
    ids, texts, metadatas = [], [], []
    for path in sorted(DOCS_DIR.glob("*.md")):
        content = path.read_text()
        for i, chunk in enumerate(chunk_text(content)):
            ids.append(f"{path.stem}-{i}")
            texts.append(chunk)
            metadatas.append({"source": path.name})

    add_documents(ids, texts, metadatas)
    return len(ids)


if __name__ == "__main__":
    count = ingest()
    print(f"Ingested {count} chunks from {DOCS_DIR}")
