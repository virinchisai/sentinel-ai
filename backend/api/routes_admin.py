"""Admin routes: audit log, session management."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.agents.memory import list_sessions
from backend.auth.middleware import require_permission
from backend.auth.models import AuditLog, User, get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/audit-log")
def get_audit_log(
    limit: int = 50,
    current_user: User = Depends(require_permission("view_audit_log")),
    db=Depends(get_db),
) -> list[dict]:
    entries = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "user_id": e.user_id,
            "action": e.action,
            "resource": e.resource,
            "detail": e.detail,
            "ip_address": e.ip_address,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        }
        for e in entries
    ]


@router.get("/sessions")
def get_sessions(
    current_user: User = Depends(require_permission("view_sessions")),
) -> list[dict]:
    return list_sessions()
