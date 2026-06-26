"""Sandboxed file system connector for reading workspace files."""

from __future__ import annotations

from pathlib import Path

from backend.config import settings


class FileSystemClient:
    def __init__(self) -> None:
        self._root = Path(settings.workspace_dir).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, rel_path: str) -> Path:
        target = (self._root / rel_path).resolve()
        if not str(target).startswith(str(self._root)):
            raise PermissionError(f"Access denied: path escapes workspace: {rel_path}")
        return target

    def list_files(self, directory: str = ".") -> list[dict]:
        target = self._safe_path(directory)
        if not target.is_dir():
            return []
        return [
            {"name": p.name, "type": "dir" if p.is_dir() else "file", "size": p.stat().st_size if p.is_file() else 0}
            for p in sorted(target.iterdir())
            if not p.name.startswith(".")
        ]

    def read_file(self, path: str) -> dict:
        target = self._safe_path(path)
        if not target.is_file():
            return {"error": f"File not found: {path}"}
        content = target.read_text(errors="replace")
        return {"path": path, "content": content[:5000], "truncated": len(content) > 5000}

    def search_files(self, query: str, directory: str = ".") -> list[dict]:
        target = self._safe_path(directory)
        results = []
        for p in target.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                try:
                    content = p.read_text(errors="replace")
                    if query.lower() in content.lower():
                        line_matches = [
                            (i + 1, line.strip())
                            for i, line in enumerate(content.splitlines())
                            if query.lower() in line.lower()
                        ]
                        results.append({
                            "path": str(p.relative_to(self._root)),
                            "matches": line_matches[:5],
                        })
                except Exception:
                    continue
                if len(results) >= 10:
                    break
        return results


_client: FileSystemClient | None = None


def get_client() -> FileSystemClient:
    global _client
    if _client is None:
        _client = FileSystemClient()
    return _client
