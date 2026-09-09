"""Membership is checked at the API and again before every tool invocation."""

import uuid
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from backend.auth.models import Workspace, Membership, get_session_factory


def resolve_workspace(user_id, workspace_id=None):
    with get_session_factory()() as db:
        if not workspace_id:
            workspace_id = str(
                uuid.uuid5(uuid.NAMESPACE_URL, f"sentinel:user:{user_id}")
            )
            if not db.get(Workspace, workspace_id):
                db.add(
                    Workspace(
                        id=workspace_id, name="Personal workspace", owner_id=user_id
                    )
                )
                try:
                    db.flush()
                    db.add(Membership(workspace_id=workspace_id, user_id=user_id))
                    db.commit()
                except IntegrityError:
                    db.rollback()
                    # Another request may have created this personal workspace.
                    # Accept only a committed workspace with this user's membership.
                    if not db.get(Membership, (workspace_id, user_id)):
                        raise
        if not db.get(Membership, (workspace_id, user_id)):
            raise HTTPException(status_code=403, detail="Workspace access denied")
        return workspace_id
