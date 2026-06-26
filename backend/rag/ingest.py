"""CLI to chunk and embed enterprise docs (markdown + PDF) into the vector store.

Usage:
    python -m backend.rag.ingest
    python -m backend.rag.ingest --path /path/to/docs
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from backend.rag.chunking import chunk_by_heading
from backend.rag.store import add_documents

DOCS_DIR = Path(__file__).parent / "sample_docs"


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def ingest(docs_dir: Path | None = None) -> int:
    docs_dir = docs_dir or DOCS_DIR
    ids, texts, metadatas = [], [], []

    for path in sorted(docs_dir.iterdir()):
        if path.suffix == ".md":
            content = path.read_text()
            file_hash = _file_hash(path)
            chunks = chunk_by_heading(content)
            for i, chunk in enumerate(chunks):
                ids.append(f"{path.stem}-{file_hash}-{i}")
                texts.append(chunk["text"])
                metadatas.append({"source": path.name, "chunk_hash": chunk["hash"]})

        elif path.suffix == ".pdf":
            from backend.rag.pdf_parser import extract_text_from_pdf

            file_hash = _file_hash(path)
            pages = extract_text_from_pdf(path)
            for page_info in pages:
                page_chunks = chunk_by_heading(page_info["text"])
                for i, chunk in enumerate(page_chunks):
                    ids.append(f"{path.stem}-p{page_info['page']}-{file_hash}-{i}")
                    texts.append(chunk["text"])
                    metadatas.append({
                        "source": path.name,
                        "page": page_info["page"],
                        "chunk_hash": chunk["hash"],
                    })

    if ids:
        add_documents(ids, texts, metadatas)
    return len(ids)


if __name__ == "__main__":
    import sys

    docs_path = None
    if "--path" in sys.argv:
        idx = sys.argv.index("--path")
        docs_path = Path(sys.argv[idx + 1])

    count = ingest(docs_path)
    print(f"Ingested {count} chunks from {docs_path or DOCS_DIR}")
