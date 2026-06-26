"""Role-based access control permissions."""

from __future__ import annotations

from backend.auth.models import Role

PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {
        "chat",
        "upload_documents",
        "view_audit_log",
        "manage_users",
        "view_sessions",
        "use_tools",
    },
    Role.USER: {
        "chat",
        "upload_documents",
        "use_tools",
    },
    Role.VIEWER: {
        "chat",
    },
}


def has_permission(role: Role, permission: str) -> bool:
    return permission in PERMISSIONS.get(role, set())
