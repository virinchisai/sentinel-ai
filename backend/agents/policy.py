"""Trusted identity and tool authorization; never derived from model arguments."""

from dataclasses import dataclass
from fastapi import HTTPException
from backend.auth.models import User, Role, get_session_factory
from backend.auth.workspaces import resolve_workspace
from backend.auth.rbac import has_permission
from backend.config import settings


@dataclass
class Actor:
    user_id: int
    workspace_id: str


def authorize(actor, tool, arguments):
    resolve_workspace(actor.user_id, actor.workspace_id)
    with get_session_factory()() as db:
        user = db.get(User, actor.user_id)
        if not user or not has_permission(user.role, "chat"):
            raise HTTPException(403, "Chat access denied")
        if tool not in {
            "query_knowledge_base",
            "echo",
            "current_time",
        } and not has_permission(user.role, "use_tools"):
            raise HTTPException(403, "Tool access denied")
        if tool.startswith(("fs_", "db_")) and user.role != Role.ADMIN:
            raise HTTPException(403, "Host tools require administrator access")
    from backend.connectors.credentials import read

    if tool.startswith("github_") and not read(actor.user_id, "github"):
        raise HTTPException(403, "Connect your GitHub account first")
    if tool.startswith(("gmail_", "calendar_")) and not read(actor.user_id, "google"):
        raise HTTPException(403, "Connect your Google account first")
    if tool.startswith("github_"):
        repo = arguments.get("repo") or settings.github_default_repo
        allowed = {
            r.strip().lower()
            for r in (
                settings.github_allowed_repos or settings.github_default_repo
            ).split(",")
        }
        if repo.lower() not in allowed:
            raise HTTPException(403, "Repository is outside the configured allowlist")
