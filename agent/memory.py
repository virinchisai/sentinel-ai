"""In-memory conversation history keyed by session id."""

from collections import defaultdict

_sessions: dict[str, list[dict]] = defaultdict(list)


def get_history(session_id: str) -> list[dict]:
    return _sessions[session_id]


def append(session_id: str, message: dict) -> None:
    _sessions[session_id].append(message)


def reset(session_id: str) -> None:
    _sessions.pop(session_id, None)
