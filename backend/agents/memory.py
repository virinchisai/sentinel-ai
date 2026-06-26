"""SQLite-backed conversation memory with session isolation."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("sentinel_memory.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON conversations(session_id)")
    conn.commit()
    return conn


def get_history(session_id: str) -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        "SELECT role, content FROM conversations WHERE session_id = ? ORDER BY id",
        (session_id,),
    ).fetchall()
    conn.close()
    return [{"role": r[0], "content": _parse_content(r[1])} for r in rows]


def append(session_id: str, message: dict) -> None:
    conn = _connect()
    content = message.get("content", "")
    if not isinstance(content, str):
        content = json.dumps(content)
    conn.execute(
        "INSERT INTO conversations (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (session_id, message["role"], content, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def reset(session_id: str) -> None:
    conn = _connect()
    conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


def list_sessions() -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        "SELECT session_id, COUNT(*), MAX(timestamp) FROM conversations GROUP BY session_id ORDER BY MAX(timestamp) DESC"
    ).fetchall()
    conn.close()
    return [{"session_id": r[0], "message_count": r[1], "last_active": r[2]} for r in rows]


def _parse_content(raw: str):
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw
