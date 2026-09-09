"""Smart chunking: split by headings and paragraph boundaries."""

from __future__ import annotations

import hashlib
import re


def chunk_by_heading(text: str, max_chunk_size: int = 800) -> list[dict]:
    """Split text on markdown headings, keeping each section as a chunk.
    Oversized sections are split on paragraph boundaries."""
    sections = re.split(r"(?=^#{1,3}\s)", text, flags=re.MULTILINE)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section) <= max_chunk_size:
            chunks.append(section)
        else:
            chunks.extend(_split_on_paragraphs(section, max_chunk_size))
    return [
        {"text": part, "hash": hashlib.sha256(part.encode()).hexdigest()[:16]}
        for c in chunks
        for part in [
            c[i : i + max_chunk_size] for i in range(0, len(c), max_chunk_size)
        ]
    ]


def _split_on_paragraphs(text: str, max_size: int) -> list[str]:
    paragraphs = re.split(r"\n\n+", text)
    chunks, current = [], ""
    for para in paragraphs:
        if current and len(current) + len(para) + 2 > max_size:
            chunks.append(current.strip())
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current.strip():
        chunks.append(current.strip())
    return chunks
