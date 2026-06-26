"""Audit logging for authenticated actions."""

from __future__ import annotations

from datetime import datetime, timezone
from functools import wraps

from backend.auth.models import AuditLog, get_session_factory


def log_action(user_id: int | None, action: str, resource: str = "", detail: str = "", ip: str = "") -> None:
    factory = get_session_factory()
    db = factory()
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            detail=detail,
            ip_address=ip,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()


def audited(action: str):
    """Decorator for FastAPI route handlers that logs the action after execution."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            user = kwargs.get("current_user") or kwargs.get("user")
            user_id = getattr(user, "id", None) if user else None
            request = kwargs.get("request")
            ip = request.client.host if request and request.client else ""
            log_action(user_id=user_id, action=action, ip=ip)
            return result

        return wrapper

    return decorator
