"""Report the live/mock status of each connector, based on what's configured."""

from __future__ import annotations

from backend.config import settings


def get_connector_status() -> list[dict]:
    """Return a status row per connector with mode (live/mock) and detail."""
    statuses = []

    statuses.append({
        "name": "GitHub",
        "mode": "live" if settings.github_token else "mock",
        "detail": (
            f"Token configured, default repo: {settings.github_default_repo}"
            if settings.github_token
            else "No GITHUB_TOKEN set — using mock responses"
        ),
    })

    statuses.append({
        "name": "Gmail",
        "mode": "live" if settings.gmail_credentials_json else "mock",
        "detail": (
            "OAuth credentials configured"
            if settings.gmail_credentials_json
            else "No GMAIL_CREDENTIALS_JSON set — returning sample emails"
        ),
    })

    statuses.append({
        "name": "Calendar",
        "mode": "live" if settings.google_calendar_credentials_json else "mock",
        "detail": (
            "OAuth credentials configured"
            if settings.google_calendar_credentials_json
            else "No GOOGLE_CALENDAR_CREDENTIALS_JSON set — returning sample events"
        ),
    })

    statuses.append({
        "name": "File System",
        "mode": "live",
        "detail": f"Sandboxed to {settings.workspace_dir}",
    })

    is_sqlite = settings.database_url.startswith("sqlite")
    statuses.append({
        "name": "PostgreSQL",
        "mode": "demo" if is_sqlite else "live",
        "detail": (
            "Using SQLite demo database (employees + projects tables)"
            if is_sqlite
            else f"Connected to {settings.database_url.split('@')[-1]}"
        ),
    })

    chunks = 0
    try:
        from backend.rag.store import get_collection
        chunks = get_collection().count()
    except Exception:
        pass

    statuses.append({
        "name": "Knowledge Base (RAG)",
        "mode": "live" if chunks > 0 else "empty",
        "detail": f"{chunks} document chunks indexed",
    })

    statuses.append({
        "name": "LLM Provider",
        "mode": "live" if (
            (settings.llm_provider == "anthropic" and settings.anthropic_api_key)
            or (settings.llm_provider == "openai" and settings.openai_api_key)
        ) else "no_key",
        "detail": (
            f"{settings.llm_provider} — model: "
            + (settings.anthropic_model if settings.llm_provider == "anthropic" else settings.openai_model)
        ),
    })

    return statuses
