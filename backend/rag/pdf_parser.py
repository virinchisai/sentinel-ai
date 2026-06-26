"""PDF text extraction using PyMuPDF (fitz)."""

from __future__ import annotations

from pathlib import Path


def extract_text_from_pdf(path: str | Path) -> list[dict]:
    """Return a list of dicts with 'text' and 'page' keys, one per page."""
    import fitz

    doc = fitz.open(str(path))
    pages = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text()
        if text.strip():
            pages.append({"text": text, "page": i})
    doc.close()
    return pages
